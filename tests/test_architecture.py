# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import importlib
import pkgutil
import sys

import coreason_manifest.spec


def test_spec_does_not_import_utils() -> None:
    """
    Ensures that the Core Spec (shared kernel) does NOT import from the Utils package.
    This prevents the 'Distributed Monolith' trap by ensuring the DTOs are clean.
    """
    package = coreason_manifest.spec
    prefix = package.__name__ + "."

    for _importer, modname, _ispkg in pkgutil.walk_packages(package.__path__, prefix):
        # Import the module
        try:
            module = importlib.import_module(modname)
        except ImportError as e:
            # Skip if strict dependency is missing (should not happen in dev)
            print(f"Skipping {modname} due to ImportError: {e}")
            continue

        # Check attributes
        for name in dir(module):
            # Skip internal attributes
            if name.startswith("__"):
                continue

            attr = getattr(module, name)

            # Check if it is a module
            if (
                hasattr(attr, "__name__")
                and isinstance(attr, type(sys))
                and attr.__name__.startswith("coreason_manifest.utils")
            ):
                raise AssertionError(
                    f"Module '{modname}' imports '{attr.__name__}'. Core Spec must not depend on Utils."
                )

            # Check if it is an object (class, func) from a module
            if (
                hasattr(attr, "__module__")
                and attr.__module__
                and attr.__module__.startswith("coreason_manifest.utils")
            ):
                raise AssertionError(
                    f"Module '{modname}' uses '{name}' from '{attr.__module__}'. Core Spec must not depend on Utils."
                )
