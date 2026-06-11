# Wireless Debugging (WiFi ADB)

Connect your Android device over WiFi to build, install, and run the app — no Android Studio required.

## Prerequisites

- Android 11+ on your device (for native wireless debugging)
- Device and PC on the **same WiFi network**
- `adb` available in your terminal PATH
  - Default location: `C:\Users\<you>\AppData\Local\Android\Sdk\platform-tools\`
  - Add this folder to your system PATH if `adb` is not recognized

## Setup

### 1. Enable Wireless Debugging

On your Android device:

1. Go to **Settings → Developer Options**
2. Enable **Wireless debugging**
3. Confirm the prompt

> If you don't see Developer Options, go to **Settings → About Phone** and tap **Build Number** 7 times.

### 2. Pair (one-time per device)

On your phone, tap **"Pair device with pairing code"**. It will display:

- An IP address and port (e.g., `192.168.18.5:37123`)
- A 6-digit pairing code

In your terminal:

```bash
adb pair 192.168.18.5:37123
```

Enter the 6-digit code when prompted. You should see:

```
Successfully paired to 192.168.18.5:37123
```

> This step is one-time. You don't need to pair again unless you reset wireless debugging.

### 3. Connect

After pairing, look at the main **Wireless debugging** screen on your phone. It shows an IP:port under "IP address & Port" (different from the pairing port).

```bash
adb connect 192.168.18.5:41567
```

Expected output:

```
connected to 192.168.18.5:41567
```

### 4. Verify

```bash
adb devices
```

You should see your device listed:

```
List of devices attached
192.168.18.5:41567    device
```

## Running the App

Once connected, run from the repository root. The scripts automatically target the first online ADB device. Set `ANDROID_SERIAL` only if you want to override the chosen device.

```bash
# Hot-run Flutter on the first connected device
pnpm mobile:run

# Build debug APK, then install it on the first connected device
pnpm mobile:deploy

# Restart the installed Flutter app without rebuilding
pnpm mobile:restart

# View app/Flutter logs
pnpm mobile:log

# Flutter checks
pnpm mobile:test
```

`pnpm mobile:run` uses `flutter -d <first-device> run` through `scripts/run-flutter-first.mjs`.
`pnpm mobile:deploy`, `pnpm mobile:restart`, and `pnpm mobile:log` use `scripts/run-adb.mjs`, so they work over WiFi and USB.

If several devices are connected and you need a specific one:

```bash
# Git Bash
export ANDROID_SERIAL=<device-id>
pnpm mobile:run

# PowerShell
$env:ANDROID_SERIAL='<device-id>'
pnpm mobile:run
```

## Reconnecting

The WiFi connection drops when:

- Your phone disconnects from WiFi
- Your phone goes to sleep (sometimes)
- You restart `adb server`

To reconnect, just run `adb connect` again with the same IP:port:

```bash
adb connect 192.168.18.5:41567
```

No re-pairing needed.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `adb: command not found` | Add `platform-tools` to your system PATH |
| `cannot connect to ...` | Ensure phone and PC are on the same WiFi network |
| `connection refused` | Re-check the port on the Wireless Debugging screen (it can change) |
| `device offline` | Run `adb disconnect` then `adb connect` again |
| `pairing code expired` | Tap "Pair device with pairing code" again for a fresh code |
| Connection drops frequently | Disable battery optimization for "Wireless debugging" or keep the screen on |

## Legacy Method (Android 10 and below)

For devices without native wireless debugging, you can switch from USB to WiFi:

```bash
# Connect via USB first, then:
adb tcpip 5555
adb connect <phone-ip>:5555

# Disconnect USB cable — adb now works over WiFi
```

To find your phone's IP: **Settings → WiFi → tap your network → IP address**.

To revert back to USB mode:

```bash
adb usb
```
