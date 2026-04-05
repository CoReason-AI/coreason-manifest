# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import json

dpo1 = {"l": {"a": "b"}, "k": {}, "r": {}}
dpo2 = {"l": {"b": "a"}, "k": {}, "r": {}}

print(json.dumps(dpo1, sort_keys=True))
print(json.dumps(dpo2, sort_keys=True))
