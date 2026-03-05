from coreason_manifest.state.differentials import RollbackRequest
from typing import Any
import pydantic

class MyRollback(RollbackRequest):
    def model_post_init(self, __context: Any) -> None:
        print("model_post_init called with:", self.invalidated_node_ids)
        super().model_post_init(__context)

req1 = MyRollback(request_id="r1", target_event_id="e_3", invalidated_node_ids=["node_z", "node_a", "node_k"])
req2 = MyRollback(request_id="r1", target_event_id="e_3", invalidated_node_ids=["node_k", "node_z", "node_a"])
print("req1:", req1.invalidated_node_ids)
print("req2:", req2.invalidated_node_ids)
