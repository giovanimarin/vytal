"""Real APK + Metro + SQLite + emulator HC. All identities/data are synthetic.
No app-data clear, uninstall, mocked React Native modules or cloud backend.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote

import httpx

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ.get('SMOKE_OUTPUT', ROOT / 'android-smoke-results')).resolve()
OUT.mkdir(parents=True, exist_ok=True)
APP = 'com.vytal.app'
FIXTURE = 'org.vytal.smokefixture'
checks = []


def adb(*args):
    return subprocess.check_output(['adb', *args], text=True, stderr=subprocess.STDOUT, timeout=30)


def tree():
    adb('shell', 'uiautomator', 'dump', '--compressed', '/sdcard/vytal-smoke.xml')
    value = adb('shell', 'cat', '/sdcard/vytal-smoke.xml')
    assert not re.search(r'Cannot find native module|Unable to resolve module|Render Error|Uncaught Error', value), value
    return ET.fromstring(value)


def find(selector):
    for node in tree().iter('node'):
        if (node.get('resource-id', '').split('/')[-1] == selector
                or selector in node.get('text', '') or selector == node.get('content-desc')):
            return node
    return None


def wait(selector, timeout=90):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        node = find(selector)
        if node is not None:
            return node
        time.sleep(1)
    raise AssertionError(f'UI did not show {selector}')


def tap(selector, scroll=False):
    directions = [None] + ['down'] * 4 + ['up'] * 8 if scroll else [None]
    for direction in directions:
        if direction:
            dimensions = re.findall(r'(\d+)x(\d+)', adb('shell', 'wm', 'size'))[-1]
            width, height = map(int, dimensions)
            first, second = (int(height * .8), int(height * .3))
            if direction == 'up':
                first, second = second, first
            adb('shell', 'input', 'swipe', str(width//2), str(first), str(width//2), str(second), '400')
            time.sleep(.5)
        node = find(selector)
        if node is not None:
            x1, y1, x2, y2 = map(int, re.findall(r'\d+', node.get('bounds')))
            if x2 > x1 and y2 > y1:
                adb('shell', 'input', 'tap', str((x1+x2)//2), str((y1+y2)//2))
                return
    raise AssertionError(f'UI element not tappable: {selector}')


def enter(selector, text):
    wait(selector)
    tap(selector)
    adb('shell', 'input', 'text', text)
    adb('shell', 'input', 'keyevent', '111')  # dismiss keyboard, keep route


def link(route):
    adb('shell', 'am', 'start', '-W', '-a', 'android.intent.action.VIEW', '-d', 'vytal://' + route, APP)


def evidence(name):
    (OUT / (name + '.xml')).write_text(ET.tostring(tree(), encoding='unicode'))
    with (OUT / (name + '.png')).open('wb') as file:
        subprocess.run(['adb', 'exec-out', 'screencap', '-p'], stdout=file, check=True)
    checks.append(name)
    print('PASS:', name, flush=True)


def sources():
    wait('dashboard-menu')
    tap('dashboard-menu')
    wait('Fontes de Dados')
    tap('Fontes de Dados')
    wait('hc-connect')


def signout():
    tap('dashboard-menu')
    wait('Sair')
    tap('Sair')
    wait('login-submit')


def signin(email, password):
    enter('login-email', email)
    enter('login-password', password)
    tap('login-submit')
    wait('dashboard-menu')


def run():
    assert adb('shell', 'getprop', 'ro.kernel.qemu').strip() == '1', 'Smoke only runs on a dedicated emulator; physical devices are refused'
    assert int(adb('shell', 'getprop', 'ro.build.version.sdk').strip()) >= 34, 'Smoke requires Android 14 Health Connect'
    # CI always uses a new temporary backend/DB; never a developer's database.
    with tempfile.TemporaryDirectory(prefix='vytal-android-smoke-') as directory:
        state = Path(directory)
        (state / 'config.yaml').write_text(json.dumps({'cloud': {'provider': 'local'},
            'local': {'db_path': str(state / 'smoke.db'), 'data_dir': str(state)}}))
        env = dict(os.environ, ENVIRONMENT='test', CONFIG_PATH=str(state / 'config.yaml'),
                   SECRET_KEY=os.urandom(48).hex(), JWT_SECRET_KEY=os.urandom(48).hex(),
                   GOOGLE_CLIENT_ID='synthetic-smoke', GOOGLE_CLIENT_SECRET='synthetic-smoke',
                   PYTHONPATH=str(ROOT / 'backend'))
        backend_log = (OUT / 'backend.log').open('w')
        metro_log = (OUT / 'metro.log').open('w')
        backend = None
        metro = None

        def start_backend():
            process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '8000'],
                                       cwd=ROOT / 'backend', env=env, stdout=backend_log, stderr=subprocess.STDOUT)
            for _ in range(60):
                try:
                    if httpx.get('http://127.0.0.1:8000/health').status_code == 200:
                        return process
                except httpx.HTTPError:
                    pass
                if process.poll() is not None:
                    raise AssertionError('Backend stopped; see backend.log')
                time.sleep(.5)
            process.terminate()
            raise AssertionError('Backend startup timed out')

        client = httpx.Client(base_url='http://127.0.0.1:8000/api/v1', timeout=20)
        try:
            backend = start_backend()
            metro_env = dict(os.environ, NODE_ENV='development', EXPO_OFFLINE='1', CI='1',
                             EXPO_NO_TELEMETRY='1', EXPO_PUBLIC_API_URL='http://10.0.2.2:8000/api/v1',
                             EXPO_PACKAGER_PROXY_URL='http://10.0.2.2:8081', REACT_NATIVE_PACKAGER_HOSTNAME='10.0.2.2')
            metro = subprocess.Popen(['node', 'node_modules/expo/bin/cli', 'start', '--dev-client', '--localhost', '--clear'],
                cwd=ROOT / 'mobile/vytal-app', env=metro_env, stdout=metro_log, stderr=subprocess.STDOUT)
            for _ in range(120):
                try:
                    if 'running' in httpx.get('http://127.0.0.1:8081/status').text:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(.5)
            else:
                raise AssertionError('Metro startup timed out')
            manifest = httpx.get('http://127.0.0.1:8081/', headers={
                'accept': 'application/expo+json', 'expo-platform': 'android', 'expo-protocol-version': '1'}, timeout=90).raise_for_status().json()
            assert manifest['launchAsset']['url'].startswith('http://10.0.2.2:8081/'), 'Metro must advertise a bundle URL reachable from Android'
            assert manifest['extra']['expoClient']['extra']['apiUrl'] == 'http://10.0.2.2:8000/api/v1'
            adb('logcat', '-c')
            adb('install', '-r', str(ROOT / 'mobile/vytal-app/android/app/build/outputs/apk/debug/app-debug.apk'))
            fixture_apk = ROOT / 'tests/android-fixture/build/outputs/apk/debug/android-fixture-debug.apk'
            # Gradle uses the included project name as the archive name.
            if not fixture_apk.exists():
                fixture_apk = next((ROOT / 'tests/android-fixture/build/outputs/apk/debug').glob('*.apk'))
            adb('install', '-r', str(fixture_apk))
            url = 'exp+vytal://expo-development-client/?url=' + quote('http://10.0.2.2:8081', safe='')
            adb('shell', 'am', 'start', '-W', '-a', 'android.intent.action.VIEW', '-d', url, APP)
            # Dev-client first-launch UI may show a one-time welcome overlay.
            boot_deadline = time.monotonic() + 150
            while time.monotonic() < boot_deadline:
                if find('login-submit') is not None:
                    break
                for text in ('Continue', 'Got it'):
                    if find(text) is not None:
                        tap(text)
                time.sleep(1)
            wait('login-submit', timeout=10)
            evidence('01-boot-login-no-red-screen')
            stamp = str(time.time_ns())
            email_a, email_b = f'smoke-a-{stamp}@example.invalid', f'smoke-b-{stamp}@example.invalid'
            password = 'synthetic-pass-123'
            tap('Criar conta')
            enter('register-name', 'Synthetic')
            enter('register-email', email_a)
            enter('register-password', password)
            enter('register-confirmPassword', password)
            tap('register-submit', scroll=True)
            time.sleep(2)
            tap('Pular por agora', scroll=True)
            wait('dashboard-menu')
            evidence('02-registration-dashboard')
            signout()
            signin(email_a, password)
            evidence('03-real-login')
            # Eager WebBrowser import on the actual /connect route reproduces #27.
            link('connect')
            wait('Conectar com Google Fit')
            tap('Conectar com Google Fit')
            for _ in range(30):
                activity = adb('shell', 'dumpsys', 'activity', 'activities')
                if re.search(r'(mResumedActivity|topResumedActivity).*com\.android\.chrome', activity):
                    break
                time.sleep(1)
            else:
                raise AssertionError('Native WebBrowser did not open Chrome from Google Fit route')
            evidence('04-google-fit-native-webbrowser-opens-chrome')
            adb('shell', 'input', 'keyevent', '4')
            link('')
            sources()
            evidence('05-data-sources-health-connect')
            tap('hc-connect', scroll=True)
            # Real Android permission sheet: deny via Back, then verify app state.
            time.sleep(2)
            adb('shell', 'input', 'keyevent', '4')
            wait('Permissão negada')
            evidence('06-real-native-permission-denied')
            reads = ['EXERCISE', 'STEPS', 'DISTANCE', 'ACTIVE_CALORIES_BURNED', 'TOTAL_CALORIES_BURNED',
                     'HEART_RATE', 'RESTING_HEART_RATE', 'SLEEP', 'WEIGHT', 'SPEED', 'ELEVATION_GAINED']
            for kind in reads:
                adb('shell', 'pm', 'grant', APP, 'android.permission.health.READ_' + kind)
            tap('hc-connect', scroll=True)
            wait('Sem registros para o filtro')
            evidence('07-real-native-empty-read')
            adb('shell', 'pm', 'grant', FIXTURE, 'android.permission.health.WRITE_STEPS')
            adb('shell', 'am', 'start', '-W', '-n', FIXTURE + '/.MainActivity')
            wait('SYNTHETIC_STEPS_INSERTED')
            evidence('08-separate-synthetic-hc-writer')
            link('data-sources')
            wait('hc-origin')
            tap('hc-origin', scroll=True)
            tap('hc-rescan', scroll=True)
            wait('1 registros importados')
            evidence('09-real-native-hc-import-synthetic-origin')
            token = client.post('/auth/login', json={'email': email_a, 'password': password}).raise_for_status().json()['access_token']
            headers = {'Authorization': 'Bearer ' + token}
            data = client.get('/health-connect/records', headers=headers).raise_for_status().json()
            assert data['retained_raw'] == 1 and data['records'][0]['origin'] == FIXTURE, data
            tap('hc-rescan', scroll=True)
            wait('1 registros importados')
            assert client.get('/health-connect/records', headers=headers).json()['retained_raw'] == 1
            evidence('10-replay-deduplicated')
            backend.terminate()
            backend.wait(timeout=10)
            tap('hc-sync', scroll=True)
            wait('Falha na importação', timeout=120)
            evidence('11-network-error-preserves-session')
            backend = start_backend()  # same SQLite, same keys
            tap('hc-sync', scroll=True)
            wait('1 registros importados')
            evidence('12-backend-restart-preserves-sqlite')
            signout()
            client.post('/auth/register', json={'name': 'Synthetic B', 'email': email_b, 'password': password}).raise_for_status()
            signin(email_b, password)
            sources()
            tap('hc-origin', scroll=True)
            evidence('13-account-b-no-account-a-records')
            token_b = client.post('/auth/login', json={'email': email_b, 'password': password}).raise_for_status().json()['access_token']
            assert client.get('/health-connect/records', headers={'Authorization': 'Bearer ' + token_b}).json()['records'] == []
            assert find('importado / Health Connect') is None
            signout()
            signin(email_a, password)
            sources()
            tap('hc-origin', scroll=True)
            wait('importado / Health Connect')
            evidence('14-account-a-records-retained')
            # Install over the APK without clearing SecureStore, then prove authenticated UI.
            adb('shell', 'am', 'force-stop', APP)
            adb('install', '-r', str(ROOT / 'mobile/vytal-app/android/app/build/outputs/apk/debug/app-debug.apk'))
            adb('shell', 'am', 'start', '-W', '-a', 'android.intent.action.VIEW', '-d', url, APP)
            wait('dashboard-menu')
            evidence('15-apk-reinstall-retains-session')
        finally:
            (OUT / 'logcat.txt').write_text(adb('logcat', '-d'))
            for process in (metro, backend):
                if process is not None and process.poll() is None:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
            client.close()
            backend_log.close()
            metro_log.close()
    logs = (OUT / 'logcat.txt').read_text()
    assert not re.search(r"Cannot find native module|Unable to resolve module|FATAL EXCEPTION|ReactNativeJS.*(?:TypeError|ReferenceError)", logs), 'Runtime error in logcat'


try:
    run()
except BaseException as error:
    message = (type(error).__name__ + ': ' + str(error))[-3000:].replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
    print('::error::Android runtime smoke: ' + message, flush=True)
    print('Completed runtime checks: ' + ', '.join(checks), flush=True)
    try:
        evidence('FAILURE')
        visible = ' | '.join(n.get('text', '') for n in tree().iter('node') if n.get('text'))
        print('::error::Last Android UI: ' + visible[-3000:].replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A'), flush=True)
    except (subprocess.SubprocessError, AssertionError, ET.ParseError, OSError) as capture_error:
        print('Could not capture failure UI:', type(capture_error).__name__, flush=True)
    raise
finally:
    (OUT / 'checks.json').write_text(json.dumps({'checks_passed': checks,
        'data': 'synthetic emulator Health Connect, never real Garmin homologation'}, indent=2))
