from coreason_manifest.v2.spec.definitions import ManifestMetadata

m = ManifestMetadata(name="test", requires_auth=True)
print(f"getattr: {getattr(m, 'requires_auth', 'NOT_FOUND')}")
print(f"model_extra: {m.model_extra}")
