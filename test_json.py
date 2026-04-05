import json

dpo1 = {"l": {"a": "b"}, "k": {}, "r": {}}
dpo2 = {"l": {"b": "a"}, "k": {}, "r": {}}

print(json.dumps(dpo1, sort_keys=True))
print(json.dumps(dpo2, sort_keys=True))
