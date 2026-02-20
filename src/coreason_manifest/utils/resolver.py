import asyncio
import json
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
import yaml


class ReferenceResolver:
    """
    Async resolver for JSON Schema $ref pointers.
    Supports local files, HTTP(S) URLs, and S3 URIs.
    Detects circular references.
    """

    def __init__(self, base_uri: str | Path | None = None):
        if base_uri is None:
            self.base_uri = Path.cwd()
        else:
            self.base_uri = base_uri

        # visited_paths tracks the current recursion stack to detect cycles
        self.visited_paths: set[str] = set()
        # cache stores loaded content to avoid fetching/reading same resource multiple times
        self.cache: dict[str, Any] = {}

    async def resolve(self, data: Any) -> Any:
        """
        Recursively resolves all $ref in the data structure.
        Starts with the initialized base_uri.
        """
        return await self._traverse(data, self.base_uri)

    async def _traverse(self, node: Any, base_uri: str | Path) -> Any:
        if isinstance(node, dict):
            if "$ref" in node:
                ref = node["$ref"]
                # Resolve ref relative to current base_uri
                absolute_uri = self._resolve_uri(base_uri, ref)

                content, new_base = await self._fetch_ref(absolute_uri)
                # Recursively resolve the fetched content with its own base
                return await self._traverse(content, new_base)

            # Recurse into dict keys
            resolved_dict = {}
            # We do this sequentially to propagate context correctly if needed,
            # though parallel is possible for keys.
            for k, v in node.items():
                resolved_dict[k] = await self._traverse(v, base_uri)
            return resolved_dict

        elif isinstance(node, list):
            # Resolve items in parallel
            tasks = [self._traverse(item, base_uri) for item in node]
            return await asyncio.gather(*tasks)

        return node

    def _resolve_uri(self, base: str | Path, ref: str) -> str:
        """
        Resolves a reference string against a base URI (file path or URL).
        """
        base_str = str(base)
        parsed_base = urlparse(base_str)

        # If base is URL (HTTP or S3)
        if parsed_base.scheme in ("http", "https", "s3"):
            return urljoin(base_str, ref)

        # If base is local path
        # Check if ref is absolute URL
        parsed_ref = urlparse(ref)
        if parsed_ref.scheme in ("http", "https", "s3"):
            return ref

        # Treat as file path
        base_path = Path(base)
        # If base_path is a file, take its parent
        if base_path.suffix or base_path.is_file(): # suffix check is heuristic
             base_dir = base_path.parent
        else:
             base_dir = base_path

        # Resolve ref
        target = (base_dir / ref).resolve()
        return str(target)

    async def _fetch_ref(self, uri: str) -> tuple[Any, str | Path]:
        """
        Fetches content from uri and returns (content, new_base_uri).
        """
        if uri in self.visited_paths:
             raise ValueError(f"Circular reference detected: {uri}")

        if uri in self.cache:
            return self.cache[uri], uri

        self.visited_paths.add(uri)
        try:
            parsed = urlparse(uri)
            if parsed.scheme in ("http", "https"):
                async with httpx.AsyncClient() as client:
                    response = await client.get(uri)
                    response.raise_for_status()
                    text = response.text
            elif parsed.scheme == "s3":
                import boto3
                bucket = parsed.netloc
                key = parsed.path.lstrip("/")

                def fetch_s3():
                    s3 = boto3.client("s3")
                    response = s3.get_object(Bucket=bucket, Key=key)
                    return response["Body"].read().decode("utf-8")

                loop = asyncio.get_running_loop()
                text = await loop.run_in_executor(None, fetch_s3)
            else:
                # Local file
                path = Path(uri)
                if not path.exists():
                    raise FileNotFoundError(f"Reference not found: {path}")
                text = path.read_text(encoding="utf-8")

            content = self._parse_content(text, uri)
            self.cache[uri] = content
            return content, uri
        finally:
            self.visited_paths.remove(uri)

    def _parse_content(self, text: str, source: str) -> Any:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                return yaml.safe_load(text)
            except yaml.YAMLError as e:
                raise ValueError(f"Failed to parse content from {source}: {e}")
