# Third-Party Notices

VISIQUE Luxor Fix bundles the following third-party components. Their licenses are separate from, and not replaced by, the MIT License covering this project's own source code.

## UPX – Ultimate Packer for eXecutables

- **Bundled as:** `tools/upx.exe` (version 5.2.1), used only to unpack the game launcher on the user's machine.
- **Project:** https://upx.github.io/
- **License:** GNU General Public License, version 2 or later, with special exceptions.
- **License texts:** `licenses/UPX/COPYING`, `licenses/UPX/LICENSE`
- **Corresponding source code:** https://github.com/upx/upx/releases/tag/v5.2.1

## dgVoodoo 2

- **Bundled as:** `dgvoodoo/D3D8.dll` (dgVoodoo 2.87.5 – Direct3D8, file version 4.8.2.134), copied into the game folder together with the project's own `dgVoodoo.conf`.
- **Copyright:** © 2013–2026 Dege
- **Project:** https://dege.freeweb.hu/
- **Redistribution terms** (official dgVoodoo 2.87.5 documentation, section "Redistribution rights", https://dege.freeweb.hu/dgVoodoo2/ReadmeGeneral/):
  > You can freely ship your game or game mod with unmodified individual dgVoodoo components (files) included.

  > You cannot bundle dgVoodoo inside launchers or frameworks, for general use across multiple applications

- **How this project complies:**
  - `D3D8.dll` is shipped byte-identical to `MS/x86/D3D8.dll` from the official release package `dgVoodoo2_87_5.zip` (https://github.com/dege-diosg/dgVoodoo2/releases/tag/v2.87.5, package SHA-256 `5ffde6927f7355ca3fdd5d785b581256a8e6539fa13e395a891ade6ba1040850`). DLL SHA-256: `d03e2562178db1fcf3493fc0a0b23a465e35c55d73adb3ec095be866cd662704`. The tool verifies this hash before copying it.
  - The DLL is installed only into a verified Luxor 1 installation. VISIQUE Luxor Fix is a game-specific patch, not a general-purpose launcher or framework.
  - Only the configuration file `dgVoodoo.conf` is project-specific; it is not a dgVoodoo component.
- **Note:** This assessment covers free, non-commercial distribution of a Luxor 1-specific patch. Before any commercial use, monetisation, or extension to other games, obtain written confirmation from the author.

## Build tools (not distributed)

- **Zig 0.13.0** (https://ziglang.org/, MIT License) is used to compile `cursorfix/visique_cursor.dll`. The resulting DLL is linked against the Windows Universal C Runtime that ships with Windows; no Zig components are redistributed.
- **PyInstaller** (https://pyinstaller.org/) is used to build the Windows executable. Its bootloader is distributed under the GPL with an exception that permits use in non-GPL applications.
- **Python** (https://www.python.org/) is embedded by PyInstaller under the Python Software Foundation License.

## Game and Steam files

VISIQUE Luxor Fix is an independent community project. No Luxor game executables, game assets, or Steam files are distributed with it. Users must own and install Luxor 1 through Steam.

## Credits

Developed by Fabian ~ VISIQUE.
