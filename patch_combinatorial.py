with open("src/coreason_manifest/oracles/combinatorial.py", "r") as f:
    content = f.read()

# the code review also mentioned: "placing large objects in a multiprocessing.Queue and then calling join() before get() creates a high risk of process deadlock due to pipe buffer limits"
# Let's read from queue first, and use timeout with get
replacement = """        process.start()

        receipt = None
        try:
            receipt = queue.get(timeout=timeout_sec)
        except multiprocessing.queues.Empty:
            pass

        process.join(0)

        if process.is_alive():
            process.kill()
            process.join()
            return FormalLogicProofReceipt(
                satisfiability="UNKNOWN",
                event_cid=event_cid,
                causal_provenance_id=provenance_id,
                timestamp=time.time(),
                counter_model=CombinatorialCounterModel(
                    failed_premise_cid=provenance_id,
                    unsat_core=["Execution terminated: Thermodynamic bound exceeded (SIGKILL applied)."],
                ),
                answer_sets=[],
            )

        if receipt is not None:
            return typing.cast("FormalLogicProofReceipt", receipt)"""

# I need to find the correct piece to replace
import re
pattern = re.compile(r"        process\.start\(\)\n        process\.join\(timeout_sec\)\n\n        if process\.is_alive\(\):\n            process\.kill\(\)\n            process\.join\(\)\n            return FormalLogicProofReceipt\(\n                satisfiability=\"UNKNOWN\",\n                event_cid=event_cid,\n                causal_provenance_id=provenance_id,\n                timestamp=time\.time\(\),\n                counter_model=CombinatorialCounterModel\(\n                    failed_premise_cid=provenance_id,\n                    unsat_core=\[\"Execution terminated: Thermodynamic bound exceeded \(SIGKILL applied\)\.\"\],\n                \),\n                answer_sets=\[\\],\n            \)\n\n        if not queue\.empty\(\):\n            return typing\.cast\(\"FormalLogicProofReceipt\", queue\.get\(\)\)")

content = pattern.sub(replacement, content)
import queue
content = content.replace("multiprocessing.queues.Empty", "queue.Empty")
if "import queue" not in content:
    content = "import queue\n" + content

with open("src/coreason_manifest/oracles/combinatorial.py", "w") as f:
    f.write(content)
