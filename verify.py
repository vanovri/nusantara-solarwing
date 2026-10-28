"""Check the cached-data model and references without a network request."""
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit

root = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('solarwing_model', root / 'analyze.py')
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)
before = json.loads(model.OUT.read_text(encoding='utf-8'))
model.main()
after = json.loads(model.OUT.read_text(encoding='utf-8'))
assert after == before, 'Cached outputs differ from regenerated model'
assert after['summary']['days'] == 30
assert after['summary']['modeled_sortie_pass_days'] == 29
assert not model.simulate([0.0] * 24)['passes_reserve']
assert model.simulate([10000.0] * 24)['end_soc_pct'] == 100.0
checked = 0
for html in root.glob('*.html'):
    for reference in re.findall(r'(?:src|href)=["\x27]([^"\x27]+)', html.read_text(encoding='utf-8')):
        parsed = urlsplit(reference)
        if parsed.scheme or parsed.netloc or not parsed.path:
            continue
        assert (html.parent / unquote(parsed.path)).is_file(), reference
        checked += 1
assert checked > 0
print(f'PASS: model reproduced, 30 days, 29 reserve passes, boundary cases, {checked} local references')
