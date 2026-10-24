#!/usr/bin/env python3
"""Graphical frontend for Luxor 1 Windows compatibility patcher."""
import os
import base64
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from luxor_fullscreen import assets_ready as fullscreen_assets_ready, fullscreen_status
from luxor_cursor import asset_ready as cursor_asset_ready, cursor_status


def assets_ready():
    return fullscreen_assets_ready() and cursor_asset_ready()
from luxor_fix import (EXPECTED_ORIGINAL_SHA256, EXPECTED_PATCHED_SHA256,
                       find_upx, install, restore, sha256)


# Official VISIQUE logo embedded in the GUI; no separate asset required.
VISIQUE_LOGO_PNG_BASE64 = (
    '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'
    'Fa6AL3QAAAAASUVORK5CYII='
)


def steam_folders():
    roots = []
    if os.name == 'nt':
        try:
            import winreg
            for hive, key in ((winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam'),
                              (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Valve\Steam')):
                try:
                    with winreg.OpenKey(hive, key) as handle:
                        for name in ('SteamPath', 'InstallPath'):
                            try:
                                roots.append(Path(winreg.QueryValueEx(handle, name)[0]))
                            except OSError:
                                pass
                except OSError:
                    pass
        except ImportError:
            pass
    for var in ('ProgramFiles(x86)', 'ProgramFiles'):
        if os.environ.get(var):
            roots.append(Path(os.environ[var]) / 'Steam')
    candidates = []
    for root in roots:
        candidates.append(root / 'steamapps' / 'common' / 'Luxor')
        library_file = root / 'steamapps' / 'libraryfolders.vdf'
        if library_file.is_file():
            try:
                import re
                text = library_file.read_text(encoding='utf-8-sig', errors='replace')
                for value in re.findall(r'"path"\s+"([^"]+)"', text, flags=re.I):
                    library = Path(value.replace('\\\\', '\\'))
                    candidates.append(library / 'steamapps' / 'common' / 'Luxor')
            except OSError:
                pass
    return next((p for p in candidates if (p / 'LUXOR.exe').is_file()), None)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Luxor Fix by VISIQUE | Windows 10 & 11')
        self.geometry('780x720')
        self.minsize(700, 640)
        self.configure(bg='#242325')
        self.queue = queue.Queue()
        self.busy = False
        self.folder = tk.StringVar(value=str(steam_folders() or ''))
        self.steam_dll = tk.StringVar()
        self.status = tk.StringVar(value='Spielordner auswählen und Version prüfen.')
        self.build()
        self.after(100, self.drain)
        self.check()

    def build(self):
        # VISIQUE palette; presentation only. All patch operations remain unchanged.
        bg, panel, input_bg = '#242325', '#333136', '#29282B'
        white, muted, yellow, purple = '#FFFFFF', '#B8B5BC', '#FDCA40', '#6B1755'
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('VQ.TButton', background=panel, foreground=white,
                        borderwidth=0, padding=(14, 10), font=('Segoe UI', 10, 'bold'))
        style.map('VQ.TButton', background=[('active', '#49464D'), ('disabled', '#3B3940')],
                  foreground=[('disabled', '#85818A')])
        style.configure('VQ.Primary.TButton', background=yellow, foreground=bg,
                        borderwidth=0, padding=(18, 15), font=('Segoe UI', 11, 'bold'))
        style.map('VQ.Primary.TButton', background=[('active', '#F4BE22'), ('disabled', '#5C5439')],
                  foreground=[('disabled', '#A7A08C')])
        style.configure('VQ.Outline.TButton', background=bg, foreground=white,
                        borderwidth=1, relief='solid', padding=(18, 13), font=('Segoe UI', 10, 'bold'))
        style.map('VQ.Outline.TButton', background=[('active', panel), ('disabled', '#29282B')],
                  foreground=[('disabled', '#85818A')])
        style.configure('VQ.TEntry', fieldbackground=input_bg, foreground=white,
                        borderwidth=1, padding=9, insertcolor=white)
        style.map('VQ.TEntry', fieldbackground=[('readonly', input_bg)])

        root = tk.Frame(self, bg=bg, padx=30, pady=22)
        root.pack(fill='both', expand=True)
        header = tk.Frame(root, bg=bg)
        header.pack(fill='x')
        self.visique_logo = tk.PhotoImage(data=VISIQUE_LOGO_PNG_BASE64)
        logo = tk.Label(header, image=self.visique_logo, bg=bg, borderwidth=0,
                        highlightthickness=0)
        logo.pack(side='left', padx=(0, 16))
        # Subtle vertical divider separating VISIQUE branding from the app name.
        tk.Frame(header, bg='#5A565E', width=1, height=40).pack(
            side='left', padx=(0, 18))
        brand = tk.Frame(header, bg=bg)
        brand.pack(side='left')
        tk.Label(brand, text='LUXOR FIX', bg=bg, fg=white,
                 font=('Segoe UI', 16, 'bold')).pack(anchor='w')
        tk.Label(brand, text='BY VISIQUE', bg=bg, fg=yellow,
                 font=('Segoe UI', 9, 'bold')).pack(anchor='w')
        tk.Label(header, text='v0.3.0-local-test', bg=bg, fg=muted,
                 font=('Segoe UI', 9)).pack(side='right')
        tk.Frame(root, bg='#47444A', height=1).pack(fill='x', pady=(17, 22))
        tk.Label(root, text='Make Luxor playable again.', bg=bg, fg=white,
                 font=('Segoe UI', 22, 'bold')).pack(anchor='w')
        tk.Label(root, text='Windows 10 & 11 Compatibility Fix', bg=bg, fg=muted,
                 font=('Segoe UI', 11)).pack(anchor='w', pady=(4, 18))

        panel_frame = tk.Frame(root, bg=panel, padx=18, pady=15)
        panel_frame.pack(fill='x')
        tk.Label(panel_frame, text='GAME INSTALLATION', bg=panel, fg=white,
                 font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(0, 7))
        self.path_field(panel_frame, 'Steam-Spielordner', self.folder, self.pick_folder)
        self.status_label = tk.Label(panel_frame, textvariable=self.status, bg=panel,
                                     fg=yellow, font=('Segoe UI', 10, 'bold'),
                                     wraplength=650, justify='left', anchor='w')
        self.status_label.pack(fill='x', pady=(6, 0))

        self.install_button = ttk.Button(root, text='INSTALL COMPATIBILITY FIX',
                                          style='VQ.Primary.TButton',
                                          command=lambda: self.run_action('install'))
        self.install_button.pack(fill='x', pady=(16, 8))
        self.restore_button = ttk.Button(root, text='Original wiederherstellen',
                                          style='VQ.Outline.TButton',
                                          command=lambda: self.run_action('restore'))
        self.restore_button.pack(fill='x')

        options = tk.Frame(root, bg=bg)
        options.pack(fill='x', pady=(13, 0))
        self.check_button = ttk.Button(options, text='Version erneut prüfen',
                                        style='VQ.TButton', command=self.check)
        self.check_button.pack(side='left')
        self.advanced_open = False
        self.advanced_button = ttk.Button(options, text='Erweiterte Optionen anzeigen',
                                           style='VQ.TButton', command=self.toggle_advanced)
        self.advanced_button.pack(side='right')
        self.advanced = tk.Frame(root, bg=panel, padx=14, pady=12)
        self.path_field(self.advanced, 'Steam.dll (optional; automatisch gesucht)',
                        self.steam_dll, self.pick_dll)

        tk.Label(root, text='TECHNISCHES PROTOKOLL', bg=bg, fg=muted,
                 font=('Segoe UI', 9, 'bold')).pack(anchor='w', pady=(17, 7))
        log_frame = tk.Frame(root, bg=panel, padx=9, pady=9)
        log_frame.pack(fill='both', expand=True)
        self.log = tk.Text(log_frame, height=5, state='disabled', wrap='word',
                           font=('Consolas', 9), bg=input_bg, fg='#E8E6EA',
                           insertbackground=white, borderwidth=0, padx=8, pady=8,
                           selectbackground=purple)
        self.log.pack(fill='both', expand=True)
        footer = tk.Frame(root, bg=bg)
        footer.pack(fill='x', pady=(14, 0))
        tk.Label(footer, text='Developed by Fabian ~ VISIQUE', bg=bg, fg=muted,
                 font=('Segoe UI', 9)).pack(side='left')
        tk.Label(footer, text='Open Source  ·  No game files included',
                 bg=bg, fg=yellow, font=('Segoe UI', 9)).pack(side='right')

    def toggle_advanced(self):
        self.advanced_open = not self.advanced_open
        if self.advanced_open:
            self.advanced.pack(fill='x', after=self.advanced_button.master)
            self.advanced_button.configure(text='Erweiterte Optionen ausblenden')
        else:
            self.advanced.pack_forget()
            self.advanced_button.configure(text='Erweiterte Optionen anzeigen')

    def path_field(self, parent, title, variable, callback, folder=False):
        background = parent.cget('bg')
        tk.Label(parent, text=title, bg=background, fg='#B8B5BC',
                 font=('Segoe UI', 9)).pack(anchor='w')
        row = tk.Frame(parent, bg=background)
        row.pack(fill='x', pady=(4, 9))
        entry = ttk.Entry(row, textvariable=variable, style='VQ.TEntry')
        entry.pack(side='left', fill='x', expand=True, padx=(0, 8))
        ttk.Button(row, text='Durchsuchen', style='VQ.TButton',
                   command=callback).pack(side='right')

    def pick_folder(self):
        result = filedialog.askdirectory(initialdir=self.folder.get() or None)
        if result:
            self.folder.set(result)
            self.check()

    def pick_dll(self):
        result = filedialog.askopenfilename(filetypes=[('Steam DLL', 'Steam.dll'), ('DLL', '*.dll')])
        if result:
            self.steam_dll.set(result)

    def append(self, message):
        self.log.configure(state='normal')
        self.log.insert('end', message + '\n')
        self.log.see('end')
        self.log.configure(state='disabled')

    def check(self):
        folder = Path(self.folder.get())
        exe = folder / 'LUXOR.exe'
        if not exe.is_file():
            self.status.set('Keine LUXOR.exe gefunden. Bitte den richtigen Spielordner auswählen.')
            self.install_button.configure(state='disabled')
            self.restore_button.configure(state='disabled')
            self.append('PRÜFUNG: Keine LUXOR.exe im gewählten Ordner gefunden.')
            return
        try:
            digest = sha256(exe.read_bytes())
            if digest == EXPECTED_ORIGINAL_SHA256:
                self.status.set('Originalversion erkannt. Kompatibilitäts-, Vollbild- und Cursor-Fix verfügbar.' if assets_ready() else 'Originalversion erkannt. dgVoodoo- oder Cursor-Dateien fehlen (README).')
                self.install_button.configure(state='normal' if assets_ready() else 'disabled')
            elif digest == EXPECTED_PATCHED_SHA256:
                ready = fullscreen_status(folder) and cursor_status(folder)
                self.status.set('EXE, Vollbild- und Cursor-Fix installiert.' if ready else 'EXE gepatcht. Vollbild-/Cursor-Fix kann ergänzt werden.' if assets_ready() else 'EXE gepatcht. dgVoodoo- oder Cursor-Dateien fehlen (README).')
                self.install_button.configure(state='disabled' if ready or not assets_ready() else 'normal')
            else:
                self.status.set('Unbekannte Spielversion. Änderungen sind gesperrt.')
                self.install_button.configure(state='disabled')
            self.append('PRÜFUNG: ' + self.status.get())
            self.append('SHA256: ' + digest)
            backup = folder / 'LUXOR.exe.backup'
            self.restore_button.configure(state='normal' if backup.is_file() and sha256(backup.read_bytes()) == EXPECTED_ORIGINAL_SHA256 and digest in (EXPECTED_ORIGINAL_SHA256, EXPECTED_PATCHED_SHA256) else 'disabled')
        except OSError as exc:
            self.status.set(f'Lesefehler: {exc}')
            self.append('FEHLER: ' + str(exc))
            self.install_button.configure(state='disabled')
            self.restore_button.configure(state='disabled')

    def run_action(self, action):
        if self.busy:
            return
        if not messagebox.askyesno('Bestätigen', 'Luxor muss geschlossen sein. ' + ('Fix jetzt installieren?' if action == 'install' else 'Originaldatei jetzt wiederherstellen?')):
            return
        folder = Path(self.folder.get())
        dll = self.steam_dll.get().strip() or None
        self.busy = True
        for button in (self.install_button, self.restore_button, self.check_button):
            button.configure(state='disabled')
        self.status.set('Bitte warten …')
        self.append('Aktion: ' + action)

        def work():
            try:
                if action == 'install':
                    install(folder, None, dll)
                else:
                    restore(folder)
                self.queue.put((True, 'Aktion erfolgreich abgeschlossen.'))
            except Exception as exc:
                self.queue.put((False, str(exc)))
        threading.Thread(target=work, daemon=True).start()

    def drain(self):
        try:
            while True:
                ok, message = self.queue.get_nowait()
                self.busy = False
                self.append(('OK: ' if ok else 'FEHLER: ') + message)
                self.check_button.configure(state='normal')
                self.check()
                if ok:
                    messagebox.showinfo('Luxor Fix', message)
                else:
                    messagebox.showerror('Luxor Fix', message)
        except queue.Empty:
            pass
        self.after(100, self.drain)


if __name__ == '__main__':
    App().mainloop()
