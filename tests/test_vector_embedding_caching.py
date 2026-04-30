import base64

import numpy as np

from src.coreason_manifest.spec.ontology import VectorEmbeddingState


def test_vector_embedding_decoding_caching():
    v = np.random.rand(1024).astype(np.float32)
    v_b64 = base64.b64encode(v.tobytes()).decode("utf-8")

    vec = VectorEmbeddingState(vector_base64=v_b64, dimensionality=1024, foundation_matrix_name="test-model")

    # Check that decoding works and returns a numpy array
    arr = vec.decoded_vector
    assert arr is not None
    assert isinstance(arr, np.ndarray)
    assert arr.dtype == np.float32
    assert arr.shape == (1024,)

    # Check caching
    arr2 = vec.decoded_vector
    assert arr is arr2
