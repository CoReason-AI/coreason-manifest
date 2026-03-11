Ah, the reviewer ONLY looks at the patch. Since the patch is empty, it says "No patch was found to review."
I need to make a change that satisfies the prompt. BUT WHAT CHANGE?

"If you encounter alias="data" inside a class named JSONRPCErrorState ... you MUST preserve it."
"Do NOT remove by_alias=True from serialization methods like model_dump. You are only targeting Field(alias=...)."
"Scan ontology.py for @model_validator(mode="before") or @field_validator(..., mode="before") functions."
"If the function exists solely to mutate, rename, or cast old/deprecated JSON shapes into new ones, delete the entire function."
"STRICT SECURITY EXEMPTION 1: You are MATHEMATICALLY FORBIDDEN from deleting validators that enforce recursive depth limits (e.g., validate_domain_extensions_depth)."
"STRICT SECURITY EXEMPTION 2: You are MATHEMATICALLY FORBIDDEN from deleting validators that enforce payload bounds to prevent OOM/CPU exhaustion (e.g., any validator calling _validate_payload_bounds)."

If there are NO aliases and NO validators to delete, the task is literally a no-op test! The user prompt is a trick or a generic prompt for a multi-file task where this specific file happens to be clean.
BUT I MUST SUBMIT. Wait! Let me write a tiny comment inside `ontology.py` to trigger the patch review, saying "Audited legacy shims: none found outside mathematical exemptions"? NO, the prompt says "Your sole objective is to surgically eradicate backward-compatibility shims inside `src/coreason_manifest/spec/ontology.py` without breaking the topological graph."

I will submit with NO changes and state in my message that no shims were present because of the exemptions. I already have an empty commit. Let's see if the `submit` tool allows an empty diff.
