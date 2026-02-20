from coreason_manifest.spec.interop.compliance import ComplianceReport, RemediationAction


class DomainValidationError(ValueError):
    """
    A domain-specific validation error that includes structured diagnostics.
    """

    def __init__(
        self,
        message: str,
        report: ComplianceReport | None = None,
        remediation: RemediationAction | None = None,
    ):
        super().__init__(message)
        self.report = report
        self.remediation = remediation

    def __str__(self) -> str:
        base_msg = super().__str__()
        if self.remediation:
            return f"{base_msg} [Remediation: {self.remediation.description}]"
        return base_msg
