"""Inspect compiled DEX, ABIs and permissions, not just the JS bundle."""
import hashlib
import pathlib
import subprocess
import sys
import zipfile

apk = pathlib.Path(sys.argv[1])
with zipfile.ZipFile(apk) as archive:
    dex = b''.join(archive.read(n) for n in archive.namelist() if n.endswith('.dex'))
    for name in (b'expo/modules/webbrowser/WebBrowserModule', b'expo/modules/securestore/SecureStoreModule',
                 b'expo/modules/linking/ExpoLinkingModule', b'HealthConnectModule', b'HealthConnectPermissionReactActivityHandler', b'HealthPermissionsActivity'):
        assert name in dex, f'Compiled native module missing: {name!r}'
    for abi in ('arm64-v8a', 'x86_64'):
        assert any(n.startswith(f'lib/{abi}/') for n in archive.namelist()), f'Missing {abi}'
permissions = subprocess.check_output(['aapt', 'dump', 'permissions', str(apk)], text=True)
assert 'android.permission.health.READ_STEPS' in permissions
assert 'android.permission.health.WRITE_' not in permissions
subprocess.run(['apksigner', 'verify', str(apk)], check=True)
print(f'{apk.name}: compiled modules, ARM64/emulator ABIs, read-only HC and signature OK')
print('SHA256', hashlib.sha256(apk.read_bytes()).hexdigest())
