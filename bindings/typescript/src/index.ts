// Copyright (c) 2026 CoReason, Inc
// Licensed under the Prosperity Public License 3.0
// https://github.com/CoReason-AI/coreason-manifest

export * from './ontology';
import stringify from 'fast-json-stable-stringify';
import { ExecutionEnvelopeState } from './ontology';

/**
 * AGENT INSTRUCTION: Recursively strips null and undefined values from the payload.
 * Matches the exact physics of Python's `_canonicalize_payload` to guarantee that
 * omitted properties do not fracture the RFC 8785 canonical hash.
 */
function canonicalizePayload(obj: any): any {
    if (Array.isArray(obj)) {
        return obj.map(canonicalizePayload);
    } else if (obj !== null && typeof obj === 'object') {
        const newObj: any = {};
        for (const key of Object.keys(obj)) {
            const val = obj[key];
            if (val !== null && val !== undefined) {
                newObj[key] = canonicalizePayload(val);
            }
        }
        return newObj;
    }
    return obj;
}

/**
 * Deterministically serializes an ExecutionEnvelopeState using a stable key-sorting algorithm.
 * Guarantees RFC 8785 byte-for-byte serialization invariance when VSCode transmits JSON-RPC envelopes
 * across the network, exactly matching Python's DeterministicTransportAdapter.
 */
export function serializeEnvelope(envelope: ExecutionEnvelopeState<any>): string {
    // 1. Strip nulls to match Python's exclusion physics
    const canonicalParams = canonicalizePayload(envelope);
    
    // 2. Wrap in the JSON-RPC 2.0 Shell
    const wrappedPayload = {
        jsonrpc: "2.0",
        method: "coreason_execute",
        params: canonicalParams,
        // Extract the trace_cid to use as the RPC request ID
        id: canonicalParams.trace_context?.trace_cid || "unknown" 
    };

    // 3. Deterministically sort keys and stringify
    return stringify(wrappedPayload);
}
