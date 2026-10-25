"""shadps4-front: biblioteca + configuracoes. Somente leitura nos jogos."""
import json
import os
import re
import struct
import sys
import tomllib

from PySide6.QtCore import Qt, QProcess, QSize, QUrl
from PySide6.QtGui import QDesktopServices, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QMessageBox, QPushButton, QScrollArea, QSlider, QSpinBox, QSplitter, QTabWidget,
    QVBoxLayout, QWidget,
)

from strings import DESC, UI

LANGS = {"pt": "Português (BR)", "en": "English"}


def tr(front, key):
    return UI[key][0 if front.get("lang", "pt") == "pt" else 1]


def desc_text(front, key):
    d = DESC.get(key)
    if not d:
        return ""
    return d[0] if front.get("lang", "pt") == "pt" else d[1]

SHAD_CONFIG = os.path.expanduser("~/.local/share/shadPS4/config.toml")
PROJ_DIR = os.path.dirname(os.path.abspath(__file__))
FRONT_DIR = os.path.join(PROJ_DIR, "config")
FRONT_CONFIG = os.path.join(FRONT_DIR, "front.json")
LEGACY_CONFIG = os.path.expanduser("~/.config/shadps4-front/config.json")


def default_front():
    return {"game_dirs": install_dirs_from_shad(), "emu_bin": "shadps4",
            "use_gamemode": True, "lang": "pt", "view_mode": "icons",
            "icon_size": 180}


def load_front():
    try:
        if not os.path.isfile(FRONT_CONFIG) and os.path.isfile(LEGACY_CONFIG):
            os.makedirs(FRONT_DIR, exist_ok=True)
            os.rename(LEGACY_CONFIG, FRONT_CONFIG)
        with open(FRONT_CONFIG) as f:
            cfg = json.load(f)
        for key, val in default_front().items():
            cfg.setdefault(key, val)
        return cfg
    except (OSError, ValueError):
        cfg = default_front()
        save_front(cfg)
        return cfg


def save_front(cfg):
    os.makedirs(FRONT_DIR, exist_ok=True)
    with open(FRONT_CONFIG, "w") as f:
        json.dump(cfg, f, indent=2)


def install_dirs_from_shad():
    try:
        with open(SHAD_CONFIG, "rb") as f:
            cfg = tomllib.load(f)
        gui = cfg.get("GUI", {})
        dirs = gui.get("installDirs", [])
        enabled = gui.get("installDirsEnabled", [])
        return [d for d, e in zip(dirs, enabled + [True] * len(dirs))
                if e and os.path.isdir(d)]
    except OSError:
        return []


def read_sfo(path):
    try:
        with open(path, "rb") as f:
            data = f.read()
        if data[:4] != b"\x00PSF":
            return {}
        key_off, val_off, n = struct.unpack("<III", data[8:20])
        out = {}
        for i in range(n):
            ko, _fmt, dlen, _dmax, voff = struct.unpack("<HHIII", data[20 + i * 16:36 + i * 16])
            key = data[key_off + ko:].split(b"\x00")[0].decode()
            out[key] = data[val_off + voff:val_off + voff + dlen].split(b"\x00")[0]
        return {"title": out.get("TITLE", b"?").decode(errors="replace")}
    except OSError:
        return {}


def scan_games(dirs):
    games = []
    for base in dirs:
        try:
            names = sorted(os.listdir(base))
        except OSError:
            continue
        for name in names:
            if name.endswith("-patch"):
                continue
            gdir = os.path.join(base, name)
            if not os.path.isdir(gdir):
                continue
            eboot = os.path.join(gdir, "eboot.bin")
            if not (os.path.isfile(eboot) and os.path.getsize(eboot) > 0):
                continue
            info = read_sfo(os.path.join(gdir, "sce_sys", "param.sfo"))
            icon = os.path.join(gdir, "sce_sys", "icon0.png")
            if not (os.path.isfile(icon) and os.path.getsize(icon) > 0):
                icon = ""
            games.append({"title": info.get("title") or name, "dir": gdir,
                          "eboot": eboot, "icon": icon})
    return games


def to_toml(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "[" + ", ".join(to_toml(v) for v in value) + "]"
    raise TypeError(type(value))


def apply_to_shad_config(changes):
    """changes: {(section, key): value}. Merge por linha, preserva o resto."""
    with open(SHAD_CONFIG) as f:
        lines = f.read().splitlines()
    out = []
    section = None
    pending = dict(changes)
    key_re = re.compile(r"^(\s*)([A-Za-z0-9_]+)(\s*=\s*)(.*?)(\s*(#.*)?)$")

    def flush_section():
        for (sec, key), val in sorted(pending.items()):
            if sec == section:
                out.append(f"{key} = {to_toml(val)}")
                del pending[(sec, key)]

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            flush_section()
            section = stripped[1:-1]
            out.append(line)
            continue
        m = key_re.match(line)
        if m and section and (section, m.group(2)) in pending:
            val = pending.pop((section, m.group(2)))
            comment = m.group(5) or ""
            out.append(f"{m.group(1)}{m.group(2)}{m.group(3)}{to_toml(val)}{comment}")
        else:
            out.append(line)
    flush_section()
    for (sec, key), val in sorted(pending.items()):
        out.append(f"[{sec}]" if sec not in {l.strip()[1:-1] for l in out
                                             if l.strip().startswith('[')} else "")
        out.append(f"{key} = {to_toml(val)}")
    with open(SHAD_CONFIG, "w") as f:
        f.write("\n".join(out) + "\n")
    return True


MODERN_QSS = """
* { outline: none; }
QMainWindow, QWidget { background-color: #16181d; color: #dcdde1; font-size: 13px; }
QTabWidget::pane { border: none; background: #16181d; }
QTabBar::tab { background: #1f222a; color: #9aa0ab; padding: 8px 22px;
    border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 4px; }
QTabBar::tab:selected { background: #2b303c; color: #ffffff; }
QTabBar::tab:hover { color: #ffffff; }
QListWidget { background: #1a1d24; border: 1px solid #2b303c; border-radius: 10px;
    padding: 10px; spacing: 6px; }
QListWidget::item { border-radius: 8px; padding: 4px; }
QListWidget::item:selected { background: #2f6db3; color: white; }
QListWidget::item:hover:!selected { background: #262b36; }
QListWidget#sectionList { background: #1a1d24; }
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox { background: #22262f; color: #dcdde1;
    border: 1px solid #343a47; border-radius: 8px; padding: 6px 10px; selection-background-color: #2f6db3; }
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus { border: 1px solid #2f6db3; }
QComboBox QAbstractItemView { background: #22262f; border: 1px solid #343a47;
    selection-background-color: #2f6db3; }
QPushButton { background: #2b303c; color: #e8e9eb; border: none; border-radius: 8px;
    padding: 8px 18px; }
QPushButton:hover { background: #384052; }
QPushButton:pressed { background: #232833; }
QPushButton:disabled { background: #1f222a; color: #5c616b; }
QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 18px; height: 18px; border-radius: 9px;
    background: #2b303c; border: 1px solid #4a5160; }
QCheckBox::indicator:checked { background: #2f6db3; border: 1px solid #2f6db3; }
QSlider::groove:horizontal { height: 6px; background: #2b303c; border-radius: 3px; }
QSlider::handle:horizontal { width: 16px; height: 16px; margin: -6px 0;
    border-radius: 8px; background: #2f6db3; }
QScrollBar:vertical { background: transparent; width: 10px; }
QScrollBar::handle:vertical { background: #343a47; border-radius: 5px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: transparent; height: 10px; }
QScrollBar::handle:horizontal { background: #343a47; border-radius: 5px; min-width: 30px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }
QSplitter::handle { background: #2b303c; }
QToolTip { background: #22262f; color: #e8e9eb; border: 1px solid #343a47; padding: 6px; }
QLabel { color: #dcdde1; }
QLabel#desc { color: #8a90a0; font-size: 12px; }
QLabel:disabled { color: #5c616b; }
QScrollArea { border: none; background: transparent; }
QMessageBox { background: #1a1d24; }
QPushButton#accent { background: #2f6db3; font-weight: bold; }
QPushButton#accent:hover { background: #3d7fc7; }
QPushButton#accent:pressed { background: #275a94; }
"""

COMBO_STR = {
    "FullscreenMode": ["Windowed", "Fullscreen (Borderless)", "Fullscreen"],
    "presentMode": ["Mailbox", "Fifo", "Immediate"],
    "sideTrophy": ["left", "right", "top", "bottom"],
    "chooseHomeTab": ["General", "Frontend", "Graphics", "User", "Input",
                      "Network", "Paths", "Log", "Debug", "Experimental"],
    "micDevice": ["None", "Default Device"],
}

_LANG_NAMES = ["Arabic", "Czech", "Danish", "Dutch", "English (United Kingdom)",
               "English (United States)", "Finnish", "French (Canada)", "French (France)",
               "German", "Greek", "Hungarian", "Indonesian", "Italian", "Japanese",
               "Korean", "Norwegian (Bokmaal)", "Polish", "Portuguese (Brazil)",
               "Portuguese (Portugal)", "Romanian", "Russian", "Simplified Chinese",
               "Spanish (Latin America)", "Spanish (Spain)", "Swedish", "Thai",
               "Traditional Chinese", "Turkish", "Ukrainian", "Vietnamese"]
_LANG_CODES = [21, 23, 14, 6, 18, 1, 12, 22, 2, 4, 25, 24, 29, 5, 0, 9,
               15, 16, 17, 7, 26, 8, 11, 20, 3, 13, 27, 10, 19, 30, 28]

COMBO_INT = {
    "cursorState": [("Never", 0), ("Idle", 1), ("Always", 2)],
    "usbDeviceBackend": [("Real USB Device", 0), ("Skylander Portal", 1),
                         ("Infinity Base", 2), ("Dimensions Toypad", 3)],
    "consoleLanguage": list(zip(_LANG_NAMES, _LANG_CODES)),
}

FOLDER_KEYS = {"fontsPath", "sysModulesPath", "saveDataPath", "addonInstallDir"}

INT_RANGES = {"volumeSlider": (0, 100)}


class SettingsTab(QWidget):
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.widgets = {}
        layout = QVBoxLayout(self)

        folders = QHBoxLayout()
        self.folders_label = QLabel()
        folders.addWidget(self.folders_label)
        self.dir_list = QListWidget()
        self.dir_list.setMaximumHeight(80)
        folders.addWidget(self.dir_list, 1)
        self.add_btn = QPushButton()
        self.add_btn.clicked.connect(self.add_dir)
        self.rm_btn = QPushButton()
        self.rm_btn.clicked.connect(self.remove_dir)
        folders.addWidget(self.add_btn)
        folders.addWidget(self.rm_btn)
        layout.addLayout(folders)

        split = QSplitter()
        self.sec_list = QListWidget()
        self.sec_list.setObjectName("sectionList")
        self.sec_list.setMaximumWidth(180)
        self.sec_list.currentRowChanged.connect(self.show_section)
        split.addWidget(self.sec_list)
        self.form_inner = QWidget()
        self.form_layout = QFormLayout(self.form_inner)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.form_inner)
        split.addWidget(scroll)
        layout.addWidget(split, 1)

        btns = QHBoxLayout()
        apply_btn = QPushButton()
        apply_btn.setObjectName("accent")
        apply_btn.clicked.connect(self.apply)
        self.apply_btn = apply_btn
        reload_btn = QPushButton()
        reload_btn.clicked.connect(self.reload)
        self.reload_btn = reload_btn
        btns.addWidget(apply_btn)
        btns.addWidget(reload_btn)
        btns.addStretch(1)
        layout.addLayout(btns)

        self.retranslate()

    def retranslate(self):
        f = self.main.front
        self.folders_label.setText(tr(f, "folders"))
        self.add_btn.setText(tr(f, "add"))
        self.rm_btn.setText(tr(f, "remove"))
        self.apply_btn.setText(tr(f, "apply"))
        self.reload_btn.setText(tr(f, "reload"))

        self.sections = []
        self.reload()

    def reload(self):
        self.dir_list.clear()
        for d in self.main.front.get("game_dirs", []):
            self.dir_list.addItem(d)
        try:
            with open(SHAD_CONFIG, "rb") as f:
                cfg = tomllib.load(f)
        except OSError as e:
            QMessageBox.warning(self, "shadps4-front",
                                f"{tr(self.main.front, 'no_read')} {e}")
            return
        front = self.main.front
        self.sections = [(s, v) for s, v in cfg.items() if isinstance(v, dict)]
        self.widgets = {}
        self.sec_list.clear()
        for section, _values in self.sections:
            self.sec_list.addItem(section)
        if self.sections:
            self.sec_list.setCurrentRow(0)
        else:
            self.show_section(-1)

    def show_section(self, row):
        while self.form_layout.count():
            child = self.form_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)
        if row < 0 or row >= len(self.sections):
            return
        front = self.main.front
        section, values = self.sections[row]
        for key, val in values.items():
            if section == "GUI" and key in ("installDirs", "installDirsEnabled"):
                self.form_layout.addRow(key, QLabel(tr(front, "managed_folders")))
                continue
            widget = self.make_widget(section, key, val)
            if widget is None:
                self.form_layout.addRow(key, QLabel(
                    f"{tr(front, 'not_editable')}: {type(val).__name__})"))
                continue
            self.form_layout.addRow(key, widget)
            self.widgets[(section, key)] = widget
            desc = desc_text(front, key)
            if desc:
                lab = QLabel(desc)
                lab.setObjectName("desc")
                lab.setWordWrap(True)
                self.form_layout.addRow(lab)

    def make_widget(self, section, key, val):
        if isinstance(val, int) and key in COMBO_INT:
            w = QComboBox()
            for label, code in COMBO_INT[key]:
                w.addItem(label, code)
            idx = w.findData(val)
            if idx == -1:
                w.addItem(str(val), val)
                idx = w.count() - 1
            w.setCurrentIndex(idx)
            w._kind = "combo_int"
            w._orig = val
            return w
        if isinstance(val, str) and key in COMBO_STR:
            w = QComboBox()
            w.addItems(COMBO_STR[key])
            if val not in COMBO_STR[key]:
                w.addItem(val)
            w.setCurrentText(val)
            w._kind = "combo"
            w._orig = val
            return w
        if isinstance(val, str) and key in FOLDER_KEYS:
            box = QWidget()
            lay = QHBoxLayout(box)
            lay.setContentsMargins(0, 0, 0, 0)
            edit = QLineEdit(val)
            btn = QPushButton("...")
            btn.setMaximumWidth(36)
            btn.clicked.connect(lambda: self.browse_folder(edit))
            lay.addWidget(edit, 1)
            lay.addWidget(btn)
            box._kind = "folder"
            box._edit = edit
            box._orig = val
            return box
        if isinstance(val, bool):
            w = QCheckBox()
            w.setChecked(val)
            w._kind = "bool"
            w._orig = val
            return w
        if isinstance(val, int):
            w = QSpinBox()
            lo, hi = INT_RANGES.get(key, (-1000000, 1000000000))
            w.setRange(lo, hi)
            w.setValue(max(lo, min(hi, val)))
            w._kind = "int"
            w._orig = val
            return w
        if isinstance(val, float):
            w = QDoubleSpinBox()
            w.setRange(-1e9, 1e9)
            w.setDecimals(3)
            w.setValue(val)
            w._kind = "float"
            w._orig = val
            return w
        if isinstance(val, str):
            w = QLineEdit(val)
            w._kind = "str"
            w._orig = val
            return w
        if isinstance(val, list) and all(isinstance(v, str) for v in val):
            w = QLineEdit(", ".join(val))
            w._kind = "list"
            w._orig = list(val)
            return w
        return None

    def read_widget(self, widget):
        kind = widget._kind
        if kind == "bool":
            return widget.isChecked()
        if kind == "combo":
            return widget.currentText()
        if kind == "combo_int":
            return widget.currentData()
        if kind == "folder":
            return widget._edit.text()
        if kind in ("int", "float"):
            return widget.value()
        if kind == "str":
            return widget.text()
        if kind == "list":
            return [v.strip() for v in widget.text().split(",") if v.strip()]
        raise TypeError(kind)

    def browse_folder(self, edit):
        d = QFileDialog.getExistingDirectory(self, edit.text() or tr(
            self.main.front, "folder_title"))
        if d:
            edit.setText(d)

    def add_dir(self):
        d = QFileDialog.getExistingDirectory(self, tr(self.main.front, "folder_title"))
        if d and not any(self.dir_list.item(i).text() == d
                         for i in range(self.dir_list.count())):
            self.dir_list.addItem(d)

    def remove_dir(self):
        for item in self.dir_list.selectedItems():
            self.dir_list.takeItem(self.dir_list.row(item))

    def apply(self):
        try:
            import shutil
            backup = SHAD_CONFIG + ".backup-front"
            shutil.copy2(SHAD_CONFIG, backup)
        except OSError as e:
            QMessageBox.warning(self, "shadps4-front",
                                f"{tr(self.main.front, 'no_backup')} {e}")
            return
        changes = {}
        for (section, key), widget in self.widgets.items():
            try:
                val = self.read_widget(widget)
            except TypeError:
                continue
            if val != widget._orig:
                changes[(section, key)] = val
        dirs = [self.dir_list.item(i).text() for i in range(self.dir_list.count())]
        self.main.front["game_dirs"] = dirs
        save_front(self.main.front)
        changes[("GUI", "installDirs")] = [d for d in dirs if os.path.isdir(d)]
        changes[("GUI", "installDirsEnabled")] = [True] * len(changes[("GUI", "installDirs")])
        try:
            apply_to_shad_config(changes)
        except (OSError, TypeError) as e:
            QMessageBox.warning(self, "shadps4-front",
                                f"{tr(self.main.front, 'apply_fail')} {e}")
            return
        for widget in self.widgets.values():
            try:
                widget._orig = self.read_widget(widget)
            except TypeError:
                pass
        self.main.reload_library()
        QMessageBox.information(self, "shadps4-front",
                                f"{tr(self.main.front, 'applied')} "
                                f"({len(changes)} ajustes). Backup em config.toml.backup-front")


class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("shadps4-front")
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
        if os.path.isfile(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.resize(1000, 650)
        self.front = load_front()
        self.proc = QProcess(self)
        self.proc.finished.connect(self.on_finished)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        lib = QWidget()
        layout = QVBoxLayout(lib)
        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.textChanged.connect(self.apply_filter)
        self.view_combo = QComboBox()
        self.view_combo.currentTextChanged.connect(self.change_view)
        self.lang_combo = QComboBox()
        for code, name in LANGS.items():
            self.lang_combo.addItem(name, code)
        self.lang_combo.setCurrentIndex(0 if self.front.get("lang", "pt") == "pt" else 1)
        self.lang_combo.currentIndexChanged.connect(self.change_lang)
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(96, 320)
        self.size_slider.setSingleStep(16)
        self.size_slider.setValue(int(self.front.get("icon_size", 180)))
        self.size_slider.setMaximumWidth(160)
        self.size_slider.setToolTip("Tamanho dos ícones")
        self.size_slider.valueChanged.connect(self.change_size)
        refresh = QPushButton()
        refresh.clicked.connect(self.reload_library)
        self.refresh_btn = refresh
        install_btn = QPushButton()
        install_btn.setObjectName("accent")
        install_btn.clicked.connect(self.install_pkg)
        self.install_btn = install_btn
        top.addWidget(self.search)
        top.addWidget(self.view_combo)
        top.addWidget(self.lang_combo)
        top.addWidget(self.size_slider)
        top.addWidget(self.install_btn)
        top.addWidget(refresh)
        layout.addLayout(top)

        self.list = QListWidget()
        self.list.setViewMode(QListWidget.IconMode)
        self.list.setResizeMode(QListWidget.Adjust)
        self.list.setMovement(QListWidget.Static)
        self.list.itemDoubleClicked.connect(lambda _i: self.play())
        self.list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self.context_menu)
        layout.addWidget(self.list)

        bottom = QHBoxLayout()
        self.play_btn = QPushButton()
        self.play_btn.clicked.connect(self.play)
        self.stop_btn = QPushButton()
        self.stop_btn.clicked.connect(self.stop)
        self.stop_btn.setEnabled(False)
        self.status = QLabel("")
        bottom.addWidget(self.play_btn)
        bottom.addWidget(self.stop_btn)
        bottom.addWidget(self.status, 1)
        layout.addLayout(bottom)

        self.tabs.addTab(lib, "")
        self.settings = SettingsTab(self)
        self.tabs.addTab(self.settings, "")
        self.retranslate()
        self.reload_library()

    def retranslate(self):
        f = self.front
        self.tabs.setTabText(0, tr(f, "library"))
        self.tabs.setTabText(1, tr(f, "settings"))
        self.search.setPlaceholderText(tr(f, "search"))
        self.view_combo.blockSignals(True)
        self.view_combo.clear()
        self.view_combo.addItems([tr(f, "icons"), tr(f, "list")])
        self.view_combo.setCurrentText(tr(f, "list") if f.get("view_mode") == "list"
                                       else tr(f, "icons"))
        self.view_combo.blockSignals(False)
        self.play_btn.setText(tr(f, "play"))
        self.stop_btn.setText(tr(f, "stop"))
        self.refresh_btn.setText(tr(f, "refresh"))
        self.install_btn.setText(tr(f, "install_pkg"))
        if self.proc.state() == QProcess.NotRunning:
            self.status.setText(tr(f, "ready"))
        self.settings.retranslate()

    def change_lang(self, index):
        self.front["lang"] = self.lang_combo.itemData(index)
        save_front(self.front)
        self.retranslate()
        self.settings.reload()

    def reload_library(self):
        self.list.clear()
        games = scan_games(self.front.get("game_dirs", []))
        for g in games:
            if g["icon"]:
                pix = QPixmap(g["icon"])
            else:
                pix = QPixmap()
            if pix.isNull():
                pix = QPixmap(512, 288)
                pix.fill(Qt.darkGray)
            item = QListWidgetItem(QIcon(pix), g["title"])
            item.setData(Qt.UserRole, g)
            item.setData(Qt.UserRole + 1, pix)
            item.setToolTip(f"{g['title']}\n{g['dir']}")
            self.list.addItem(item)
        self.apply_view()
        self.status.setText(f"{len(games)} jogos")
        self.apply_filter(self.search.text())

    def apply_view(self):
        if self.front.get("view_mode", "icons") == "list":
            self.list.setViewMode(QListWidget.ListMode)
            self.list.setIconSize(QSize(48, 48))
            self.list.setUniformItemSizes(False)
            self.list.setWordWrap(False)
        else:
            h = int(self.front.get("icon_size", 180))
            w = int(h * 16 / 9)
            self.list.setViewMode(QListWidget.IconMode)
            self.list.setIconSize(QSize(w, h))
            self.list.setGridSize(QSize(w + 24, h + 64))
            self.list.setUniformItemSizes(True)
            self.list.setWordWrap(True)

    def change_view(self, text):
        self.front["view_mode"] = ("list" if self.view_combo.currentIndex() == 1
                                   else "icons")
        save_front(self.front)
        self.apply_view()

    def change_size(self, value):
        self.front["icon_size"] = value
        save_front(self.front)
        if self.front.get("view_mode", "icons") != "list":
            self.apply_view()

    def install_pkg(self):
        tool = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "tools", "pkginstall-cli")
        if not os.path.isfile(tool):
            QMessageBox.warning(self, "shadps4-front", "pkginstall-cli não encontrado em tools/.")
            return
        files, _ = QFileDialog.getOpenFileNames(
            self, "Selecionar PKG(s)", os.path.expanduser("~/Downloads"),
            "PS4 PKG (*.pkg)")
        if not files:
            return
        dirs = self.front.get("game_dirs", [])
        outbase = dirs[0] if dirs else os.path.expanduser("~/Downloads")
        for pkg in files:
            if not self.install_one_pkg(tool, pkg, outbase):
                break
        self.reload_library()

    def install_one_pkg(self, tool, pkg, outbase):
        from PySide6.QtWidgets import QProgressDialog
        dlg = QProgressDialog(f"Instalando {os.path.basename(pkg)}...",
                              "Cancelar", 0, 0, self)
        dlg.setWindowTitle("shadps4-front")
        dlg.setMinimumDuration(500)
        dlg.setValue(0)
        proc = QProcess(self)
        proc.start(tool, [pkg, "--out", outbase])
        while proc.state() != QProcess.NotRunning:
            QApplication.processEvents()
            if dlg.wasCanceled():
                proc.kill()
                proc.waitForFinished(5000)
                dlg.close()
                return False
            proc.waitForFinished(200)
        dlg.close()
        out = bytes(proc.readAllStandardOutput()).decode(errors="replace")
        err = bytes(proc.readAllStandardError()).decode(errors="replace")
        if proc.exitStatus() == QProcess.NormalExit and proc.exitCode() == 0 and "\nOK" in out:
            dest = ""
            for line in out.splitlines():
                if line.startswith("OUTDIR="):
                    dest = line[7:]
            QMessageBox.information(self, "shadps4-front", f"Instalado em:\n{dest}")
            return True
        QMessageBox.warning(self, "shadps4-front",
                            f"Falha ao instalar {os.path.basename(pkg)}:\n{err.strip() or out.strip()}")
        return False

    def apply_filter(self, text):
        text = text.lower()
        for i in range(self.list.count()):
            item = self.list.item(i)
            title = item.data(Qt.UserRole)["title"].lower()
            item.setHidden(text not in title)

    def play(self):
        item = self.list.currentItem()
        game = item.data(Qt.UserRole) if item else None
        if not game:
            return
        if self.proc.state() != QProcess.NotRunning:
            QMessageBox.information(self, "shadps4-front",
                                    tr(self.front, "already_running"))
            return
        args = []
        if self.front.get("use_gamemode"):
            self.proc.start("gamemoderun", [self.front.get("emu_bin", "shadps4"),
                                            "--game", game["eboot"]])
        else:
            self.proc.start(self.front.get("emu_bin", "shadps4"), ["--game", game["eboot"]])
            args = []
        if self.proc.waitForStarted(5000):
            self.status.setText(f"{tr(self.front, 'running')} {game['title']}")
            self.stop_btn.setEnabled(True)
            self.hide()
        else:
            QMessageBox.warning(self, "shadps4-front", tr(self.front, "start_fail"))

    def stop(self):
        if self.proc.state() != QProcess.NotRunning:
            self.proc.terminate()
            self.proc.waitForFinished(5000)
        self.on_finished()

    def context_menu(self, pos):
        from PySide6.QtWidgets import QMenu
        item = self.list.itemAt(pos)
        if not item:
            return
        game = item.data(Qt.UserRole)
        menu = QMenu(self)
        running = self.proc.state() != QProcess.NotRunning
        act_play = menu.addAction(tr(self.front, "play"))
        act_play.setEnabled(not running)
        act_play.triggered.connect(self.play)
        act_stop = menu.addAction(tr(self.front, "stop"))
        act_stop.setEnabled(running)
        act_stop.triggered.connect(self.stop)
        menu.addSeparator()
        act_verify = menu.addAction(tr(self.front, "verify"))
        act_verify.triggered.connect(lambda: self.verify_game(game))
        boost = menu.addMenu(tr(self.front, "boost"))
        res_menu = boost.addMenu(tr(self.front, "res"))
        for label, w, h in [("720p", 1280, 720), ("1080p", 1920, 1080),
                            ("1440p", 2560, 1440), ("4K", 3840, 2160)]:
            a = res_menu.addAction(label)
            a.triggered.connect(lambda _c, w=w, h=h: self.quick_tweak(
                {("GPU", "internalScreenWidth"): w,
                 ("GPU", "internalScreenHeight"): h},
                f"{tr(self.front, 'res')} {w}x{h}"))
        a = boost.addAction("FSR on/off")
        a.triggered.connect(lambda: self.quick_tweak({("GPU", "fsrEnabled"): True},
                                                      "FSR"))
        a = boost.addAction("PS4 Pro on/off")
        a.triggered.connect(lambda: self.quick_tweak({("General", "isPS4Pro"): True},
                                                      "PS4 Pro"))
        act_folder = menu.addAction(tr(self.front, "open_folder"))
        act_folder.triggered.connect(
            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(game["dir"])))
        act_addon = menu.addAction(tr(self.front, "addon_folder"))
        act_addon.triggered.connect(lambda: self.open_addons())
        menu.addSeparator()
        act_del = menu.addAction(tr(self.front, "delete_rom"))
        act_del.triggered.connect(lambda: self.delete_rom(game))
        menu.exec(self.list.viewport().mapToGlobal(pos))

    def quick_tweak(self, changes, label):
        import shutil
        try:
            shutil.copy2(SHAD_CONFIG, SHAD_CONFIG + ".backup-front")
            apply_to_shad_config(dict(changes))
        except (OSError, TypeError) as e:
            QMessageBox.warning(self, "shadps4-front",
                                f"{tr(self.front, 'apply_fail')} {e}")
            return
        QMessageBox.information(self, "shadps4-front",
                                f"{label}: {tr(self.front, 'applied')} "
                                "(global, vale p/ todos os jogos)")

    def open_addons(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(
            os.path.expanduser("~/.local/share/shadPS4/addcont")))

    def verify_game(self, game):
        total = zeros = 0
        for _root, _dirs, files in os.walk(game["dir"]):
            for fn in files:
                total += 1
                try:
                    if os.path.getsize(os.path.join(_root, fn)) == 0:
                        zeros += 1
                except OSError:
                    zeros += 1
        eb = os.path.join(game["dir"], "eboot.bin")
        eb_ok = os.path.isfile(eb) and os.path.getsize(eb) > 0
        sfo = read_sfo(os.path.join(game["dir"], "sce_sys", "param.sfo"))
        lines = [f"{tr(self.front, 'verify_title')}: {game['title']}",
                 f"eboot.bin: {'OK' if eb_ok else 'ZERADO/AUSENTE'}",
                 f"param.sfo: {'OK' if sfo.get('title') else 'ilegível'}",
                 f"arquivos: {total}, zerados: {zeros}"]
        if zeros:
            lines.append(tr(self.front, "verify_damaged"))
        else:
            lines.append(tr(self.front, "verify_ok"))
        QMessageBox.information(self, "shadps4-front", "\n".join(lines))

    def delete_rom(self, game):
        r1 = QMessageBox.question(
            self, "shadps4-front",
            f"{tr(self.front, 'delete_confirm')}\n{game['title']}\n{game['dir']}",
            QMessageBox.Yes | QMessageBox.No)
        if r1 != QMessageBox.Yes:
            return
        r2 = QMessageBox.question(
            self, "shadps4-front", tr(self.front, "delete_confirm2"),
            QMessageBox.Yes | QMessageBox.No)
        if r2 != QMessageBox.Yes:
            return
        trash = os.path.expanduser("~/.local/share/Trash/files")
        os.makedirs(trash, exist_ok=True)
        dest = os.path.join(trash, os.path.basename(game["dir"]))
        if os.path.exists(dest):
            import time
            dest += f".{int(time.time())}"
        try:
            os.rename(game["dir"], dest)
        except OSError as e:
            QMessageBox.warning(self, "shadps4-front", str(e))
            return
        with open(os.path.expanduser("~/.local/share/Trash/info/") +
                  os.path.basename(dest) + ".trashinfo", "w") as f:
            import datetime
            f.write("[Trash Info]\nPath=" + game["dir"] + "\nDeletionDate=" +
                    datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + "\n")
        self.reload_library()

    def on_finished(self):
        self.stop_btn.setEnabled(False)
        self.status.setText(tr(self.front, "ready"))
        self.show()
        self.raise_()
        self.activateWindow()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(MODERN_QSS)
    win = Main()
    win.show()
    sys.exit(app.exec())
