from coreason_manifest.state.differentials import RollbackRequest

req1 = RollbackRequest(request_id="r1", target_event_id="e_3", invalidated_node_ids=["node_z", "node_a", "node_k"])
req2 = RollbackRequest(request_id="r1", target_event_id="e_3", invalidated_node_ids=["node_k", "node_z", "node_a"])

print(hash(req1), hash(req2))
print(req1._cached_hash, req2._cached_hash)
print(req1.invalidated_node_ids)
print(req2.invalidated_node_ids)

import json
print(req1.model_dump_canonical())
print(req2.model_dump_canonical())
