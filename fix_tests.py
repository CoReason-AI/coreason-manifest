import re

# Fix tests/contracts/test_domain_extensions.py
with open('tests/contracts/test_domain_extensions.py', 'r') as f:
    content = f.read()

# Replace BaseNodeProfile with AgentNodeProfile
content = content.replace('BaseNodeProfile', 'AgentNodeProfile')

with open('tests/contracts/test_domain_extensions.py', 'w') as f:
    f.write(content)

# Fix tests/fuzzing/test_instantiation_bounds.py
with open('tests/fuzzing/test_instantiation_bounds.py', 'r') as f:
    content = f.read()

# Replace BaseStateEvent with ObservationEvent
# Note: ObservationEvent has `payload` requirement. ObservationEvent might require `payload={"a":"b"}` or something.
# Let's check ObservationEvent definition. It requires payload.
content = content.replace('BaseStateEvent(', 'ObservationEvent(payload={}, ')
content = content.replace('BaseStateEvent,', 'ObservationEvent,')

with open('tests/fuzzing/test_instantiation_bounds.py', 'w') as f:
    f.write(content)
