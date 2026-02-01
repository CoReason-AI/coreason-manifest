# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from pathlib import Path

import pytest
import yaml


def test_ci_cd_workflow_does_not_contain_release_job() -> None:
    """
    Edge case test: Ensure the 'release' job is not accidentally re-introduced
    into the CI/CD workflow, as publishing is now handled by publish.yml.
    """
    workflow_path = Path(".github/workflows/ci-cd.yml")
    if not workflow_path.exists():
        pytest.fail(f"Workflow file not found at {workflow_path}")

    with open(workflow_path, "r") as f:
        workflow = yaml.safe_load(f)

    jobs = workflow.get("jobs", {})
    assert (
        "release" not in jobs
    ), "The 'release' job should not exist in ci-cd.yml. Publishing is handled by publish.yml."


def test_ci_cd_workflow_contains_build_verification() -> None:
    """
    Edge case test: Ensure we verify that the package builds in CI,
    since we removed the release job that previously did this.
    """
    workflow_path = Path(".github/workflows/ci-cd.yml")
    if not workflow_path.exists():
        pytest.fail(f"Workflow file not found at {workflow_path}")

    with open(workflow_path, "r") as f:
        workflow = yaml.safe_load(f)

    jobs = workflow.get("jobs", {})
    # Look for a job that runs 'python -m build' or strictly the 'build-package' job
    build_job_found = False
    if "build-package" in jobs:
        build_job_found = True

    assert build_job_found, "A 'build-package' job should exist to verify package buildability in CI."
