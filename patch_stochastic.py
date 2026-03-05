with open("src/coreason_manifest/compute/stochastic.py", "r") as f:
    content = f.read()

import_target = "from pydantic import Field"
import_replacement = "from pydantic import Field, model_validator\nfrom typing import Any"
if "model_validator" not in content:
    content = content.replace(import_target, import_replacement)

target = """class DistributionProfile(CoreasonBaseModel):
    \"\"\"Profile defining a probability density function.\"\"\"

    distribution_type: DistributionType = Field(
        description="The mathematical shape of the probability density function."
    )
    mean: float | None = Field(default=None, description="The expected value (mu) of the distribution.")
    variance: float | None = Field(default=None, description="The mathematical variance (sigma squared).")
    confidence_interval_95: tuple[float, float] | None = Field(default=None, description="The 95% probability bounds.")"""

replacement = target + """

    @model_validator(mode="after")
    def validate_confidence_interval(self) -> Any:
        if self.confidence_interval_95 is not None:
            if self.confidence_interval_95[0] >= self.confidence_interval_95[1]:
                raise ValueError("confidence_interval_95 must have interval[0] < interval[1]")
        return self"""

content = content.replace(target, replacement)

with open("src/coreason_manifest/compute/stochastic.py", "w") as f:
    f.write(content)
