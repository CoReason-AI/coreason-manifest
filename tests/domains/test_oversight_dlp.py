import pytest
from pydantic import ValidationError

from coreason_manifest.oversight.dlp import FilesystemIsolationContract


def test_filesystem_isolation_contract_bounds() -> None:
    # Valid
    contract = FilesystemIsolationContract(
        require_hardware_enclave=True, max_symlink_depth=0, allowed_mount_paths=["/mnt/secure"]
    )
    assert contract.max_symlink_depth == 0

    # Invalid depth
    with pytest.raises(ValidationError):
        FilesystemIsolationContract(
            require_hardware_enclave=True, max_symlink_depth=-1, allowed_mount_paths=["/mnt/secure"]
        )

    # Invalid empty mount paths
    with pytest.raises(ValidationError):
        FilesystemIsolationContract(require_hardware_enclave=True, max_symlink_depth=0, allowed_mount_paths=[])
