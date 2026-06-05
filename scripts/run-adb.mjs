#!/usr/bin/env node
/**
 * Cross-platform adb wrapper that always targets a single device.
 *
 * Why: with wireless debugging, the same phone often appears twice in
 * `adb devices` (a manual IP:port connection + an mDNS `adb-...._tcp` entry).
 * Bare `adb` commands then fail with "more than one device/emulator".
 *
 * Device selection order:
 *   1. ANDROID_SERIAL environment variable (explicit override)
 *   2. The single online device, if only one exists
 *   3. If multiple online devices share the same physical serial
 *      (ro.serialno), they are the same phone — pick the directly
 *      addressable one (IP:port or USB serial) over the mDNS name.
 *   4. Otherwise, error and list the candidates so the user can set
 *      ANDROID_SERIAL.
 *
 * Usage: node scripts/run-adb.mjs <adb args...>
 *   e.g. node scripts/run-adb.mjs install -r path/to/app.apk
 */

import { spawnSync } from "node:child_process";

function adb(args) {
  return spawnSync("adb", args, { encoding: "utf8" });
}

function listOnlineDevices() {
  const res = adb(["devices"]);
  if (res.status !== 0) {
    process.stderr.write(res.stderr || "Failed to run `adb devices`\n");
    process.exit(res.status ?? 1);
  }
  return res.stdout
    .split(/\r?\n/)
    .slice(1) // drop "List of devices attached"
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [serial, state] = line.split(/\s+/);
      return { serial, state };
    })
    .filter((d) => d.state === "device");
}

function physicalSerial(serial) {
  const res = adb(["-s", serial, "shell", "getprop", "ro.serialno"]);
  return res.status === 0 ? res.stdout.trim() : null;
}

function isDirectlyAddressable(serial) {
  // IP:port (192.168.x.x:port) or a plain USB serial; mDNS names start with "adb-".
  return !serial.startsWith("adb-");
}

function selectTarget() {
  if (process.env.ANDROID_SERIAL) {
    return process.env.ANDROID_SERIAL;
  }

  const devices = listOnlineDevices();

  if (devices.length === 0) {
    process.stderr.write(
      "No online adb devices found. Connect a device or run `adb connect <ip:port>`.\n",
    );
    process.exit(1);
  }

  if (devices.length === 1) {
    return devices[0].serial;
  }

  // Multiple entries: check whether they are the same physical phone.
  const byPhysical = new Map();
  for (const d of devices) {
    const phys = physicalSerial(d.serial) || d.serial;
    if (!byPhysical.has(phys)) byPhysical.set(phys, []);
    byPhysical.get(phys).push(d.serial);
  }

  if (byPhysical.size === 1) {
    // Same device surfaced multiple times — pick the addressable alias.
    const aliases = [...byPhysical.values()][0];
    const addressable = aliases.find(isDirectlyAddressable) || aliases[0];
    return addressable;
  }

  // Genuinely different devices — require explicit choice.
  process.stderr.write(
    "Multiple distinct devices are connected. Set ANDROID_SERIAL to choose one:\n",
  );
  for (const d of devices) {
    process.stderr.write(`  - ${d.serial}\n`);
  }
  process.stderr.write("\nExample (Git Bash):  export ANDROID_SERIAL=<serial>\n");
  process.stderr.write("Example (PowerShell): $env:ANDROID_SERIAL='<serial>'\n");
  process.exit(1);
}

const target = selectTarget();
const passthrough = process.argv.slice(2);
process.stderr.write(`[run-adb] target device: ${target}\n`);

const result = spawnSync("adb", ["-s", target, ...passthrough], {
  stdio: "inherit",
});
process.exit(result.status ?? 1);
