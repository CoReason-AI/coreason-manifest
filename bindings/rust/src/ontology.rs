#![allow(non_snake_case)]
#![allow(non_camel_case_types)]
// Example code that deserializes and serializes the model.
// extern crate serde;
// #[macro_use]
// extern crate serde_derive;
// extern crate serde_json;
//
// use generated_module::ontology;
//
// fn main() {
//     let json = r#"{"answer": 42}"#;
//     let model: ontology = serde_json::from_str(&json).unwrap();
// }

use serde::{Deserialize, Serialize};

pub type Ontology = Option<serde_json::Value>;
