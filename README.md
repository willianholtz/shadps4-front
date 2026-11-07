# shadps4-front

![shadps4-front](icon.png)

A **PySide6 graphical frontend** for the [shadPS4](https://github.com/shadps4-emu/shadPS4) emulator on Linux:
game library with covers, game launcher and a **safe** editor for the emulator's `config.toml`.

> The frontend **never touches game files**. It only reads the library and, when you ask,
> edits shadPS4's `config.toml` (always with a backup).

---

## Features

### Library
- Scans the game folders configured in shadPS4 itself and builds the list automatically
- Reads the real game name from `sce_sys/param.sfo` and the cover from `sce_sys/icon0.png`
- Search by name, **icons** or **list** view, adjustable icon size
- Ignores `*-patch` folders and games without a valid `eboot.bin`

### Playing
- Double click (or context menu) starts the game
- Optional **gamemoderun** (when installed) for priority/performance
- Stop button, running status and automatic window restore when the game closes
- Prevents opening two games at the same time

### PKG installation
- Install `.pkg` directly from the UI, using `tools/pkginstall-cli`
- Install several files in sequence, with progress and cancel option
- Shows the destination folder at the end

### shadPS4 settings
- Lists **all** sections and keys of `config.toml` with proper widgets
  (checkbox, number, text, folder, list, combos with fixed values)
- Portuguese/English description for every option
- **Automatic backup** in `config.toml.backup-front` before any write
- Line-by-line merge: preserves comments and anything it does not understand
- Game folders managed by the UI (syncs `installDirs`/`installDirsEnabled`)

### Quick tweaks (context menu)
- Internal resolution: **720p / 1080p / 1440p / 4K**
- **Presets** (Performance / Balanced / Quality / Auto by GPU) — apply resolution, FSR, RCAS, HDR, PS4 Pro, fullscreen, pipeline cache, patch shaders, present mode and VBlank at once
- Toggle **FSR**, **RCAS** (sharpening), **HDR**, **PS4 Pro**, **Fullscreen**,
  **Pipeline cache**, **Patch shaders**
- Present mode (Mailbox / Fifo / Immediate) and VBlank (30 / 60 / 120 Hz)
- *These are global settings — they apply to all games*

### Utilities
- **Integrity check**: finds zeroed files (corrupted download/installation)
- Open game folder and addon folder
- **Delete ROM** sends to the trash (with `.trashinfo`, restorable)

### Interface
- Dark theme, PT-BR and English (switched on the fly)
- Responsive layout with a side section list in settings

---

## Requirements

- **Linux** (uses `gamemoderun` and the XDG trash)
- **Python 3.11+** (uses `tomllib`; tested on 3.14)
- **PySide6 6.x**
- **shadPS4** installed and reachable in `PATH` (or point the binary in `config/front.json`)
- Optional: `gamemode` for `gamemoderun`

```bash
# Arch
sudo pacman -S python pyside6
# Debian/Ubuntu
sudo apt install python3 python3-pyside6.qtwidgets
```

## Installation and usage

```bash
git clone https://github.com/willianholtz/shadps4-front.git
cd shadps4-front

python3 -m venv .venv
source .venv/bin/activate
pip install PySide6

python app.py
```

On first run the app imports the game folders already configured in shadPS4.
If there are none, add them in **Settings → Game folders**.

---

## How it works

| File | Role |
|---|---|
| `app.py` | Whole application (library, launcher, config editor) |
| `strings.py` | PT-BR/EN UI texts + description of each `config.toml` key |
| `config/front.json` | Frontend preferences (folders, binary, language, view) — **not committed**; template in `config/front.example.json` |
| `tools/pkginstall-cli` | PKG installer used by the UI |
| `icon.png` | App icon |

**Paths used:**

- Emulator config: `~/.local/share/shadPS4/config.toml`
- Frontend config: `config/front.json` (in the project folder)
- Legacy config (auto-migrated): `~/.config/shadps4-front/config.json`
- Emulator backup: `~/.local/share/shadPS4/config.toml.backup-front`

**PKG installer contract** (in case you swap the binary):

```bash
tools/pkginstall-cli game.pkg --out /destination/folder
# prints "OUTDIR=/folder/..." and "OK" on success
```

---

## Security

- Games are treated as **read-only**
- Every write to `config.toml` makes a backup first
- Deleting a ROM uses the system trash, never `rm -rf`
- Before applying, the app shows how many settings changed

## Known limitations

- Linux only
- Internal resolution, FSR and PS4 Pro are **global** (shadPS4's `config.toml` does not separate per game)
- The displayed title comes from `param.sfo`; games without it use the folder name
- `tools/PKGInstall.AppImage` (~30 MB) is an external utility and can be removed from the repo

## Legal notice

This project **does not include games, firmware or game data**. You need your own legal copy
of the titles. shadPS4 is a separate project; this repository is only a frontend.

## License

To be defined.

---

## Português (resumo)

**shadps4-front** é uma interface gráfica em PySide6 para o emulador shadPS4 no Linux:
biblioteca de jogos com capas, launcher (com `gamemoderun` opcional), instalador de PKG e
editor seguro do `config.toml` (backup automático, merge linha a linha preservando comentários).
Também oferece presets (Performance / Balanced / Quality / Auto por GPU) e ajustes rápidos
(resolução interna, FSR, RCAS, HDR, PS4 Pro, fullscreen, pipeline cache, patch shaders,
present mode, VBlank), verificação de integridade, abrir pasta e apagar ROM para a lixeira.

Requisitos: Linux, Python 3.11+, PySide6, shadPS4 no `PATH`. Rodar com `python app.py`.
Não inclui dados de jogos. Interface em PT-BR e English.