import re

with open("src/coreason_manifest/spec/ontology.py", "r", encoding="utf-8") as f:
    content = f.read()

content = re.sub(r'sorted\(self\.concurrent_branch_ids\)', r'sorted(self.concurrent_branch_cids)', content)
content = re.sub(r'sorted\(self\.protected_event_ids\)', r'sorted(self.protected_event_cids)', content)
content = re.sub(r'sorted\(self\.space_ids\)', r'sorted(self.space_cids)', content)
content = re.sub(r'sorted\(self\.panel_ids\)', r'sorted(self.panel_cids)', content)
content = re.sub(r'sorted\(self\.step_ids\)', r'sorted(self.step_cids)', content)
content = re.sub(r'sorted\(self\.quarantined_ids\)', r'sorted(self.quarantined_cids)', content)
content = re.sub(r'sorted\(self\.shocks,\s*key=operator\.attrgetter\("shock_id"\)\)', r'sorted(self.shocks, key=operator.attrgetter("shock_cid"))', content)


with open("src/coreason_manifest/spec/ontology.py", "w", encoding="utf-8") as f:
    f.write(content)
