# Flutter demo setup

The `lib/` source is complete. Generate platform folders once on your machine:

```bash
cd flutter_app
flutter create . --project-name gentle_activity_demo
flutter pub get
```

Then add pedometer permissions:

**Android** — `android/app/src/main/AndroidManifest.xml`:
```xml
<uses-permission android:name="android.permission.ACTIVITY_RECOGNITION"/>
```

**iOS** — `ios/Runner/Info.plist`:
```xml
<key>NSMotionUsageDescription</key>
<string>Counts steps for general wellness tracking while the app is open.</string>
```

## Run

```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

Use your machine LAN IP for physical devices.
