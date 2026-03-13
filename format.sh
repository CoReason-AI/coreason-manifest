#!/bin/bash
grep -E '^(def |class |@|import|from|    )' tests/test_new_ontology_validators.py > temp.py
# That regex is too dangerous.
