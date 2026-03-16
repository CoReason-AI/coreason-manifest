from src.coreason_manifest.spec.ontology import ContinuousObservationStream

stream = ContinuousObservationStream(
    stream_id="stream-123",
    token_buffer=["hello", "world", "this", "is", "a", "test"],
    temporal_decay_matrix={0: 1.0, 1: 0.9, 2: 0.8},
    latest_confidence_score=0.95,
)

print(stream.token_buffer)
