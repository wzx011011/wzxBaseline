import json
import zipfile
import tempfile
from pathlib import Path

src = Path(r'e:\wzx\C3DBaseline\test_framework\engine_params\data\models\process\strength\walls\wall_loops\wall_loops_arachne_0.3mf')

with tempfile.TemporaryDirectory() as tmpdir:
    tmppath = Path(tmpdir)
    with zipfile.ZipFile(src, 'r') as zf:
        zf.extractall(tmppath)
    
    config_file = tmppath / 'Metadata' / 'project_settings.config'
    with open(config_file, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    wg = config.get('wall_generator')
    wl = config.get('wall_loops')
    print("wall_generator:", wg)
    print("wall_loops:", wl)
