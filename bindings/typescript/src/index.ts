// Copyright (c) 2026 CoReason, Inc
// Licensed under the Prosperity Public License 3.0
// https://github.com/CoReason-AI/coreason-manifest

export * from './ontology';
import stringify from 'fast-json-stable-stringify';
import { ExecutionEnvelopeState } from './ontology';

/**
 * Deterministically serializes an ExecutionEnvelopeState using a stable key-sorting algorithm.
 * Guarantees RFC 8785 byte-for-byte serialization invariance when VSCode transmits JSON-RPC envelopes
 * across the network, matching Python's DeterministicTransportAdapter.
 */
export function serializeEnvelope(envelope: ExecutionEnvelopeState): string {
    return stringify(envelope);
}
