with open("src/coreason_manifest/spec/ontology.py") as f:
    content = f.read()

# Update AnyIntent
old_intent = "type AnyIntent = Annotated["
new_intent = "type AnyIntent = Annotated[\n    EpistemicZeroTrustContract |"
content = content.replace(old_intent, new_intent)

# Update AnyStateEvent
old_event = "type AnyStateEvent = Annotated["
new_event = "type AnyStateEvent = Annotated[\n    EpistemicZeroTrustReceipt |"
content = content.replace(old_event, new_event)

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(content)
