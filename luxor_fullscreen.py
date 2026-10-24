"""Hash-verified dgVoodoo installation with conservative ownership tracking."""
from pathlib import Path
import hashlib
import json
import os
import sys

EXPECTED_D3D8_SHA256 = "d03e2562178db1fcf3493fc0a0b23a465e35c55d73adb3ec095be866cd662704"
ASSET_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "dgvoodoo"
MANIFEST_NAME = ".visique_luxor_fullscreen.json"
MANIFEST_VERSION = 1
FILES = ("D3D8.dll", "dgVoodoo.conf")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def asset_paths():
    return ASSET_DIR / FILES[0], ASSET_DIR / FILES[1]


def assets_ready():
    dll, conf = asset_paths()
    return (dll.is_file() and conf.is_file()
            and digest(dll) == EXPECTED_D3D8_SHA256
            and "DeferredScreenModeSwitch            = true" in conf.read_text(encoding="utf-8-sig", errors="replace"))


def fullscreen_status(folder):
    folder = Path(folder)
    dll, conf = folder / FILES[0], folder / FILES[1]
    source_dll, source_conf = asset_paths()
    return (dll.is_file() and conf.is_file() and source_conf.is_file()
            and digest(dll) == EXPECTED_D3D8_SHA256
            and digest(conf) == digest(source_conf))


def _manifest_path(folder):
    return Path(folder) / MANIFEST_NAME


def _load_manifest(folder):
    path = _manifest_path(folder)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(data, dict) or data.get("version") != MANIFEST_VERSION
            or not isinstance(data.get("created"), dict)
            or set(data["created"]) - set(FILES)
            or any(not isinstance(h, str) or len(h) != 64 or
                   any(c not in "0123456789abcdef" for c in h)
                   for h in data["created"].values())):
        raise RuntimeError("Unbekannte Vollbild-Installationsmarkierung; keine Aenderung.")
    return data


def _save_manifest(folder, data):
    path = _manifest_path(folder)
    with path.open("x", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")


def install_fullscreen(folder):
    folder = Path(folder)
    if not assets_ready():
        raise RuntimeError("dgVoodoo-Dateien fehlen oder sind nicht verifiziert. Siehe README.")
    old = _load_manifest(folder)
    if old is not None:
        # Never silently take ownership of files replaced since installation.
        for name, expected in old["created"].items():
            dest = folder / name
            if not dest.is_file() or digest(dest) != expected:
                raise RuntimeError(f"{name} wurde nach Installation veraendert oder entfernt; bitte manuell pruefen.")
    if fullscreen_status(folder):
        return False
    sources = asset_paths()
    destinations = tuple(folder / name for name in FILES)
    for source, dest in zip(sources, destinations):
        if dest.exists() and (not dest.is_file() or digest(source) != digest(dest)):
            raise RuntimeError(f"Vorhandene Datei {dest.name} unterscheidet sich. Keine Ueberschreibung.")
    if old is not None:
        raise RuntimeError("Unvollstaendige markierte Installation; bitte manuell pruefen.")
    created = {}
    try:
        for source, dest in zip(sources, destinations):
            if not dest.exists():
                with dest.open("xb") as handle:
                    handle.write(source.read_bytes())
                created[dest.name] = digest(dest)
        if created:
            _save_manifest(folder, {"version": MANIFEST_VERSION, "created": created})
    except Exception:
        for name, expected in created.items():
            dest = folder / name
            if dest.is_file() and digest(dest) == expected:
                dest.unlink()
        raise
    return bool(created)


def restore_fullscreen(folder):
    folder = Path(folder)
    data = _load_manifest(folder)
    if data is None:
        print("Keine VISIQUE-Installationsmarkierung: dgVoodoo-Dateien bleiben unveraendert.")
        return False
    # Preflight every owned file before removing any of them.
    for name, expected in data["created"].items():
        dest = folder / name
        if not dest.is_file() or digest(dest) != expected:
            raise RuntimeError(f"{name} wurde veraendert oder entfernt; keine dgVoodoo-Dateien geloescht.")
    for name in data["created"]:
        (folder / name).unlink()
    _manifest_path(folder).unlink()
    print("Nur vom VISIQUE-Patcher angelegte, unveraenderte dgVoodoo-Dateien entfernt.")
    return True
