import hashlib
import importlib.abc
import importlib.util
import re
import sys
import warnings
import json
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Any, cast, Protocol
import asyncio
from urllib.parse import urlparse

import httpx
from pydantic import AnyUrl, HttpUrl, validate_call
from opentelemetry import trace
import yaml
from yaml.nodes import MappingNode

from coreason_manifest.spec.core.manifest import AnyFlow, Manifest
from coreason_manifest.spec.core.resilience import RecoveryReceipt
from coreason_manifest.utils.resolver import ReferenceResolver


class RuntimeSecurityWarning(RuntimeWarning):
    """Warning for runtime security risks."""

class SecurityViolationError(Exception):
    """Raised when a security policy is violated."""


# SOTA Security: Context-aware jail root for import resolution.
_jail_root_var: ContextVar[Path | None] = ContextVar("jail_root", default=None)
_jail_modules_var: ContextVar[set[str] | None] = ContextVar("jail_modules", default=None)


class SandboxedPathFinder(importlib.abc.MetaPathFinder):
    """
    A custom MetaPathFinder that resolves imports relative to a 'jail' directory
    without modifying sys.path.
    """

    def find_spec(
        self,
        fullname: str,
        _path: Any = None,
        _target: Any = None,
    ) -> importlib.machinery.ModuleSpec | None:
        if fullname in sys.stdlib_module_names:
            return None

        jail_root = _jail_root_var.get()
        if not jail_root:
            return None

        if ".." in fullname:
            return None

        parts = fullname.split(".")
        potential_path = jail_root.joinpath(*parts)

        spec = None
        init_py = potential_path / "__init__.py"
        if init_py.is_file():
            spec = importlib.util.spec_from_file_location(fullname, init_py)
        elif potential_path.with_suffix(".py").is_file():
            spec = importlib.util.spec_from_file_location(fullname, potential_path.with_suffix(".py"))

        if spec:
            modules = _jail_modules_var.get()
            if modules is not None:
                modules.add(fullname)
            return spec

        return None


_SANDBOXED_FINDER = SandboxedPathFinder()


@contextmanager
def sandbox_context(jail_root: Path):
    if _SANDBOXED_FINDER not in sys.meta_path:
        sys.meta_path.insert(0, _SANDBOXED_FINDER)

    token_root = _jail_root_var.set(jail_root.resolve())
    token_modules = _jail_modules_var.set(set())
    try:
        yield
    finally:
        _jail_root_var.reset(token_root)
        _jail_modules_var.reset(token_modules)


class YamlLoaderProtocol(Protocol):
    def construct_object(self, node: yaml.Node, deep: bool = False) -> Any: ...
    def flatten_mapping(self, node: MappingNode) -> None: ...


def construct_mapping_unique(loader: yaml.SafeLoader, node: yaml.Node, deep: bool = False) -> dict[Any, Any]:
    """
    Construct a mapping while checking for duplicate keys.
    """
    if not isinstance(node, MappingNode):
        node_any = cast(Any, node)
        raise yaml.constructor.ConstructorError(
            None,
            None,
            f"expected a mapping node, but found {node_any.id}",
            node.start_mark,
        )

    mapping_node = node
    loader_typed = cast(YamlLoaderProtocol, loader)
    loader_typed.flatten_mapping(mapping_node)
    mapping = {}
    for key_node, value_node in mapping_node.value:
        key = loader_typed.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(
                "while constructing a mapping",
                node.start_mark,
                f"found duplicate key {key!r}",
                key_node.start_mark,
            )
        mapping[key] = loader_typed.construct_object(value_node, deep=deep)
    return mapping


class Loader:
    """
    SOTA Manifest Loader.
    Ingestion is Liquid: Accepts strings, URLs, Paths, S3 URIs.
    """

    @classmethod
    @validate_call
    async def load(cls, source: str | Path | HttpUrl | AnyUrl, auto_heal: bool = True) -> Manifest:
        """
        Loads a manifest from various sources, resolves references, and validates.
        Wraps the process in an OTEL span.
        """
        tracer = trace.get_tracer(__name__)

        with tracer.start_as_current_span("Loader.load", attributes={"source": str(source)}) as span:
            # Determine base URI and fetch content
            content, base_uri = await cls._fetch_source(source)

            resolver = ReferenceResolver(base_uri=base_uri)

            initial_receipt = None

            try:
                raw_data = resolver._parse_content(content, str(source))
            except ValueError as e:
                # If parsing fails, try auto-healing the string
                cleaned_data, receipt = Manifest._perform_auto_healing(content)
                initial_receipt = receipt

                if isinstance(cleaned_data, str):
                     try:
                        raw_data = resolver._parse_content(cleaned_data, str(source))
                     except ValueError:
                        span.record_exception(e)
                        raise e
                else:
                    raw_data = cleaned_data

            # Resolve References
            resolved_data = await resolver.resolve(raw_data)

            # Validate
            try:
                # Pass auto_heal via context
                manifest = Manifest.model_validate(resolved_data, context={"auto_heal": auto_heal})
            except Exception as e:
                span.record_exception(e)
                raise e

            # Merge initial receipt from string healing if present
            if initial_receipt and initial_receipt.mutations:
                current_receipt = manifest.recovery_receipt
                if current_receipt:
                    all_mutations = initial_receipt.mutations + current_receipt.mutations
                    new_receipt = RecoveryReceipt(mutations=all_mutations)
                    # Use object.__setattr__ to bypass frozen check
                    object.__setattr__(manifest, "_recovery_receipt", new_receipt)
                else:
                    object.__setattr__(manifest, "_recovery_receipt", initial_receipt)

            # Attach RecoveryReceipt as Span Event if present
            if manifest.recovery_receipt and manifest.recovery_receipt.mutations:
                span.add_event(
                    "auto_heal_applied",
                    attributes={
                        "mutations": json.dumps(manifest.recovery_receipt.mutations),
                        "original_checksum": manifest.recovery_receipt.original_checksum or "",
                    }
                )

            return manifest

    @staticmethod
    async def _fetch_source(source: str | Path | HttpUrl | AnyUrl) -> tuple[str, str | Path]:
        source_str = str(source)

        # Check if URL
        if source_str.startswith(("http://", "https://")):
            async with httpx.AsyncClient() as client:
                resp = await client.get(source_str)
                resp.raise_for_status()
                return resp.text, source_str

        # Check if S3
        if source_str.startswith("s3://"):
            import boto3
            parsed = urlparse(source_str)
            bucket = parsed.netloc
            key = parsed.path.lstrip("/")

            def fetch_s3() -> str:
                s3 = boto3.client("s3")
                response = s3.get_object(Bucket=bucket, Key=key)
                return str(response["Body"].read().decode("utf-8"))

            try:
                loop = asyncio.get_running_loop()
                content = await loop.run_in_executor(None, fetch_s3)
            except RuntimeError:
                content = fetch_s3()

            return content, source_str

        # Check if local path
        try:
            path = Path(source_str)
            if path.exists():
                return path.read_text(encoding="utf-8"), path.resolve()
        except OSError:
            pass

        # Treat as raw content (String)
        # Base URI defaults to CWD
        return source_str, Path.cwd()


def load_flow_from_file(
    path: str, root_dir: Path | None = None, allow_dynamic_execution: bool = False
) -> AnyFlow:
    """
    Synchronous wrapper for Loader.load to support legacy CLI/Tests.
    Ignores root_dir and allow_dynamic_execution for now as new loader handles it differently.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    manifest = loop.run_until_complete(Loader.load(path, auto_heal=True))
    return manifest.flow


def load_agent_from_ref(reference: str, root_dir: Path) -> type:
    """
    Load an Agent class from a Python file reference (file.py:ClassName).
    WARNING: Executes arbitrary code. Ensure source is trusted.
    """
    if ":" not in reference:
        raise ValueError(f"Invalid reference format: {reference}. Expected 'file.py:ClassName'.")

    file_ref, class_name = reference.rsplit(":", 1)

    file_path = (root_dir / file_ref).resolve()
    if not file_path.is_file():
        raise ValueError(f"Agent file not found: {file_path}")

    warnings.warn(
        f"Dynamic Code Execution: Loading agent from {file_ref}. Ensure this code is trusted.",
        category=RuntimeSecurityWarning,
        stacklevel=2,
    )

    path_hash = hashlib.sha256(str(file_path).encode("utf-8")).hexdigest()[:16]
    module_name = f"agent_{path_hash}"

    with sandbox_context(root_dir):
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise ValueError(f"Could not load spec for {file_ref}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module

        try:
            spec.loader.exec_module(module)
        except Exception as e:
            if module_name in sys.modules:
                del sys.modules[module_name]
            cleanup_modules = _jail_modules_var.get()
            if cleanup_modules:
                for mod in cleanup_modules:
                    if mod in sys.modules:
                        del sys.modules[mod]
            raise ValueError(f"Failed to execute agent code in {file_ref}: {e}") from e

        agent_class = getattr(module, class_name, None)

        if module_name in sys.modules:
            del sys.modules[module_name]

        cleanup_modules = _jail_modules_var.get()
        if cleanup_modules:
            for mod in cleanup_modules:
                if mod in sys.modules:
                    del sys.modules[mod]

    if agent_class is None:
        raise ValueError(f"Agent class '{class_name}' not found in {file_ref}")

    if isinstance(agent_class, type):
        return agent_class

    raise TypeError(f"'{class_name}' in {file_ref} is not a class.")
