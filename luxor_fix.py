#!/usr/bin/env python3
"""Community compatibility patcher for the Steam release of Luxor 1.

No copyrighted game files are included. Requires an existing UPX executable.
"""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile

from luxor_fullscreen import assets_ready, fullscreen_status, install_fullscreen, restore_fullscreen
from luxor_cursor import (asset_ready as cursor_asset_ready, cursor_preflight, cursor_status,
                          install_cursor, restore_cursor)

EXPECTED_PACKED_SIZE = 91728
EXPECTED_ORIGINAL_SHA256 = "334e7cc50d81500a2bf59d1592b063d1a2da43bb7f672a6ac4da60f0030747cc"
EXPECTED_PATCHED_SHA256 = "a14894451ca5f127a4df715bd3b00c8d0aa92379441468c202598a64e51f511a"
EXPECTED_UNPACKED_SIZE = 157264
PATCHES = {0x17C0: (bytes.fromhex('FF 15 04 B1 41 00'), bytes.fromhex('83 C4 14 6A 01 58')),
           0x17EC: (bytes.fromhex('FF 15 04 B1 41 00'), bytes.fromhex('83 C4 14 6A 01 58'))}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def section_offset(data, rva):
    if data[:2] != b'MZ':
        raise ValueError('Keine gueltige Windows-EXE (MZ fehlt).')
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    if data[pe:pe+4] != b'PE\0\0':
        raise ValueError('Keine gueltige PE-Datei.')
    count = struct.unpack_from('<H', data, pe+6)[0]
    optsize = struct.unpack_from('<H', data, pe+20)[0]
    imagebase = struct.unpack_from('<I', data, pe+24+28)[0]
    if imagebase != 0x400000:
        raise ValueError('Unerwartete Image Base; diese Version wird nicht unterstuetzt.')
    for i in range(count):
        s = pe + 24 + optsize + 40*i
        vsize, va, rawsize, raw = struct.unpack_from('<IIII', data, s+8)
        if va <= rva < va + min(vsize, rawsize):
            off = raw + rva - va
            if off+6 > len(data):
                break
            return off
    raise ValueError(f'RVA 0x{rva:X} nicht in Dateidaten gefunden.')


# SHA256 of the verified UPX 5.2.1 executable shipped with this project.
EXPECTED_UPX_SHA256 = "d20ebe0b7b22b6be968c8c34be61f94ddea12cb11462e2cec27f548ef9574df8"


def find_upx(explicit=None):
    """Use only the bundled, hash-verified UPX executable."""
    if explicit is not None:
        raise ValueError('Externe UPX-Programme sind aus Sicherheitsgruenden nicht erlaubt.')
    bundled_dir = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    bundled_upx = bundled_dir / "tools" / "upx.exe"
    if not bundled_upx.is_file():
        raise FileNotFoundError('Die mitgelieferte tools/upx.exe fehlt. Abbruch.')
    if sha256(bundled_upx.read_bytes()) != EXPECTED_UPX_SHA256:
        raise ValueError('UPX-Integritaetspruefung fehlgeschlagen (SHA256). Abbruch.')
    return str(bundled_upx)


def game_running():
    if os.name != 'nt':
        return False
    try:
        r = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], capture_output=True, text=True, timeout=10)
        names = {'luxor.exe', 'luxor_patched.exe', 'game.dmg'}
        return any(line.strip().lower().startswith('"'+name+'"') for line in r.stdout.splitlines() for name in names)
    except Exception:
        return False


def install(folder, upx_arg, steam_dll):
    exe = folder / 'LUXOR.exe'
    backup = folder / 'LUXOR.exe.backup'
    dll = folder / 'Steam.dll'
    if not exe.is_file():
        raise FileNotFoundError(f'LUXOR.exe fehlt in {folder}')
    if game_running():
        raise RuntimeError('Luxor scheint noch zu laufen. Bitte Spiel und Debugger zuerst schliessen.')
    original = exe.read_bytes()
    if backup.exists() and sha256(backup.read_bytes()) != EXPECTED_ORIGINAL_SHA256:
        raise RuntimeError('Vorhandenes Backup ist unbekannt. Es wird nichts veraendert.')
    if sha256(original) == EXPECTED_PATCHED_SHA256:
        if fullscreen_status(folder) and cursor_status(folder):
            print('EXE, Vollbild-Fix und Cursor-Fix sind bereits installiert.')
            return
        if not assets_ready():
            raise RuntimeError('EXE ist bereits gepatcht; dgVoodoo-Paket fehlt oder ist ungueltig.')
        if not cursor_asset_ready():
            raise RuntimeError('EXE ist bereits gepatcht; visique_cursor.dll fehlt oder ist ungueltig.')
        cursor_preflight(folder)
        install_fullscreen(folder)
        install_cursor(folder)
        print('ERFOLG: Vollbild- und Cursor-Fix nachinstalliert. EXE blieb unveraendert.')
        return
    if sha256(original) != EXPECTED_ORIGINAL_SHA256:
        raise ValueError('Nicht unterstuetzte LUXOR.exe (SHA256 stimmt nicht). Abbruch.')
    if len(original) != EXPECTED_PACKED_SIZE:
        raise ValueError(f'Nicht unterstuetzte Originaldatei ({len(original)} Bytes statt {EXPECTED_PACKED_SIZE}). Abbruch.')
    if not assets_ready():
        raise RuntimeError('dgVoodoo-Paket fehlt oder ist ungueltig; keine Aenderungen vorgenommen.')
    # Conflict check before changing the executable.
    for source, dest in zip((__import__('luxor_fullscreen').asset_paths()), (folder / 'D3D8.dll', folder / 'dgVoodoo.conf')):
        if dest.exists() and sha256(source.read_bytes()) != sha256(dest.read_bytes()):
            raise RuntimeError(f'Konflikt bei {dest.name}: Datei existiert bereits und wird nicht ueberschrieben.')
    if not cursor_asset_ready():
        raise RuntimeError('visique_cursor.dll fehlt oder ist ungueltig; keine Aenderungen vorgenommen.')
    cursor_preflight(folder)
    upx = find_upx(upx_arg)
    with tempfile.TemporaryDirectory(prefix='luxorfix_') as tmp:
        working = Path(tmp) / 'LUXOR.exe'
        working.write_bytes(original)
        result = subprocess.run([upx, '-d', str(working)], capture_output=True, text=True, timeout=90)
        if result.returncode:
            raise RuntimeError('UPX-Entpacken fehlgeschlagen:\n'+result.stdout+'\n'+result.stderr)
        data = bytearray(working.read_bytes())
    if len(data) != EXPECTED_UNPACKED_SIZE:
        raise ValueError(f'Entpackte EXE hat unerwartete Groesse: {len(data)} Bytes. Abbruch.')
    offsets = {}
    for rva, (expected, replacement) in PATCHES.items():
        offset = section_offset(data, rva)
        if data[offset:offset+len(expected)] != expected:
            raise ValueError(f'Unerwartete Bytes bei RVA 0x{rva:X}. Abbruch ohne Dateiaenderung.')
        offsets[rva] = offset
    for rva, (expected, replacement) in PATCHES.items():
        offset = offsets[rva]
        data[offset:offset+len(replacement)] = replacement
    # Preflight Steam.dll, if absent; never download or overwrite it.
    dll_source = None
    if not dll.exists():
        candidates = ([Path(steam_dll)] if steam_dll else [])
        candidates += [folder.parents[2] / 'Steam.dll'] if len(folder.parents) > 2 else []
        # Typical folder: Steam/steamapps/common/Luxor -> Steam is parents[2].
        dll_source = next((p for p in candidates if p.is_file()), None)
        if dll_source is None:
            raise FileNotFoundError('Steam.dll fehlt im Spielordner. Gib --steam-dll "C:\\...\\Steam.dll" an.')
    print(f'Original SHA256: {sha256(original)}')
    print(f'Gepatcht SHA256: {sha256(data)}')
    print('Patchstellen:', ', '.join(f'RVA 0x{rva:X} -> Datei 0x{off:X}' for rva, off in offsets.items()))
    if not backup.exists():
        # Backup nicht ueberschreiben, falls es bereits von einem frueheren Test stammt.
        with backup.open('xb') as handle:
            handle.write(original)
    try:
        # os.replace is atomic within the same filesystem; stage next to the destination.
        staged = folder / 'LUXOR.exe.luxorfix.tmp'
        try:
            staged.write_bytes(data)
            os.replace(staged, exe)
        finally:
            staged.unlink(missing_ok=True)
        if dll_source:
            shutil.copy2(dll_source, dll)
            print(f'Steam.dll kopiert aus {dll_source}')
        install_fullscreen(folder)
        install_cursor(folder)
    except Exception:
        # Recover original if anything failed after creating the backup.
        exe.write_bytes(original)
        raise
    print('ERFOLG: LUXOR.exe gepatcht. Original gesichert als LUXOR.exe.backup.')
    print('Zum Rueckgaengigmachen: py luxor_fix.py --folder "..." --restore')


def restore(folder):
    exe = folder / 'LUXOR.exe'
    backup = folder / 'LUXOR.exe.backup'
    if game_running():
        raise RuntimeError('Luxor zuerst schliessen.')
    if not backup.is_file():
        raise FileNotFoundError('Keine LUXOR.exe.backup gefunden.')
    original = backup.read_bytes()
    if sha256(original) != EXPECTED_ORIGINAL_SHA256:
        raise ValueError('Backup entspricht nicht der erwarteten Originalversion. Abbruch.')
    if exe.exists() and sha256(exe.read_bytes()) not in (EXPECTED_ORIGINAL_SHA256, EXPECTED_PATCHED_SHA256):
        raise ValueError('Aktuelle LUXOR.exe ist unbekannt; Wiederherstellung verweigert.')
    staged = folder / 'LUXOR.exe.luxorfix.tmp'
    try:
        staged.write_bytes(original)
        os.replace(staged, exe)
    finally:
        staged.unlink(missing_ok=True)
    restore_cursor(folder)
    restore_fullscreen(folder)
    print('Original LUXOR.exe wiederhergestellt. Backup bleibt erhalten.')
    print('Eine ggf. kopierte Steam.dll wird aus Sicherheitsgruenden nicht automatisch geloescht.')


def main():
    p = argparse.ArgumentParser(description='Luxor 1 Windows 11 Compatibility Fix (Steam)')
    p.add_argument('--folder', required=True, type=Path, help='Luxor-Spielordner')
    p.add_argument('--steam-dll', help='Pfad zur vorhandenen Steam.dll')
    p.add_argument('--restore', action='store_true', help='Original aus Backup wiederherstellen')
    args = p.parse_args()
    try:
        if args.restore:
            restore(args.folder)
        else:
            install(args.folder, None, args.steam_dll)
    except Exception as exc:
        print('FEHLER:', exc, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
