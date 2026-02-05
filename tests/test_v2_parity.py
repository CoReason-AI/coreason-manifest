# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import os
import tempfile

from coreason_manifest.v2.io import load_from_yaml


def test_full_definition() -> None:
    yaml_content = """
apiVersion: coreason.ai/v2
kind: Recipe
metadata:
  name: TestRecipe
interface:
  inputs:
    topic:
      type: string
  outputs:
    summary:
      type: string
policy:
  max_steps: 10
  max_retries: 5
  timeout: 60
  human_in_the_loop: true
workflow:
  start: step1
  steps:
    step1:
      type: logic
      id: step1
      code: "print('hello')"
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as tmp:
        tmp.write(yaml_content)
        tmp_path = tmp.name

    try:
        manifest = load_from_yaml(tmp_path)

        assert manifest.interface.inputs["topic"]["type"] == "string"
        assert manifest.interface.outputs["summary"]["type"] == "string"
        assert manifest.policy.max_steps == 10
        assert manifest.policy.max_retries == 5
        assert manifest.policy.timeout == 60
        assert manifest.policy.human_in_the_loop is True
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
