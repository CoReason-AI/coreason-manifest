# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

from pydantic import BaseModel, ConfigDict


class CoreasonBaseState(BaseModel):
    """
    Base class for all Coreason states.
    Enforces strict configuration to prevent arbitrary assignment and extra fields.
    """

    model_config = ConfigDict(extra="forbid", validate_assignment=True)
