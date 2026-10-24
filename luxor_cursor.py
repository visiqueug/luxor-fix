"""Hash-verified gameplay cursor fix (visique_cursor.dll) with ownership tracking.

The DLL is registered as GraphicsAPI_1 in luxor.ini and forwards to
gfx2d_dx8.dll; GraphicsAPI_2 points to gfx2d_dx8.dll as fallback. Only these
two lines are touched, because the game itself rewrites luxor.ini
(CurrentProfile, graphics settings).
"""
from pathlib import Path
import hashlib
import json
import sys

EXPECTED_DLL_SHA256 = "119bbf21f5f4220f006131641883a6de6d08f47d0db04cd14d8533b9f888d239"
ASSET = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "cursorfix" / "visique_cursor.dll"
DLL_NAME = "visique_cursor.dll"
INI_NAME = "luxor.ini"
INI_BACKUP_NAME = "luxor.ini.visique-backup"
LOG_NAME = "visique_cursor.log"
MANIFEST_NAME = ".visique_luxor_cursor.json"
MANIFEST_VERSION = 1
ORIGINAL_LINES = (b"GraphicsAPI_1=gfx2d_dx8.dll", b"GraphicsAPI_2=gfx2d_ogl.dll")
PATCHED_LINES = (b"GraphicsAPI_1=" + DLL_NAME.encode(), b"GraphicsAPI_2=gfx2d_dx8.dll")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def asset_ready():
    return ASSET.is_file() and digest(ASSET.read_bytes()) == EXPECTED_DLL_SHA256


def _lines_present(data, lines):
    """True if every line occurs exactly once as a complete ini line."""
    rows = [row.rstrip(b"\r") for row in data.split(b"\n")]
    return all(rows.count(line) == 1 for line in lines)


def _swap_lines(data, old, new):
    rows = data.split(b"\n")
    for i, row in enumerate(rows):
        stripped = row.rstrip(b"\r")
        if stripped in old:
            rows[i] = new[old.index(stripped)] + row[len(stripped):]
    return b"\n".join(rows)


def cursor_status(folder):
    folder = Path(folder)
    dll, ini = folder / DLL_NAME, folder / INI_NAME
    return (dll.is_file() and ini.is_file()
            and digest(dll.read_bytes()) == EXPECTED_DLL_SHA256
            and _lines_present(ini.read_bytes(), PATCHED_LINES))


def cursor_preflight(folder):
    """Raise if the cursor fix cannot be installed cleanly. Changes nothing."""
    folder = Path(folder)
    if not asset_ready():
        raise RuntimeError("visique_cursor.dll fehlt oder ist nicht verifiziert.")
    if cursor_status(folder):
        return
    if (folder / MANIFEST_NAME).exists():
        raise RuntimeError("Unvollstaendige Cursor-Fix-Installation; bitte manuell pruefen.")
    dll, ini = folder / DLL_NAME, folder / INI_NAME
    if dll.exists() and digest(dll.read_bytes()) != EXPECTED_DLL_SHA256:
        raise RuntimeError(f"Vorhandene Datei {DLL_NAME} unterscheidet sich. Keine Ueberschreibung.")
    if not ini.is_file() or not _lines_present(ini.read_bytes(), ORIGINAL_LINES):
        raise RuntimeError("luxor.ini enthaelt nicht die erwartete GraphicsAPI-Reihenfolge. Keine Aenderung.")


def install_cursor(folder):
    folder = Path(folder)
    cursor_preflight(folder)
    if cursor_status(folder):
        return False
    dll, ini, backup = folder / DLL_NAME, folder / INI_NAME, folder / INI_BACKUP_NAME
    original_ini = ini.read_bytes()
    created_dll = created_backup = False
    try:
        # Keep the oldest backup; it is never overwritten.
        if not backup.exists():
            with backup.open("xb") as handle:
                handle.write(original_ini)
            created_backup = True
        if not dll.exists():
            with dll.open("xb") as handle:
                handle.write(ASSET.read_bytes())
            created_dll = True
        ini.write_bytes(_swap_lines(original_ini, ORIGINAL_LINES, PATCHED_LINES))
        with (folder / MANIFEST_NAME).open("x", encoding="utf-8") as handle:
            json.dump({"version": MANIFEST_VERSION, "dll": EXPECTED_DLL_SHA256,
                       "created_dll": created_dll}, handle, indent=2)
            handle.write("\n")
    except Exception:
        ini.write_bytes(original_ini)
        if created_dll and dll.is_file() and digest(dll.read_bytes()) == EXPECTED_DLL_SHA256:
            dll.unlink()
        if created_backup and backup.is_file() and backup.read_bytes() == original_ini:
            backup.unlink()
        raise
    return True


def restore_cursor(folder):
    folder = Path(folder)
    manifest = folder / MANIFEST_NAME
    if not manifest.exists():
        print("Keine Cursor-Fix-Markierung: luxor.ini und visique_cursor.dll bleiben unveraendert.")
        return False
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if (not isinstance(data, dict) or data.get("version") != MANIFEST_VERSION
            or data.get("dll") != EXPECTED_DLL_SHA256):
        raise RuntimeError("Unbekannte Cursor-Fix-Markierung; keine Aenderung.")
    ini, dll = folder / INI_NAME, folder / DLL_NAME
    if ini.is_file() and _lines_present(ini.read_bytes(), PATCHED_LINES):
        # Only the two GraphicsAPI lines are reverted; game-written settings stay.
        ini.write_bytes(_swap_lines(ini.read_bytes(), PATCHED_LINES, ORIGINAL_LINES))
    else:
        print("Hinweis: GraphicsAPI-Zeilen in luxor.ini wurden veraendert und bleiben unangetastet.")
    if data.get("created_dll") and dll.is_file():
        if digest(dll.read_bytes()) == EXPECTED_DLL_SHA256:
            dll.unlink()
        else:
            print(f"Hinweis: {DLL_NAME} wurde veraendert und wird nicht geloescht.")
    (folder / LOG_NAME).unlink(missing_ok=True)
    manifest.unlink()
    print("Cursor-Fix entfernt. Sicherung bleibt als luxor.ini.visique-backup erhalten.")
    return True
