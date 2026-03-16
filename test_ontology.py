# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

from src.coreason_manifest.spec.ontology import ContinuousObservationStream

stream = ContinuousObservationStream(
    stream_id="stream-123",
    token_buffer=["hello", "world", "this", "is", "a", "test"],
    temporal_decay_matrix={0: 1.0, 1: 0.9, 2: 0.8},
    latest_confidence_score=0.95,
)

print(stream.token_buffer)
