# VISIQUE Luxor Fix

**Bringing a childhood classic back to life.**

**Version:** 0.3.0
**Developed by Fabian ~ VISIQUE**

## Why I created this project

When I was a child, my mother used to play Luxor. Recently, I wanted to bring back those memories and make the game available for her again.

So I purchased the original game on Steam, installed it, and expected everything to work.

Unfortunately, it didn't.

The game simply wouldn't launch.

After some research, I discovered that I wasn't the only one experiencing this issue. Many players had been struggling to get the original Luxor running on modern versions of Windows.

There were community discussions, different workarounds, replacement files, and complicated instructions, but I wanted something simpler.

**Download the game. Apply one fix. Play.**

What started as a small personal project to get my mother's favorite game from my childhood running again turned into something I wanted to share with everyone facing the same problem.

That's how **VISIQUE Luxor Fix** was born.

## The problem

The original Steam version of **Luxor (2005)** has a long-standing compatibility issue with modern Windows operating systems.

Although the game is still available for purchase on Steam, many players experience the same frustrating behavior:

- Steam briefly shows the game as running.
- No game window appears, or the application closes immediately.
- The game returns to its normal Steam status without an explanation.
- Reinstalling or verifying the game files doesn't necessarily resolve the issue.

### What's causing it?

The original Luxor launcher relies on outdated executable protection and Windows API behavior that is no longer fully compatible with modern Windows versions. It starts the actual game process in a suspended state, decrypts it, and adjusts its memory protection before letting it run.

Our investigation identified two problematic `VirtualProtectEx` calls inside the original launcher. On current Windows versions they fail, and the launcher never hands over to the game.

These calls can prevent the game from launching correctly.

VISIQUE Luxor Fix repairs the affected executable while preserving the original game installation as much as possible. Once the game runs, it also takes care of two smaller issues on modern displays: black side bars in fullscreen and a Windows mouse cursor that stays visible on the playfield. See [What it fixes](#what-it-fixes).

## Our goal

We want to make playing the original Luxor as easy as it should have been from the beginning.

No complicated tutorials. No searching through years of forum posts. No manually replacing files from unknown sources.

**Just install Luxor through Steam, run VISIQUE Luxor Fix, and enjoy the game again.**

This project is an independent, community-focused compatibility fix. It is not affiliated with or endorsed by MumboJumbo, Accelerate Games, or Valve.

A legitimate copy of Luxor is required.

## What it fixes

| Problem | Fix |
|---|---|
| The game does not start on current Windows (launcher loops) | Patches two instructions in the game launcher `LUXOR.exe` |
| Fullscreen with black side bars (driver-dependent) | Installs the dgVoodoo 2 Direct3D 8 wrapper with a preconfigured `dgVoodoo.conf` |
| The Windows mouse cursor stays visible on the playfield while playing | Installs `visique_cursor.dll`, which hides the cursor during gameplay only (menus and pause keep it) |

## How to use

1. Install Luxor 1 through Steam and close the game.
2. Download `VISIQUE-Luxor-Fix.exe` and run it. Nothing else needs to be installed.
3. Select the Luxor installation folder if it is not detected automatically, e.g.
   `C:\Program Files (x86)\Steam\steamapps\common\Luxor`
4. Click **INSTALL COMPATIBILITY FIX**.
5. Start Luxor through Steam as usual.

To undo everything, run the tool again and click **Original wiederherstellen**.

The interface is in German.

## What is changed in the game folder

Installation only proceeds if every precondition is met; otherwise nothing is changed.

| File | Change |
|---|---|
| `LUXOR.exe` | Replaced by an unpacked copy with two patched instructions. The original is kept as `LUXOR.exe.backup`. |
| `D3D8.dll`, `dgVoodoo.conf` | Added (dgVoodoo 2.87.5). Existing different files are never overwritten. |
| `visique_cursor.dll` | Added. |
| `luxor.ini` | Two lines changed: `GraphicsAPI_1=visique_cursor.dll`, `GraphicsAPI_2=gfx2d_dx8.dll`. The original is kept as `luxor.ini.visique-backup`. |
| `.visique_luxor_fullscreen.json`, `.visique_luxor_cursor.json` | Markers recording which files the tool created. |
| `Steam.dll` | Copied from your own Steam installation only if it is missing. |

**Restore** puts back the original `LUXOR.exe`, reverts the two `luxor.ini` lines (settings written by the game itself are kept), and removes only the files the tool created that are still unchanged. Backups are kept. A copied `Steam.dll` is not removed.

## Supported version

Only the original Steam `LUXOR.exe` is supported:

- Original SHA-256: `334e7cc50d81500a2bf59d1592b063d1a2da43bb7f672a6ac4da60f0030747cc` (91,728 bytes)
- Patched SHA-256: `a14894451ca5f127a4df715bd3b00c8d0aa92379441468c202598a64e51f511a` (157,264 bytes)

Unknown versions are rejected without changes. The cursor fix additionally checks the game's `ui2.dll` build and stays inactive (graphics pass-through only) on any other build.

## Technical background

- **Launcher:** The UPX-packed launcher creates the game process suspended and changes its memory protection with `VirtualProtectEx`. On current Windows this call fails and the launcher loops. The patch replaces the two calls at RVA `0x17C0` and `0x17EC` (`FF 15 04 B1 41 00` → `83 C4 14 6A 01 58`) so they report success; the surrounding read/write operations are unchanged.
- **Graphics:** Without a wrapper the game switches the display to 800×600 in exclusive fullscreen, which shows black side bars depending on the graphics driver. dgVoodoo renders through Direct3D 11/12 and scales the image to the full screen without side bars, confines the mouse to the game window, and defers the mode switch until the game has initialized (`DeferredScreenModeSwitch = true`). The watermark is disabled.
- **Cursor:** Luxor 1 never hides the Windows cursor itself and contains no custom cursor graphic. `visique_cursor.dll` is loaded by the game as its graphics API, forwards to the original `gfx2d_dx8.dll` unchanged, and hides the cursor while the in-game dialog `Game` is on top. It does not modify the game's window procedure. Details: [`cursorfix/README.md`](cursorfix/README.md).

## Limitations

- Tested on one Windows 11 24H2 system with AMD graphics. An earlier version containing only the launcher patch was reported to start on Windows 10. Other GPUs (NVIDIA, Intel), Windows 10 with the full fix, and multi-monitor setups have not yet been verified.
- **Steam "Verify integrity of game files"** may restore the original `LUXOR.exe` or `luxor.ini`. Run the tool again afterwards.
- If the game is installed under `C:\Program Files (x86)`, Windows may require running the tool as administrator to write to the game folder.
- Unsigned community tools may trigger Windows SmartScreen or antivirus warnings. Verify the published checksum.
- Use at your own risk.

## Building from source

Requirements: Windows, Python 3.13, PyInstaller 6.x, and these files:

| Path | Content | Source | Expected SHA-256 |
|---|---|---|---|
| `tools/upx.exe` | UPX 5.2.1 | Not in the repository. `upx-5.2.1-win64/upx.exe` from `upx-5.2.1-win64.zip`: https://github.com/upx/upx/releases/tag/v5.2.1 | `d20ebe0b7b22b6be968c8c34be61f94ddea12cb11462e2cec27f548ef9574df8` |
| `dgvoodoo/D3D8.dll` | dgVoodoo 2.87.5 Direct3D 8 | Not in the repository. `MS/x86/D3D8.dll` from `dgVoodoo2_87_5.zip`: https://github.com/dege-diosg/dgVoodoo2/releases/tag/v2.87.5 | `d03e2562178db1fcf3493fc0a0b23a465e35c55d73adb3ec095be866cd662704` |
| `dgvoodoo/dgVoodoo.conf` | Project configuration | Repository | `aa2fe07e8180d9ff77fd1be274410e45be68fbdac3316cc08375d3210029534d` |
| `cursorfix/visique_cursor.dll` | Built from `cursorfix/visique_cursor.c` | Repository | `119bbf21f5f4220f006131641883a6de6d08f47d0db04cd14d8533b9f888d239` |

Run `build_windows.bat` or:

```powershell
py -m PyInstaller --clean --noconfirm VISIQUE-Luxor-Fix.spec
```

Output: `dist\VISIQUE-Luxor-Fix.exe`. The bundled binaries are excluded from UPX compression in the spec file, because the tool verifies their hashes at runtime.

The tool can also be used without the GUI:

```powershell
py luxor_fix.py --folder "C:\Program Files (x86)\Steam\steamapps\common\Luxor"
py luxor_fix.py --folder "C:\Program Files (x86)\Steam\steamapps\common\Luxor" --restore
```

## Third-party components

VISIQUE Luxor Fix includes an unmodified Direct3D 8 compatibility component from **dgVoodoo2**, developed by Dege.

- Component: `D3D8.dll`
- Version: dgVoodoo2 2.87.5
- Copyright © 2013–2026 Dege
- Official website: https://dege.freeweb.hu/

dgVoodoo2 is an independent third-party project and is not developed by or affiliated with VISIQUE.

The component is distributed in accordance with the redistribution terms published by its author.

## Licensing

The project's own source code is licensed under the MIT License (see [`LICENSE`](LICENSE)). Bundled third-party components (UPX, dgVoodoo 2) are subject to their own terms; see [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

No Luxor game files or Steam files are distributed with this project.
