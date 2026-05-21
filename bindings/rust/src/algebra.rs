// Copyright (c) 2026 CoReason, Inc
// Licensed under the Prosperity Public License 3.0
// https://github.com/CoReason-AI/coreason-manifest

use crate::ontology::{EpistemicOntologicalAlignmentPolicy, VectorEmbeddingState};
use sha2::{Digest, Sha256};
use std::collections::HashMap;
use std::net::IpAddr;
use url::Url;

/// Validate a URL to prevent Server-Side Request Forgery (SSRF).
/// Mathematically blocks local, loopback, private, and bogon IP space without invoking dynamic DNS resolution.
pub fn validate_ssrf_safety(url_str: &str) -> Result<(), String> {
    let parsed =
        Url::parse(url_str).map_err(|e| format!("Invalid URL for SSRF validation: {}", e))?;

    let hostname = parsed
        .host_str()
        .ok_or_else(|| "URL is missing a hostname".to_string())?;

    let hostname_lower = hostname.to_lowercase();
    if hostname_lower == "localhost"
        || hostname_lower == "localhost.localdomain"
        || hostname_lower.ends_with(".localhost")
    {
        return Err(format!(
            "SSRF Security Violation: The target hostname '{}' resolves to the local loopback network.",
            hostname
        ));
    }

    // Remove IPv6 brackets if present
    let clean_host = if hostname_lower.starts_with('[') && hostname_lower.ends_with(']') {
        &hostname_lower[1..hostname_lower.len() - 1]
    } else {
        &hostname_lower
    };

    if let Ok(ip) = clean_host.parse::<IpAddr>() {
        check_ip_safety(&ip, hostname)?;
    } else {
        // Fallback check for non-standard IPv4 representations (octal, hex, decimal integers)
        if let Some(ip_val) = parse_packed_ipv4(clean_host) {
            check_ip_safety(&IpAddr::V4(ip_val), hostname)?;
        }
    }

    Ok(())
}

fn check_ip_safety(ip: &IpAddr, hostname: &str) -> Result<(), String> {
    let is_unsafe = match ip {
        IpAddr::V4(ipv4) => {
            ipv4.is_loopback()
                || ipv4.is_private()
                || ipv4.is_link_local()
                || ipv4.is_multicast()
                || ipv4.is_unspecified()
                || ipv4.is_broadcast()
                || ipv4.is_documentation()
                || !is_global_ipv4(ipv4)
        }
        IpAddr::V6(ipv6) => {
            ipv6.is_loopback()
                || ipv6.is_unspecified()
                || ipv6.is_multicast()
                || (ipv6.segments()[0] & 0xfe00) == 0xfc00 // unique local address (private)
                || (ipv6.segments()[0] & 0xffc0) == 0xfe80 // link local unicast
        }
    };

    if is_unsafe {
        return Err(format!(
            "SSRF Security Violation: The target IP address '{}' is not a valid global routing address.",
            hostname
        ));
    }
    Ok(())
}

fn is_global_ipv4(ipv4: &std::net::Ipv4Addr) -> bool {
    let octets = ipv4.octets();
    // 0.0.0.0/8
    if octets[0] == 0 {
        return false;
    }
    // 10.0.0.0/8
    if octets[0] == 10 {
        return false;
    }
    // 127.0.0.0/8
    if octets[0] == 127 {
        return false;
    }
    // 169.254.0.0/16
    if octets[0] == 169 && octets[1] == 254 {
        return false;
    }
    // 172.16.0.0/12
    if octets[0] == 172 && (octets[1] >= 16 && octets[1] <= 31) {
        return false;
    }
    // 192.0.0.0/24
    if octets[0] == 192 && octets[1] == 0 && octets[2] == 0 {
        return false;
    }
    // 192.0.2.0/24
    if octets[0] == 192 && octets[1] == 0 && octets[2] == 2 {
        return false;
    }
    // 192.88.99.0/24
    if octets[0] == 192 && octets[1] == 88 && octets[2] == 99 {
        return false;
    }
    // 192.168.0.0/16
    if octets[0] == 192 && octets[1] == 168 {
        return false;
    }
    // 198.18.0.0/15
    if octets[0] == 198 && (octets[1] == 18 || octets[1] == 19) {
        return false;
    }
    // 198.51.100.0/24
    if octets[0] == 198 && octets[1] == 51 && octets[2] == 100 {
        return false;
    }
    // 203.0.113.0/24
    if octets[0] == 203 && octets[1] == 0 && octets[2] == 113 {
        return false;
    }
    // 224.0.0.0/4 (multicast)
    if octets[0] >= 224 && octets[0] <= 239 {
        return false;
    }
    // 240.0.0.0/4 (reserved)
    if octets[0] >= 240 {
        return false;
    }

    true
}

fn parse_packed_ipv4(s: &str) -> Option<std::net::Ipv4Addr> {
    if let Ok(val) = s.parse::<u32>() {
        return Some(std::net::Ipv4Addr::from(val));
    }
    if s.starts_with("0x") || s.starts_with("0X") {
        if let Ok(val) = u32::from_str_radix(&s[2..], 16) {
            return Some(std::net::Ipv4Addr::from(val));
        }
    }
    None
}

/// Compute a Merkle-style SHA-256 CID over a set of named files.
/// This matches python's compute_merkle_directory_cid exactly.
pub fn compute_merkle_directory_cid(file_contents: &HashMap<String, Vec<u8>>) -> String {
    let mut sorted_keys: Vec<&String> = file_contents.keys().collect();
    sorted_keys.sort();

    let mut file_hashes = Vec::new();
    for filename in sorted_keys {
        let content = &file_contents[filename];
        let mut hasher = Sha256::new();
        hasher.update(content);
        let hash_hex = hex::encode(hasher.finalize());
        file_hashes.push(format!("{}:{}", filename, hash_hex));
    }

    let merkle_input = file_hashes.join("\n");
    let mut root_hasher = Sha256::new();
    root_hasher.update(merkle_input.as_bytes());
    let root_hash_hex = hex::encode(root_hasher.finalize());
    format!("sha256:{}", root_hash_hex)
}

/// Calculate cosine similarity of two vectors and ensure it meets the policy threshold.
pub fn calculate_latent_alignment(
    v1: &VectorEmbeddingState,
    v2: &VectorEmbeddingState,
    policy: &EpistemicOntologicalAlignmentPolicy,
) -> Result<f64, String> {
    if *v1.foundation_matrix_name != *v2.foundation_matrix_name
        || v1.dimensionality != v2.dimensionality
    {
        return Err(
            "Topological Contradiction: Vector geometries are incommensurable.".to_string(),
        );
    }

    use base64::Engine;
    let b1 = base64::engine::general_purpose::STANDARD
        .decode(v1.vector_base64.as_str())
        .map_err(|e| {
            format!(
                "Topological Contradiction: Invalid base64 encoding for v1: {}",
                e
            )
        })?;
    let b2 = base64::engine::general_purpose::STANDARD
        .decode(v2.vector_base64.as_str())
        .map_err(|e| {
            format!(
                "Topological Contradiction: Invalid base64 encoding for v2: {}",
                e
            )
        })?;

    if b1.len() % 4 != 0 || b2.len() % 4 != 0 {
        return Err(
            "Byte length does not match float32 alignment (must be a multiple of 4)".to_string(),
        );
    }

    let arr1: Vec<f32> = b1
        .chunks_exact(4)
        .map(|chunk| f32::from_ne_bytes(chunk.try_into().unwrap()))
        .collect();
    let arr2: Vec<f32> = b2
        .chunks_exact(4)
        .map(|chunk| f32::from_ne_bytes(chunk.try_into().unwrap()))
        .collect();

    if arr1.len() != v1.dimensionality as usize || arr2.len() != v2.dimensionality as usize {
        return Err("Byte length does not match declared dimensionality.".to_string());
    }

    let dot_product: f32 = arr1.iter().zip(&arr2).map(|(x, y)| x * y).sum();
    let norm1: f32 = arr1.iter().map(|x| x * x).sum::<f32>().sqrt();
    let norm2: f32 = arr2.iter().map(|x| x * x).sum::<f32>().sqrt();

    let mut similarity = if norm1 == 0.0 || norm2 == 0.0 {
        0.0
    } else {
        dot_product / (norm1 * norm2)
    };

    if similarity.is_nan() {
        similarity = 0.0;
    } else if similarity > 1.0 {
        similarity = 1.0;
    } else if similarity < -1.0 {
        similarity = -1.0;
    }

    if (similarity as f64) < policy.min_cosine_similarity {
        return Err("Latent alignment failed.".to_string());
    }

    Ok(similarity as f64)
}

/// Recursively canonicalize a serde_json::Value by sorting keys and removing Null values.
fn canonicalize_value(value: serde_json::Value) -> serde_json::Value {
    match value {
        serde_json::Value::Object(map) => {
            let mut new_map = serde_json::Map::new();
            for (k, v) in map {
                let canonical_v = canonicalize_value(v);
                if !canonical_v.is_null() {
                    new_map.insert(k, canonical_v);
                }
            }
            serde_json::Value::Object(new_map)
        }
        serde_json::Value::Array(arr) => {
            let canonical_arr = arr.into_iter().map(canonicalize_value).collect();
            serde_json::Value::Array(canonical_arr)
        }
        _ => value,
    }
}

/// Deterministically computes the SOTA Merkle-DAG SHA-256 fingerprint of a given topology.
pub fn compute_topology_hash<T: serde::Serialize>(topology: &T) -> Result<String, String> {
    let val = serde_json::to_value(topology)
        .map_err(|e| format!("Failed to serialize topology: {}", e))?;
    let canonical = canonicalize_value(val);
    let bytes = serde_json::to_vec(&canonical)
        .map_err(|e| format!("Failed to serialize canonical JSON: {}", e))?;

    let mut hasher = Sha256::new();
    hasher.update(&bytes);
    Ok(hex::encode(hasher.finalize()))
}

#[cfg(feature = "pyo3")]
use pyo3::prelude::*;

#[cfg(feature = "pyo3")]
#[pyfunction]
#[pyo3(name = "validate_ssrf_safety")]
pub fn py_validate_ssrf_safety(url_str: &str) -> PyResult<()> {
    validate_ssrf_safety(url_str).map_err(|e| pyo3::exceptions::PyValueError::new_err(e))
}

#[cfg(feature = "pyo3")]
#[pyfunction]
#[pyo3(name = "compute_merkle_directory_cid")]
pub fn py_compute_merkle_directory_cid(file_contents: HashMap<String, Vec<u8>>) -> String {
    compute_merkle_directory_cid(&file_contents)
}

#[cfg(feature = "pyo3")]
#[pyfunction]
#[pyo3(name = "calculate_latent_alignment")]
pub fn py_calculate_latent_alignment(
    v1_json: &str,
    v2_json: &str,
    policy_json: &str,
) -> PyResult<f64> {
    let r_v1: VectorEmbeddingState = serde_json::from_str(v1_json)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid v1 JSON: {}", e)))?;
    let r_v2: VectorEmbeddingState = serde_json::from_str(v2_json)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid v2 JSON: {}", e)))?;
    let r_policy: EpistemicOntologicalAlignmentPolicy =
        serde_json::from_str(policy_json).map_err(|e| {
            pyo3::exceptions::PyValueError::new_err(format!("Invalid policy JSON: {}", e))
        })?;

    calculate_latent_alignment(&r_v1, &r_v2, &r_policy)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(e))
}

#[cfg(feature = "pyo3")]
#[pyfunction]
#[pyo3(name = "compute_topology_hash")]
pub fn py_compute_topology_hash(topology_json: &str) -> PyResult<String> {
    let val: serde_json::Value = serde_json::from_str(topology_json).map_err(|e| {
        pyo3::exceptions::PyValueError::new_err(format!("Invalid topology JSON: {}", e))
    })?;
    compute_topology_hash(&val).map_err(|e| pyo3::exceptions::PyValueError::new_err(e))
}

/// Canonicalizes JSON and returns both the canonical JSON bytes and the SHA-256 hex digest.
pub fn canonicalize_json_and_hash(val: &serde_json::Value) -> Result<(Vec<u8>, String), String> {
    let canonical = canonicalize_value(val.clone());
    let bytes = serde_json::to_vec(&canonical)
        .map_err(|e| format!("Failed to serialize canonical JSON: {}", e))?;
    let mut hasher = Sha256::new();
    hasher.update(&bytes);
    let hash = hex::encode(hasher.finalize());
    Ok((bytes, hash))
}

#[cfg(feature = "pyo3")]
#[pyfunction]
#[pyo3(name = "canonicalize_json_and_hash")]
pub fn py_canonicalize_json_and_hash(json_str: &str) -> PyResult<(Vec<u8>, String)> {
    let val: serde_json::Value = serde_json::from_str(json_str)
        .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Invalid JSON: {}", e)))?;
    canonicalize_json_and_hash(&val).map_err(|e| pyo3::exceptions::PyValueError::new_err(e))
}
