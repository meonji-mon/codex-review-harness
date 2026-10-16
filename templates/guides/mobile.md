# Mobile and simulator usage

Use for mobile development, debugging, UI checks, tests, or release verification. Boundaries: [section 3](../AGENTS.md#3-implementation-and-verification).

## Device selection

- iOS default: **iPhone 17 Pro Simulator**.
- Android default: `Medium_Phone_API_35` (1080×2400, 420dpi).
- Extra checks for large screens, long translations, or spacious layouts: `Pixel_9_Pro_API_35`.
- Latest API compatibility: `DunkLoop_API_36`.
- `flutter_emulator` profiles are not the default. Apply central iPad/tablet conditions.

## Execution

1. Reuse running simulators/project profiles that meet the designated conditions.
2. Prefer available XcodeBuildMCP for iOS builds/operation; otherwise use a supported local alternative.
3. If SimSlim is installed, establish initial state with `simslim list`. Use `status`, `on`, `boot`, and profile verification only as needed.
4. Verify required services are active for push, StoreKit, and universal-link tests.
5. Compare final to initial state; restore SimSlim with `off` if it was initially off.

## Standalone Android emulator

Apply the [central Android tool rule](../AGENTS.md#product-and-ui).

1. Locate the installed SDK through its environment settings or known installation path. Check available emulator and adb tools.
2. Reuse a suitable running device; otherwise list existing AVDs and start the selected one as a standalone window.
3. Build, install, run, inspect logs, and capture through the project's CLI and adb as needed. Select the intended device/serial explicitly.
4. If SDK tools or the required AVD are missing, report the prerequisite instead of opening Studio by default. Keep the central approval and device-data preservation boundaries.

Example for the installed SDK and existing default AVD:

```sh
${USER_HOME}/Library/Android/sdk/emulator/emulator -list-avds
${USER_HOME}/Library/Android/sdk/emulator/emulator -avd Medium_Phone_API_35
```

For visible UI checks, use the emulator's own window rather than Studio's embedded/hidden-window launch options. Command reference: [Android Emulator CLI](https://developer.android.com/studio/run/emulator-commandline).
