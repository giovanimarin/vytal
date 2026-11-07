"""LAN launcher; retain SQLite, secure app storage and local authentication keys."""
import ipaddress
import json
import os
import secrets
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import quote

import httpx
import yaml
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[2]


def prepare(root, supplied=None):
    """Resolve persistent state without replacing existing keys or databases."""
    backend = root / 'backend'
    state = root / '.local-vytal'
    state.mkdir(mode=0o700, parents=True, exist_ok=True)
    env = {**dotenv_values(backend / '.env'), **os.environ}
    if env.get('K_SERVICE') or env.get('ENVIRONMENT', 'local') not in ('local', 'dev', 'development'):
        raise ValueError('Launcher exclusivo do backend local.')
    configs = [Path(env['CONFIG_PATH'])] if env.get('CONFIG_PATH') else [
        state / 'linux-config.json', state / 'windows-config.json', backend / 'config.yaml']
    databases = []
    for path in configs:
        if not path.is_absolute():
            path = backend / path
        if path.exists():
            config = yaml.safe_load(path.read_text())
            if config.get('cloud', {}).get('provider') != 'local':
                raise ValueError('Configuração de nuvem recusada; selecione SQLite local.')
            db = Path(config['local']['db_path'])
            databases.append(db if db.is_absolute() else backend / db)
    existing = {p.resolve() for p in databases if p.exists()}
    if supplied:
        db = Path(supplied).resolve()
    elif len(existing) > 1:
        raise ValueError('SQLite ambíguo. Defina VYTAL_DATABASE_PATH; nenhum banco foi alterado.')
    else:
        db = next(iter(existing)) if existing else (databases[0] if databases else backend / 'data/vytal.db').resolve()
    keys_file = state / 'keys.json'  # same keys file as the Windows launcher
    if keys_file.exists():
        keys = json.loads(keys_file.read_text(encoding='utf-8-sig'))
        if any(not keys.get(key) for key in ('SECRET_KEY', 'JWT_SECRET_KEY')):
            raise ValueError('Chaves locais inválidas; não foram sobrescritas.')
        for key in keys:
            if env.get(key) and env[key] != keys[key]:
                raise ValueError('Conflito entre chaves existentes e .env; preserve a configuração original.')
        env.update(keys)
    else:
        keys = {key: env.get(key) or secrets.token_urlsafe(48) for key in ('SECRET_KEY', 'JWT_SECRET_KEY')}
        with keys_file.open('x', encoding='utf-8') as file:
            os.chmod(keys_file, 0o600)
            json.dump(keys, file)
        env.update(keys)
    config_path = state / 'linux-config.json'
    config_path.write_text(json.dumps({'cloud': {'provider': 'local'},
        'local': {'db_path': str(db), 'data_dir': str(db.parent)}}))
    env.update(ENVIRONMENT='local', CONFIG_PATH=str(config_path))
    env.setdefault('GOOGLE_CLIENT_ID', 'local-not-configured')
    env.setdefault('GOOGLE_CLIENT_SECRET', 'local-not-configured')
    return env, db


def main():
    address, run = sys.argv[1:]
    ip = ipaddress.IPv4Address(address)
    if not (ip in ipaddress.ip_network('10.0.0.0/8') or ip in ipaddress.ip_network('172.16.0.0/12')
            or ip in ipaddress.ip_network('192.168.0.0/16')) or not run.isdigit():
        raise ValueError('Use IPv4 LAN privado e RUN_ID numérico.')
    # Fail before writes if this is not a local interface, or ports are already in use.
    for port in (8000, 8081):
        with socket.socket() as probe:
            probe.bind((address, port))
    env, db = prepare(ROOT, os.environ.get('VYTAL_DATABASE_PATH'))
    apk_dir = ROOT / '.local-vytal' / ('apk-' + run)
    apk_dir.mkdir(exist_ok=True)
    if not (apk_dir / 'app-debug.apk').exists():
        subprocess.run(['gh', 'run', 'download', run, '--repo', 'giovanimarin/vytal',
            '--name', 'android-health-connect-debug-apk', '--dir', str(apk_dir)], check=True)
    subprocess.run(['adb', 'install', '-r', str(apk_dir / 'app-debug.apk')], check=True)
    # Never retry INSTALL_FAILED_UPDATE_INCOMPATIBLE with uninstall or data clear.
    workers = []
    try:
        workers.append(subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', address, '--port', '8000'],
                                        cwd=ROOT / 'backend', env=env))
        for _ in range(60):
            try:
                if httpx.get(f'http://{address}:8000/health', trust_env=False).status_code == 200:
                    break
            except httpx.HTTPError:
                pass
            if workers[0].poll() is not None:
                raise RuntimeError('Backend local encerrou antes de iniciar.')
            time.sleep(.5)
        else:
            raise RuntimeError('Backend local não iniciou na rede LAN.')
        metro_env = dict(os.environ, NODE_ENV='development', EXPO_PUBLIC_API_URL=f'http://{address}:8000/api/v1',
                         REACT_NATIVE_PACKAGER_HOSTNAME=address, EXPO_OFFLINE='1', EXPO_NO_TELEMETRY='1')
        workers.append(subprocess.Popen(['npx', 'expo', 'start', '--dev-client', '--lan'],
                                        cwd=ROOT / 'mobile/vytal-app', env=metro_env))
        for _ in range(120):
            try:
                if 'running' in httpx.get('http://127.0.0.1:8081/status').text:
                    break
            except httpx.HTTPError:
                pass
            if workers[-1].poll() is not None:
                raise RuntimeError('Metro encerrou antes de iniciar.')
            time.sleep(.5)
        else:
            raise RuntimeError('Metro não iniciou.')
        url = 'exp+vytal://expo-development-client/?url=' + quote(f'http://{address}:8081', safe='')
        subprocess.run(['adb', 'shell', 'am', 'start', '-W', '-a', 'android.intent.action.VIEW',
                        '-d', url, 'com.vytal.app'], check=True)
        print(f'Backend SQLite: {db}\nMetro: http://{address}:8081\nCtrl+C encerra serviços; dados permanecem.', flush=True)
        while all(worker.poll() is None for worker in workers):
            time.sleep(1)
    finally:
        for worker in reversed(workers):
            if worker.poll() is None:
                worker.terminate()
                try:
                    worker.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    worker.kill()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
