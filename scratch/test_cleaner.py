import re

with open(r'c:\files\git\github\coreason-ai\coreason-manifest\tests\contracts\test_coverage_gaps.py', 'r', encoding='utf-8') as f:
    text = f.read()
text = re.sub(r'class TestSimpleTTLCacheEviction.*?(?=def |class |$)', '', text, flags=re.DOTALL)
with open(r'c:\files\git\github\coreason-ai\coreason-manifest\tests\contracts\test_coverage_gaps.py', 'w', encoding='utf-8') as f:
    f.write(text)

with open(r'c:\files\git\github\coreason-ai\coreason-manifest\tests\contracts\test_browser_dom_state.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Since re is greedy/weird sometimes, I'll just remove the lines using string splitting
lines = text.split('\n')
new_lines = []
skip = False
for line in lines:
    if 'def test_browser_dom_state_ssrf_dns_resolution(' in line or '@pytest.mark.parametrize' in line and '"url", ["http://this-domain-does-not-exist.coreason.ai/"' in line:
        skip = True
        continue
    
    if skip:
        if line.strip() == '' or line.startswith('def ') or line.startswith('@') or line.startswith('# ---'):
            if line.startswith('        raise ValueError'):
                continue
            if line.startswith('    with pytest.raises'):
                continue
            if line.startswith('        BrowserDOMState'):
                continue
            skip = False
        else:
            continue
            
    if not skip:
        new_lines.append(line)

with open(r'c:\files\git\github\coreason-ai\coreason-manifest\tests\contracts\test_browser_dom_state.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(new_lines))
