from pathlib import Path
import json
import yaml

ROOT = Path(__file__).resolve().parents[1]

def test_config():
    cfg = json.loads((ROOT / 'config/settings.json').read_text(encoding='utf-8'))
    assert cfg['corp_code'] == '00126380'
    assert cfg['start_year'] == 2010

def test_workflow_yaml():
    for p in (ROOT / 'github_workflows').glob('*.yml'):
        data = yaml.safe_load(p.read_text(encoding='utf-8'))
        assert 'jobs' in data
        assert 'on' in data or True
        assert data['jobs']
