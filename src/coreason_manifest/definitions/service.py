from typing import Any, Dict, List, Optional

from pydantic import ConfigDict

from ..common import CoReasonBaseModel
from ..spec.cap import ServiceRequest, ServiceResponse


class AgentRequest(CoReasonBaseModel):
    """Strictly typed payload inside a ServiceRequest."""

    model_config = ConfigDict(frozen=True)

    query: str
    files: List[str] = []
    conversation_id: Optional[str] = None
    meta: Dict[str, Any] = {}


class ServiceContract:
    """Utility class to generate the OpenAPI specification."""

    @staticmethod
    def generate_openapi() -> Dict[str, Any]:
        """Generate the OpenAPI 3.1 Path Item Object for the agent service."""
        return {
            "post": {
                "summary": "Invoke Agent",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": ServiceRequest.model_json_schema()
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Successful Response",
                        "content": {
                            "application/json": {
                                "schema": ServiceResponse.model_json_schema()
                            }
                        },
                    }
                },
            }
        }
