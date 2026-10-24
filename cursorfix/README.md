# visique_cursor.dll

Hides the Windows cursor during Luxor 1 gameplay. Loaded by `core.dll!LoadGraphicsAPI`
through `luxor.ini` (`GraphicsAPI_1=visique_cursor.dll`) and forwards
`CreateGfxSubsystem` to `gfx2d_dx8.dll` unchanged.

## How it works

- A thread timer (100 ms) on the game's main thread reads the top ui2 dialog:
  `g_ui` → `[ui+0x2C]` → `[node]` → name at `+0x1C`. Name `Game` means gameplay.
- A thread-local `WH_CALLWNDPROCRET` hook calls `SetCursor(NULL)` after
  `WM_SETCURSOR` has been handled, while in gameplay.
- The window procedure chain (game → dgVoodoo) is never modified. An earlier
  subclassing prototype recursed with dgVoodoo's own subclass and crashed
  (`0xC000041D`).
- Offsets are only valid for `ui2.dll` timestamp `0x42CB840F` / image size `0x2E000`
  (Luxor 1.0.5.34, Steam). Any other build: forwarding only, cursor untouched.

## Build

Requires Zig 0.13.0 (portable, `zig-windows-x86_64-0.13.0.zip`,
SHA256 `d859994725ef9402381e557c60bb57497215682e355204d754ee3df75ee3c158`).

```
zig cc -target x86-windows-gnu -O2 -shared -s -Wall ^
    -o visique_cursor.dll visique_cursor.c visique_cursor.def -luser32
```

The build is deterministic for the same output path, but the path is embedded,
so a build in another directory yields a different SHA256. The patcher pins the
committed `visique_cursor.dll`; after a rebuild, update `EXPECTED_DLL_SHA256` in
`luxor_cursor.py` and the hash in `README_TEST.txt`.
