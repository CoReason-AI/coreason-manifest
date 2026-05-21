pub mod ontology;
pub use ontology::*;

pub mod algebra;
pub use algebra::*;

#[cfg(feature = "pyo3")]
use pyo3::prelude::*;

#[cfg(feature = "pyo3")]
#[pymodule]
fn coreason_manifest_rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(algebra::py_validate_ssrf_safety, m)?)?;
    m.add_function(wrap_pyfunction!(
        algebra::py_compute_merkle_directory_cid,
        m
    )?)?;
    m.add_function(wrap_pyfunction!(algebra::py_calculate_latent_alignment, m)?)?;
    m.add_function(wrap_pyfunction!(algebra::py_compute_topology_hash, m)?)?;
    m.add_function(wrap_pyfunction!(algebra::py_canonicalize_json_and_hash, m)?)?;
    Ok(())
}
