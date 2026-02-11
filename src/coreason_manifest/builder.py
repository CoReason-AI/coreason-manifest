# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.spec.core.flow import GraphFlow, LinearFlow

class AgentBuilder:
    """Builder for creating Agent manifests programmatically.

    WARNING: This builder is currently a placeholder for the new Core Kernel refactor.
    """

    def __init__(self) -> None:
        raise NotImplementedError("Builder is being refactored for the new Core Kernel.")

    def build(self) -> LinearFlow | GraphFlow:
        """Build and validate the manifest."""
        raise NotImplementedError()
