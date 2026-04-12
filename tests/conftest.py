# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Root-level test configuration for Hypothesis profile registration.

Registers named Hypothesis profiles that control the depth of property-based
testing across the repository. The ``ci-deep`` profile is loaded by the
nightly fuzzing workflow to perform exhaustive state-space exploration without
blocking PR checks.
"""

from hypothesis import HealthCheck, settings

# Default profile — mirrors reasonable CI limits for PR checks.
settings.register_profile(
    "default",
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)

# Deep fuzzing profile — used by the nightly-fuzzing.yml workflow.
settings.register_profile(
    "ci-deep",
    max_examples=5000,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow],
)

settings.load_profile("default")
