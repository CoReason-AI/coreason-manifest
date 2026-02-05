# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any, Dict

from ..cap import ServiceRequest, ServiceResponse


class ServiceContract:
    """Utility class to generate the OpenAPI specification."""

    @staticmethod
    def generate_openapi() -> Dict[str, Any]:
        """Generate the OpenAPI 3.1 Path Item Object for the agent service."""
        return {
            "post": {
                "summary": "Invoke Agent",
                "requestBody": {"content": {"application/json": {"schema": ServiceRequest.model_json_schema()}}},
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {"application/json": {"schema": ServiceResponse.model_json_schema()}},
                    }
                },
            }
        }
