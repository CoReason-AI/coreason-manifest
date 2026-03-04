from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.primitives import GitSHA


class CustodyRecord(CoreasonBaseModel):
    """
    Cryptographic state of an agent to ensure full traceability and provenance.
    """

    prompt_template_sha: GitSHA = Field(description="The cryptographic SHA of the prompt template used.")
    context_hash: str = Field(description="The cryptographic hash of the input context provided to the agent.")
    temperature: float = Field(description="The temperature parameter used for generating the response.")
