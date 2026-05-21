// Copyright (c) 2026 CoReason, Inc
// Licensed under the Prosperity Public License 3.0
// https://github.com/CoReason-AI/coreason-manifest

use coreason_manifest_rust::algebra::{
    calculate_latent_alignment, compute_merkle_directory_cid, compute_topology_hash,
    validate_ssrf_safety,
};
use coreason_manifest_rust::ontology::{
    EpistemicOntologicalAlignmentPolicy, FoundationMatrixName, VectorBase64, VectorEmbeddingState,
};
use std::collections::HashMap;

#[test]
fn test_ssrf_safety_valid() {
    assert!(validate_ssrf_safety("https://example.com/api/v1").is_ok());
    assert!(validate_ssrf_safety("http://google.com").is_ok());
    assert!(validate_ssrf_safety("https://github.com/CoReason-AI").is_ok());
}

#[test]
fn test_ssrf_safety_invalid_localhost() {
    let r1 = validate_ssrf_safety("http://localhost");
    assert!(r1.is_err());
    assert!(r1.unwrap_err().contains("local loopback network"));

    let r2 = validate_ssrf_safety("http://localhost.localdomain");
    assert!(r2.is_err());

    let r3 = validate_ssrf_safety("https://sub.localhost");
    assert!(r3.is_err());
}

#[test]
fn test_ssrf_safety_invalid_ips() {
    // IPv4 Loopback
    assert!(validate_ssrf_safety("http://127.0.0.1").is_err());
    // IPv4 Private Range (10.x.x.x)
    assert!(validate_ssrf_safety("http://10.0.0.1").is_err());
    // IPv4 Private Range (192.168.x.x)
    assert!(validate_ssrf_safety("http://192.168.1.1").is_err());
    // IPv6 Loopback
    assert!(validate_ssrf_safety("http://[::1]").is_err());
}

#[test]
fn test_ssrf_safety_invalid_packed_ips() {
    // Decimal integer representation of 127.0.0.1
    assert!(validate_ssrf_safety("http://2130706433").is_err());
    // Hex representation of 127.0.0.1
    assert!(validate_ssrf_safety("http://0x7f000001").is_err());
}

#[test]
fn test_merkle_directory_cid() {
    let mut files = HashMap::new();
    files.insert("file_a.txt".to_string(), b"hello world".to_vec());
    files.insert("file_b.txt".to_string(), b"coreason rules".to_vec());

    let cid = compute_merkle_directory_cid(&files);
    assert!(cid.starts_with("sha256:"));

    // Hash must be deterministic. Changing insertion order should yield the same hash.
    let mut files_alt = HashMap::new();
    files_alt.insert("file_b.txt".to_string(), b"coreason rules".to_vec());
    files_alt.insert("file_a.txt".to_string(), b"hello world".to_vec());
    let cid_alt = compute_merkle_directory_cid(&files_alt);
    assert_eq!(cid, cid_alt);
}

#[test]
fn test_latent_alignment() {
    use base64::Engine;

    // Create base64 encoded f32 vectors
    // Vec 1: [1.0, 0.0]
    let f1 = vec![1.0f32, 0.0f32];
    let bytes1: Vec<u8> = f1.iter().flat_map(|x| x.to_ne_bytes().to_vec()).collect();
    let b64_1 = base64::engine::general_purpose::STANDARD.encode(&bytes1);

    // Vec 2: [1.0, 0.0] (Identical)
    let f2 = vec![1.0f32, 0.0f32];
    let bytes2: Vec<u8> = f2.iter().flat_map(|x| x.to_ne_bytes().to_vec()).collect();
    let b64_2 = base64::engine::general_purpose::STANDARD.encode(&bytes2);

    // Vec 3: [0.0, 1.0] (Orthogonal)
    let f3 = vec![0.0f32, 1.0f32];
    let bytes3: Vec<u8> = f3.iter().flat_map(|x| x.to_ne_bytes().to_vec()).collect();
    let b64_3 = base64::engine::general_purpose::STANDARD.encode(&bytes3);

    let v1 = VectorEmbeddingState {
        dimensionality: 2,
        foundation_matrix_name: FoundationMatrixName::try_from("test-model").unwrap(),
        temporal_decay_function: None,
        tenant_cid: None,
        time_derivative_vector: None,
        vector_base64: VectorBase64::try_from(b64_1.as_str()).unwrap(),
    };

    let v2 = VectorEmbeddingState {
        dimensionality: 2,
        foundation_matrix_name: FoundationMatrixName::try_from("test-model").unwrap(),
        temporal_decay_function: None,
        tenant_cid: None,
        time_derivative_vector: None,
        vector_base64: VectorBase64::try_from(b64_2.as_str()).unwrap(),
    };

    let v3 = VectorEmbeddingState {
        dimensionality: 2,
        foundation_matrix_name: FoundationMatrixName::try_from("test-model").unwrap(),
        temporal_decay_function: None,
        tenant_cid: None,
        time_derivative_vector: None,
        vector_base64: VectorBase64::try_from(b64_3.as_str()).unwrap(),
    };

    let policy_strict = EpistemicOntologicalAlignmentPolicy {
        fallback_state_contract: None,
        min_cosine_similarity: 0.9,
        require_isometry_proof: false,
        tenant_cid: None,
    };

    // Identical alignment should pass (similarity = 1.0)
    let res = calculate_latent_alignment(&v1, &v2, &policy_strict);
    assert!(res.is_ok());
    assert!((res.unwrap() - 1.0).abs() < 1e-6);

    // Orthogonal alignment should fail policy constraint (similarity = 0.0 < 0.9)
    let res_ortho = calculate_latent_alignment(&v1, &v3, &policy_strict);
    assert!(res_ortho.is_err());
    assert!(res_ortho.unwrap_err().contains("Latent alignment failed"));
}

#[test]
fn test_topology_hash() {
    let policy = EpistemicOntologicalAlignmentPolicy {
        fallback_state_contract: None,
        min_cosine_similarity: 0.85,
        require_isometry_proof: true,
        tenant_cid: None,
    };

    let hash_res = compute_topology_hash(&policy);
    assert!(hash_res.is_ok());
    let hash = hash_res.unwrap();
    assert_eq!(hash.len(), 64); // SHA-256 hex length
}
