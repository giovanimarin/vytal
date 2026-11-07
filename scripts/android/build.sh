#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
cd "$root/mobile/vytal-app"
export NODE_ENV=development EXPO_NO_TELEMETRY=1
export EXPO_PUBLIC_API_URL=${EXPO_PUBLIC_API_URL:-http://10.0.2.2:8000/api/v1}
npm ci
npx expo install --check
node ../../scripts/android/check-native.cjs
npx expo prebuild --clean --platform android --no-install
node tests/health-connect-manifest.cjs
# Emulator-only fixture stays a separate package and APK.
printf '\ninclude(":healthFixture")\nproject(":healthFixture").projectDir = new File(rootDir, "../../../tests/android-fixture")\n' >> android/settings.gradle
cd android
./gradlew clean :app:assembleDebug :healthFixture:assembleDebug -PreactNativeArchitectures=arm64-v8a,x86_64 --no-daemon --max-workers=2
python "$root/scripts/android/check-apk.py" app/build/outputs/apk/debug/app-debug.apk
