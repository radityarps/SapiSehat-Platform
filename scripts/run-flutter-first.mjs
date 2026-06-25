#!/usr/bin/env node
/**
 * Run Flutter against the first online adb device from repository root.
 * Override with ANDROID_SERIAL when several devices are connected.
 */
import { spawnSync } from "node:child_process";

function adb(args) {
  return spawnSync("adb", args, { encoding: "utf8" });
}

function firstOnlineDevice() {
  if (process.env.ANDROID_SERIAL) return process.env.ANDROID_SERIAL;
  const res = adb(["devices"]);
  if (res.status !== 0) {
    process.stderr.write(res.stderr || "Failed to run `adb devices`\n");
    process.exit(res.status ?? 1);
  }
  const device = res.stdout
    .split(/\r?\n/)
    .slice(1)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [serial, state] = line.split(/\s+/);
      return { serial, state };
    })
    .find((entry) => entry.state === "device");

  if (!device) {
    process.stderr.write("No online adb devices found. Run `adb connect <ip:port>` or plug in a device.\n");
    process.exit(1);
  }
  return device.serial;
}

const target = firstOnlineDevice();
const args = process.argv.slice(2);
process.stderr.write(`[run-flutter-first] target device: ${target}\n`);
const result = spawnSync("flutter", ["-d", target, ...args], {
  cwd: "apps/mobile",
  stdio: "inherit",
  shell: process.platform === "win32",
});
process.exit(result.status ?? 1);
