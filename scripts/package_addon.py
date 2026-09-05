"""Synchronize a self-contained Supervisor build context and install archive."""
from pathlib import Path
import shutil
import tarfile

root = Path(__file__).resolve().parents[1]
addon = root / 'inkypi_neoframe'
for name in ('src/display/neoframe_display.py', 'src/blueprints/frame.py',
             'scripts/apply_overlay.py', 'device.json', 'LICENSE', 'REFERENCES.md'):
    dest = addon / name
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(root / name, dest)
dockerfile = (root / 'Dockerfile').read_text()
dockerfile = dockerfile.replace('CMD ["python", "src/inkypi.py"]', '''ARG BUILD_VERSION=0.1.0
ARG BUILD_ARCH=amd64
LABEL io.hass.version="${BUILD_VERSION}" io.hass.type="app" io.hass.arch="${BUILD_ARCH}"
COPY run.py /run.py
CMD ["python", "/run.py"]''')
(addon / 'Dockerfile').write_text(dockerfile)
(root / 'dist').mkdir(exist_ok=True)
with tarfile.open(root / 'dist/inkypi-neoframe-haos.tar.gz', 'w:gz') as archive:
    for path in sorted(addon.rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts:
            archive.add(path, arcname=path.relative_to(root))
print('Created dist/inkypi-neoframe-haos.tar.gz')
