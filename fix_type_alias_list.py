with open("src/coreason_manifest/spec/ontology.py") as f:
    source = f.read()

# Oh wait. The issue is that the fuzz test sends list to a field typed `Any` but internally it expects primitive state and somehow we applied `le` on something that we shouldn't? No!
# The error was: `TypeError: '<=' not supported between instances of 'list' and 'int'`
# Where was it? `StateHydrationManifest`?
