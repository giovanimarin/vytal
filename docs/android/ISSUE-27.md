# Issue #27 — Android runtime / Expo SDK 54

Branch `codex/issue-27-android-runtime` is stacked on #26 (`codex/windows-android-launcher`), which depends on #25 (`codex/android-health-connect`). No merge, deployment, provisioning or changes to existing user data.

## Correction

The failing APK used SDK 54 with SDK 52/53-era WebBrowser 14, Linking 7, SecureStore 14, Router 5 and Babel preset 13. Dependencies and the npm lockfile now use the SDK 54 versions (SDK 54.0.37, dev-client 6.0.21, WebBrowser 15, Linking 8, SecureStore 15, Router 6, Babel preset 54). Router's Constants/Font peers are explicit. Google Fit and Health Connect remain enabled.

`expo install --check`, `expo-doctor`, native autolinking resolution and inspection of the compiled DEX/signature/ARM64+x86_64 ABIs now gate the Android workflow. Unit tests and an exported JS bundle alone do not certify this fix.

## Reproduce the build and smoke

Ubuntu, Node 22, Python 3.12, JDK 17, Android SDK 36/build-tools 36, and a running Android 14/API 34 Google APIs emulator with `adb` available:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r backend/requirements-prod.txt
bash scripts/android/build.sh && .venv/bin/python scripts/android/smoke.py
```

The build uses a clean generated Android directory and builds a universal debug dev-client APK for ARM64 phones and x86_64 emulators. Set `ANDROID_HOME` to the SDK; the build script adds build-tools to PATH. The separate `org.vytal.smokefixture` APK writes 123 synthetic steps into the emulator's actual Health Connect service; it is never included in the Vytal APK and never impersonates Garmin.

The runtime smoke boots the actual APK with Metro and a real FastAPI/SQLite server bound to `0.0.0.0`, accessed at `10.0.2.2` by the emulator. It drives registration, login, dashboard, Google Fit route (native WebBrowser import), data sources, native Health Connect permission denial, granted empty reads, synthetic import, replay/deduplication, network failure, backend restart and account A/B isolation. It restarts the APK without clearing app storage. Screenshots, UI trees, logcat and the list of completed checks are uploaded even on failure. The backend uses a new temporary SQLite database and random test-only keys, never an existing developer database.

## Install on Ubuntu + Samsung

Use the successful **Android APK runtime smoke** run for this branch, artifact **android-health-connect-debug-apk**. The artifact contains `app-debug.apk`. Install over the existing development APK with `adb install -r app-debug.apk`; do not uninstall, clear app data, delete SQLite, or rotate local keys. Android rejects an upgrade with a different signing certificate; do not work around that by uninstalling. The SDK/template debug signing identity is unchanged.

The single-command launcher below downloads the artifact, installs with `-r`, starts the local backend and Metro, and opens the dev-client. Use your PC's private LAN IPv4 and the successful run ID:

```bash
bash scripts/android/run-local.sh 192.168.1.10 RUN_ID
```

This requires `gh` authenticated for artifact download, `adb`, Node 22 and Python 3.12; both PC and phone must share a trusted Wi-Fi network. No cloud backend, EAS login, administrator firewall changes or data resets are required. Existing backend `.env` and SQLite configuration are reused; ambiguity fails with an explicit path request. Set `VYTAL_DATABASE_PATH` to select an existing database when needed.

Real Samsung permissions, historical Garmin-origin data, and Garmin homologation remain physical-device checks. Synthetic emulator results do not certify those integrations. Runtime and CI outcomes are recorded below after execution.
