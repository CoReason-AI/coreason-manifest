import json

with open('coreason_ontology.schema.json', 'r', encoding='utf-8') as f:
    schema = json.load(f)

any_state = schema['$defs']['AnyStateEvent']
mapping = any_state['discriminator']['mapping']

for key, ref in mapping.items():
    def_name = ref.split('/')[-1]
    def_schema = schema['$defs'][def_name]
    
    if 'properties' not in def_schema:
        print(f'ERROR: {def_name} has no properties')
        continue
        
    if 'topology_class' not in def_schema['properties']:
        print(f'ERROR: {def_name} is missing topology_class property!')
    else:
        tc = def_schema['properties']['topology_class']
        if 'const' in tc and tc['const'] != key:
            print(f'ERROR: {def_name} topology_class const ' + tc.get('const', '') + ' != mapping ' + key)

print("Discriminator check complete.")
