from pydantic import TypeAdapter
from coreason_manifest.workflow.topologies import AnyTopology

topology_adapter: TypeAdapter[AnyTopology] = TypeAdapter(AnyTopology)
