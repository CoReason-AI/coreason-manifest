from typing import Any

from ..cap import ServiceRequest, ServiceResponse


class ServiceContract:
    """Utility class to generate the OpenAPI specification."""

    @staticmethod
    def generate_openapi() -> dict[str, Any]:
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
