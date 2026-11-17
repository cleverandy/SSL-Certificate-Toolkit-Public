"""SSL Certificate Toolkit — PySide6 / Qt, Fluent-inspired Windows GUI.

GUI only: cryptographic operations live in core.py. All operations are local.
"""
from __future__ import annotations

import sys
import os
import traceback
from datetime import datetime
from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt, Signal, QUrl, QSettings
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMainWindow,
    QMessageBox, QPlainTextEdit, QPushButton, QScrollArea, QSizePolicy,
    QStackedWidget, QTableWidget, QTableWidgetItem, QToolButton,
    QVBoxLayout, QWidget, QAbstractItemView, QHeaderView,
)

import core


APP_VERSION = "3.2.0"
APP_AUTHOR = "cleverandy"
APP_LICENSE = "MIT License"
APP_REPO_URL = "https://github.com/cleverandy/SSL-Certificate-Toolkit-Public"

CERT_FILTER = "Certificates (*.crt *.cer *.pem *.txt *.der);;All files (*)"
KEY_FILTER = "Private keys (*.key *.pem *.txt);;All files (*)"
CSR_FILTER = "CSR files (*.csr *.pem *.txt);;All files (*)"


LIGHT = {
    "bg": "#F5F7FB", "surface": "#FFFFFF", "side": "#EDF2F9",
    "text": "#16243A", "muted": "#68788F", "line": "#DFE6F0",
    "field": "#FFFFFF", "brand": "#175CD3", "hover": "#E6EEFB",
    "selected": "#DCE9FF", "code": "#F6F8FC", "danger": "#B42318",
}
DARK = {
    "bg": "#101722", "surface": "#1B2635", "side": "#15202E",
    "text": "#E8EFF9", "muted": "#9BAAC0", "line": "#344459",
    "field": "#243246", "brand": "#80AAFF", "hover": "#2C3E58",
    "selected": "#304A70", "code": "#131D2B", "danger": "#FF9A91",
}


def qt_style(dark: bool) -> str:
    c = DARK if dark else LIGHT
    check_image = (Path(__file__).resolve().parent / "assets" / "check_white.png").as_posix()
    return f"""
    QWidget {{font-family: 'Segoe UI', 'Microsoft JhengHei UI', sans-serif;
             color: {c['text']}; font-size: 10pt;}}
    QMainWindow, QWidget#central, QScrollArea#mainScroll, QWidget#page {{background: {c['bg']};}}
    QWidget#sidebar {{background: {c['side']}; border-right: 1px solid {c['line']};}}
    QFrame#card {{background: {c['surface']}; border: 1px solid {c['line']}; border-radius: 14px;}}
    QFrame#card QLabel, QFrame#card QCheckBox {{background: transparent;}}
    QLabel#appTitle {{font-size: 14pt; font-weight: 700;}}
    QLabel#pageTitle {{font-size: 22pt; font-weight: 700;}}
    QLabel#sectionTitle {{font-size: 12pt; font-weight: 650;}}
    QLabel#muted, QLabel#hint, QLabel#footer {{color: {c['muted']};}}
    QLabel#hint {{font-size: 9pt;}}
    QLabel#kicker {{color: {c['brand']}; font-size: 9pt; font-weight: 700;}}
    QLabel#value {{font-size: 11pt; font-weight: 600;}}
    QLineEdit, QComboBox, QPlainTextEdit, QListWidget, QTableWidget {{
        background: {c['field']}; border: 1px solid {c['line']}; border-radius: 8px;
        padding: 8px; selection-background-color: {c['selected']};
    }}
    QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus {{border: 1px solid {c['brand']};}}
    QComboBox QAbstractItemView {{background: {c['field']}; selection-background-color: {c['selected']};}}
    QPushButton, QToolButton {{background: {c['surface']}; border: 1px solid {c['line']};
         border-radius: 8px; padding: 9px 14px; font-weight: 500;}}
    QPushButton:hover, QToolButton:hover {{background: {c['hover']};}}
    QPushButton:disabled {{color: {c['muted']};}}
    QPushButton#primary {{background: {c['brand']}; color: {'#0D1829' if dark else '#FFFFFF'};
         border: 1px solid {c['brand']}; font-weight: 700; padding: 11px 18px;}}
    QPushButton#primary:hover {{background: {'#A2C1FF' if dark else '#0F4DBE'};}}
    QPushButton#nav {{background: transparent; border: none; text-align: left;
         padding: 13px 15px; border-radius: 10px; font-weight: 500;}}
    QPushButton#nav:hover {{background: {c['hover']};}}
    QPushButton#nav:checked {{background: {c['selected']}; color: {c['brand']}; font-weight: 700;}}
    QToolButton#disclosure {{background: transparent; border: none; font-weight: 600;
         text-align: left; padding: 10px 2px;}}
    QToolButton#disclosure:hover {{background: {c['hover']};}}
    QFrame#divider {{background: {c['line']}; border: none; max-height: 1px;}}
    QPlainTextEdit#code {{font-family: Consolas, 'Cascadia Mono', monospace;
         font-size: 10pt; background: {c['code']}; border-radius: 9px;}}
    QTableWidget {{gridline-color: {c['line']};}}
    QHeaderView::section {{background: {c['side']}; border: none;
         padding: 9px; font-weight: 600; color: {c['muted']};}}
    QCheckBox {{spacing: 9px; color: {c['text']}; min-height: 25px;}}
    QCheckBox::indicator {{width: 17px; height: 17px; border: 2px solid {'#9EBBDD' if dark else '#8598B1'};
        border-radius: 4px; background: {'#2A3C53' if dark else '#FFFFFF'};}}
    QCheckBox::indicator:hover {{border: 2px solid {c['brand']};}}
    QCheckBox::indicator:checked {{border: 2px solid {c['brand']};
        background: {c['brand']}; image: url('{check_image}');}}
    QCheckBox::indicator:disabled {{border-color: {c['line']}; background: {c['surface']};}}
    QScrollArea {{border: none;}}
    QScrollBar:vertical {{background: transparent; width: 9px;}}
    QScrollBar::handle:vertical {{background: {c['line']}; border-radius: 4px; min-height: 24px;}}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{height: 0;}}
    QStatusBar {{background: {c['surface']}; border-top: 1px solid {c['line']};
         color: {c['muted']};}}
    """


def label(text: str = "", kind: str = "") -> QLabel:
    out = QLabel(text)
    if kind:
        out.setObjectName(kind)
    out.setWordWrap(True)
    out.setTextFormat(Qt.TextFormat.PlainText)
    return out


def button(text: str, fn: Callable, *, primary: bool = False) -> QPushButton:
    b = QPushButton(text)
    if primary:
        b.setObjectName("primary")
    b.clicked.connect(fn)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    return b


def row(*widgets: QWidget, stretch: bool = False) -> QHBoxLayout:
    result = QHBoxLayout()
    result.setSpacing(10)
    for w in widgets:
        result.addWidget(w)
    if stretch:
        result.addStretch(1)
    return result


def card(parent_layout: QVBoxLayout | QHBoxLayout, *, spacing: int = 14) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(22, 20, 22, 20)
    layout.setSpacing(spacing)
    parent_layout.addWidget(frame)
    return frame, layout


def horizontal_line() -> QFrame:
    result = QFrame()
    result.setObjectName("divider")
    result.setFrameShape(QFrame.Shape.HLine)
    return result


def small_code(value: str = "", *, lines: int = 13) -> QPlainTextEdit:
    w = QPlainTextEdit()
    w.setObjectName("code")
    w.setReadOnly(True)
    w.setPlainText(value)
    w.setMinimumHeight(lines * 20)
    return w


def form_field(name: str, widget: QWidget, parent: QVBoxLayout, hint: str = "") -> None:
    parent.addWidget(label(name))
    parent.addWidget(widget)
    if hint:
        parent.addWidget(label(hint, "hint"))


class DialogDirectoryTracker:
    """Persist most recently used folder across all Browse dialogs and app runs."""

    def __init__(self, fallback: str | Path):
        self.settings = QSettings("SSLToolkit", "SSL Certificate Toolkit")
        self.fallback = Path(fallback)
        saved = self.settings.value("dialogs/last_directory", "", type=str)
        self.last_folder = Path(saved) if saved and Path(saved).is_dir() else self.fallback

    def initial(self, current_path: str = "") -> str:
        current = Path(current_path).expanduser() if current_path.strip() else None
        if current is not None and current.is_file():
            return str(current.parent)
        if self.last_folder.is_dir():
            return str(self.last_folder)
        if current is not None and current.is_dir():
            return str(current)
        return str(self.fallback if self.fallback.is_dir() else Path.home())

    def remember(self, chosen: str) -> None:
        target = Path(chosen).expanduser()
        folder = target if target.is_dir() else target.parent
        if folder.is_dir():
            self.last_folder = folder
            self.settings.setValue("dialogs/last_directory", str(folder))


def file_field(title: str, filter_text: str, parent: QVBoxLayout,
               *, optional: bool = False,
               tracker: DialogDirectoryTracker | None = None) -> tuple[QLineEdit, QPushButton]:
    parent.addWidget(label(title + (" · optional" if optional else "")))
    field = QLineEdit()
    field.setPlaceholderText("Choose a file…")
    browse = QPushButton("Browse")
    def choose():
        initial = tracker.initial(field.text()) if tracker else str(Path.home())
        path, _ = QFileDialog.getOpenFileName(field, title, initial, filter_text)
        if path:
            field.setText(path)
            if tracker:
                tracker.remember(path)
    browse.clicked.connect(choose)
    line = QHBoxLayout()
    line.addWidget(field, 1)
    line.addWidget(browse)
    parent.addLayout(line)
    return field, browse


class Collapsible(QFrame):
    """Focusable expandable section; hides advanced content until requested."""
    def __init__(self, title: str, summary: str = "", open_by_default: bool = False):
        super().__init__()
        self.setObjectName("card")
        self._is_open = open_by_default
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 12, 20, 16)
        root.setSpacing(5)
        self.toggle = QToolButton()
        self.toggle.setObjectName("disclosure")
        self.toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        self.toggle.setCheckable(True)
        self.toggle.setChecked(open_by_default)
        self.toggle.clicked.connect(self.set_open)
        self.title = title
        self.summary = summary
        root.addWidget(self.toggle)
        self.content = QWidget()
        self.inner = QVBoxLayout(self.content)
        self.inner.setContentsMargins(3, 6, 3, 2)
        self.inner.setSpacing(12)
        root.addWidget(self.content)
        self.set_open(open_by_default)

    def set_open(self, state: bool):
        self._is_open = bool(state)
        self.toggle.setChecked(self._is_open)
        self.toggle.setText(("▾  " if state else "▸  ") + self.title + ("" if state or not self.summary else f"     ·     {self.summary}"))
        self.content.setVisible(self._is_open)


class FileDrop(QFrame):
    files_added = Signal(list)

    def __init__(self, heading: str, detail: str,
                 tracker: DialogDirectoryTracker | None = None):
        super().__init__()
        self.setObjectName("card")
        self.tracker = tracker
        self.setAcceptDrops(True)
        self.setMinimumHeight(122)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 14, 20, 14)
        layout.setSpacing(8)
        layout.addWidget(label(heading, "sectionTitle"))
        layout.addWidget(label(detail, "muted"))
        choose = button("+ Select files", self.choose_files)
        choose.setMaximumWidth(150)
        layout.addWidget(choose)

    def choose_files(self):
        initial = self.tracker.initial() if self.tracker else str(Path.home())
        paths, _ = QFileDialog.getOpenFileNames(self, "Import certificate files", initial, CERT_FILTER)
        if paths:
            if self.tracker:
                self.tracker.remember(paths[0])
            self.files_added.emit(paths)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() and any(x.isLocalFile() for x in event.mimeData().urls()):
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [x.toLocalFile() for x in event.mimeData().urls() if x.isLocalFile()]
        if paths:
            if self.tracker:
                self.tracker.remember(paths[0])
            self.files_added.emit(paths)
            event.acceptProposedAction()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SSL Certificate Toolkit · v3.2")
        self.resize(1260, 850)
        self.setMinimumSize(900, 680)
        self.dark = False
        self.csr_data = b""
        self.generated_key_data = b""
        self.imported: list[core.ImportedCert] = []
        self.last_bundle_pem = b""
        self.last_bundle_pfx = b""
        self.desktop = str(core.desktop_path())
        self.dialog_paths = DialogDirectoryTracker(self.desktop)
        self.last_saved_csr: Path | None = None
        self.last_saved_key: Path | None = None
        self.last_saved_folder: Path | None = None

        self.main = QWidget()
        self.main.setObjectName("central")
        self.setCentralWidget(self.main)
        shell = QHBoxLayout(self.main)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(244)
        shell.addWidget(self.sidebar)
        sidenav = QVBoxLayout(self.sidebar)
        sidenav.setContentsMargins(18, 24, 18, 18)
        sidenav.setSpacing(7)
        sidenav.addWidget(label("◈  SSL Toolkit", "appTitle"))
        sidenav.addWidget(label("CERTIFICATE WORKSPACE", "kicker"))
        sidenav.addSpacing(28)

        self.nav_buttons: list[QPushButton] = []
        for name, idx in (("▤   Generate CSR", 0), ("◫   Certificate Viewer", 2), ("▦   PEM / PFX Builder", 3), ("ⓘ   About", 4)):
            b = QPushButton(name)
            b.setObjectName("nav")
            b.setCheckable(True)
            b.setMinimumHeight(48)
            b.clicked.connect(lambda _checked=False, n=idx: self.navigate(n))
            sidenav.addWidget(b)
            self.nav_buttons.append(b)
        sidenav.addStretch(1)
        sidenav.addWidget(horizontal_line())
        sidenav.addWidget(label("Local processing · no uploads", "hint"))
        self.theme_button = button("☾  Dark mode", self.switch_theme)
        sidenav.addWidget(self.theme_button)
        sidenav.addWidget(label("v3.2.0  •  PySide6", "footer"))
        sidenav.addWidget(label("Developed by cleverandy", "footer"))

        self.pages = QStackedWidget()
        shell.addWidget(self.pages, 1)
        self.gen_page = self._page()
        self.result_page = self._page()
        self.inspect_page = self._page()
        self.bundle_page = self._page()
        self.about_page = self._page()
        self._build_generator()
        self._build_results()
        self._build_inspector()
        self._build_bundle_page()
        self._build_about_page()
        self.apply_theme()
        self.navigate(0)
        self.statusBar().showMessage("Ready · cryptographic operations run on this computer")
        self._update_generator()

    def _page(self) -> QVBoxLayout:
        scroll = QScrollArea()
        scroll.setObjectName("mainScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        content.setObjectName("page")
        content.setMinimumWidth(545)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(38, 28, 38, 36)
        layout.setSpacing(16)
        scroll.setWidget(content)
        self.pages.addWidget(scroll)
        return layout

    def _heading(self, parent: QVBoxLayout, kicker: str, title: str, desc: str) -> None:
        parent.addWidget(label(kicker.upper(), "kicker"))
        parent.addWidget(label(title, "pageTitle"))
        parent.addWidget(label(desc, "muted"))
        parent.addSpacing(6)

    def switch_theme(self):
        self.dark = not self.dark
        self.apply_theme()

    def apply_theme(self):
        QApplication.instance().setStyleSheet(qt_style(self.dark))
        self.theme_button.setText("☀  Light mode" if self.dark else "☾  Dark mode")

    def navigate(self, page_idx: int):
        self.pages.setCurrentIndex(page_idx)
        target = 0 if page_idx in (0, 1) else (1 if page_idx == 2 else (2 if page_idx == 3 else 3))
        for i, b in enumerate(self.nav_buttons):
            b.setChecked(i == target)
        scroll = self.pages.currentWidget()
        if isinstance(scroll, QScrollArea):
            scroll.verticalScrollBar().setValue(0)

    def _build_about_page(self) -> None:
        """Show accurate authorship, license, capabilities and limitations."""
        p = self.about_page
        self._heading(
            p, "ABOUT THIS APP", "SSL Certificate Toolkit",
            "A practical Windows utility for creating, inspecting and packaging SSL/TLS certificate files.",
        )

        _, details = card(p)
        details.addWidget(label("APPLICATION INFORMATION", "kicker"))
        for name, value in (
            ("Version", f"{APP_VERSION} — Generic Edition"),
            ("Author / Developer", APP_AUTHOR),
            ("License", APP_LICENSE),
            ("Platform", "Windows · Python / PySide6"),
            ("Processing", "Local only — no cloud upload"),
        ):
            details.addWidget(label(name, "hint"))
            details.addWidget(label(value, "value"))
        repo_link = button("View source on GitHub ↗", lambda: QDesktopServices.openUrl(QUrl(APP_REPO_URL)))
        repo_link.setToolTip(APP_REPO_URL)
        details.addWidget(repo_link)

        _, overview = card(p)
        overview.addWidget(label("WHAT THIS TOOL DOES", "sectionTitle"))
        overview.addWidget(label(
            "SSL Certificate Toolkit brings common SSL/TLS certificate tasks into one desktop workspace. "
            "Generate a certificate signing request (CSR) and private key, inspect certificate details "
            "and validity dates, check CSR/certificate/private-key matching, and assemble PEM certificate "
            "chains or password-protected PFX files. The interface is designed to simplify routine "
            "certificate preparation without requiring command-line expertise."
        ))
        overview.addWidget(label("CAPABILITIES", "sectionTitle"))
        overview.addWidget(label(
            "• CSR and private key generation with editable subject and SAN entries\n"
            "• CSR, certificate and private-key inspection and matching\n"
            "• Certificate-chain analysis, PEM assembly and password-protected PFX export\n"
            "• Local file processing, plus light and dark themes"
        ))

        _, assurances = card(p)
        assurances.addWidget(label("SECURITY & CERTIFICATION", "sectionTitle"))
        assurances.addWidget(label(
            "The application processes certificate material locally and does not upload private keys "
            "or certificate files to a server. Generated private keys may be unencrypted; store them "
            "securely. Certificate checks do not replace operating-system trust validation, "
            "revocation checking or independent deployment testing."
        ))
        assurances.addWidget(label(
            "This software is not a Certificate Authority (CA), does not issue trusted certificates, "
            "and is not certified or endorsed by any CA or standards body."
        ))
        assurances.addWidget(label(
            "© 2026 cleverandy. Released under the MIT License. "
            "Third-party libraries are subject to their respective licenses.", "hint"
        ))
        p.addStretch(1)

    def _copy(self, text: str, name: str) -> None:
        if not text:
            self._notify("warning", "Nothing to copy", f"No {name} is available.")
            return
        QApplication.clipboard().setText(text)
        self.statusBar().showMessage(f"{name} copied to clipboard", 5000)

    def _notify(self, level: str, title: str, message: str) -> QMessageBox.StandardButton:
        """Use an explicit theme on modal dialogs (Windows native palette may differ)."""
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(str(message))
        box.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        box.setIcon({
            "critical": QMessageBox.Icon.Critical,
            "warning": QMessageBox.Icon.Warning,
            "information": QMessageBox.Icon.Information,
        }[level])
        box.setStandardButtons(QMessageBox.StandardButton.Ok)
        return self._exec_message_box(box)

    def _ask(self, title: str, message: str) -> bool:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle(title)
        box.setText(str(message))
        box.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.No)
        return self._exec_message_box(box) == QMessageBox.StandardButton.Yes

    def _exec_message_box(self, box: QMessageBox) -> QMessageBox.StandardButton:
        c = DARK if self.dark else LIGHT
        box.setStyleSheet(f"""
            QMessageBox {{ background-color: {c['surface']}; color: {c['text']}; }}
            QMessageBox QLabel {{ color: {c['text']}; background: transparent; font-size: 10pt; }}
            QMessageBox QPushButton {{ background-color: {c['field']}; color: {c['text']};
                border: 1px solid {c['line']}; border-radius: 7px;
                min-width: 76px; padding: 8px 14px; }}
            QMessageBox QPushButton:hover {{ background-color: {c['hover']}; }}
            QMessageBox QPushButton:focus {{ border: 2px solid {c['brand']}; }}
        """)
        return QMessageBox.StandardButton(box.exec())

    def _error(self, title: str, err: Exception | str):
        self._notify("critical", title, str(err))
        self.statusBar().showMessage(f"{title}: {err}", 7000)

    def _folder_picker(self, field: QLineEdit):
        path = QFileDialog.getExistingDirectory(self, "Select base output folder", self.dialog_paths.initial(field.text()))
        if path:
            self.dialog_paths.remember(path)
            field.setText(path)

    def _write(self, path: Path, outputs: dict[str, bytes]) -> bool:
        existing = [n for n in outputs if (path / n).exists()]
        if existing:
            prompt = "Files already exist. Overwrite?\n\n" + "\n".join(str(path / n) for n in existing)
            if not self._ask("Overwrite existing files?", prompt):
                return False
        core.safe_write_files(path, outputs, overwrite=True)
        return True

    def _build_generator(self):
        p = self.gen_page
        self._heading(p, "Certificate tools / 01", "Generate CSR", "Create a new CSR and private key with editable subject fields.")

        _, main = card(p)
        main.addWidget(label("Primary domain", "sectionTitle"))
        self.primary = QLineEdit("www.example.com")
        self.primary.setPlaceholderText("e.g. www.example.com")
        main.addWidget(self.primary)
        self.auto_www = QCheckBox("Include www / non-www variant automatically")
        self.auto_www.setChecked(True)
        main.addWidget(self.auto_www)
        main.addSpacing(6)
        header = row(label("Additional DNS names", "sectionTitle"))
        main.addLayout(header)
        dns_line = QHBoxLayout()
        self.dns_entry = QLineEdit()
        self.dns_entry.setPlaceholderText("e.g. portal.example.com")
        self.dns_entry.returnPressed.connect(self.add_dns)
        dns_line.addWidget(self.dns_entry, 1)
        dns_line.addWidget(button("+ Add", self.add_dns))
        main.addLayout(dns_line)
        self.extra_sans = QListWidget()
        self.extra_sans.setMaximumHeight(104)
        self.extra_sans.hide()
        main.addWidget(self.extra_sans)
        self.remove_dns_btn = button("Remove selected DNS", self.remove_dns)
        self.remove_dns_btn.hide()
        main.addWidget(self.remove_dns_btn, 0, Qt.AlignmentFlag.AlignLeft)
        main.addWidget(label("SAN preview", "hint"))
        self.san_preview = label("", "muted")
        main.addWidget(self.san_preview)

        self.subject_block = Collapsible("Certificate Subject", "editable defaults")
        p.addWidget(self.subject_block)
        self.fields = {}
        for name, key in (("Country (C)", "C"), ("State / Province (ST)", "ST"),
                          ("City / Locality (L)", "L"), ("Organization (O)", "O"),
                          ("Organizational Unit (OU)", "OU")):
            input_ = QLineEdit(core.DEFAULT_SUBJECT[key])
            self.fields[key] = input_
            form_field(name, input_, self.subject_block.inner)

        self.key_block = Collapsible("Key Settings", "RSA · 2048-bit")
        p.addWidget(self.key_block)
        self.key_kind = QComboBox()
        self.key_kind.addItems(["RSA", "ECDSA"])
        self.key_param = QComboBox()
        self.key_param.addItems(["2048", "3072", "4096"])
        form_field("Algorithm", self.key_kind, self.key_block.inner)
        form_field("Key size / curve", self.key_param, self.key_block.inner)
        self.key_block.inner.addWidget(label("RSA 2048 is the default. Use larger RSA or ECDSA if the target platform supports it.", "hint"))

        self.output_block = Collapsible("Output Location", "Desktop / domain_YYYYMM")
        p.addWidget(self.output_block)
        self.gen_base = QLineEdit(self.desktop)
        output_path = QHBoxLayout()
        output_path.addWidget(self.gen_base, 1)
        output_path.addWidget(button("Browse", lambda: self._folder_picker(self.gen_base)))
        self.output_block.inner.addWidget(label("Base folder"))
        self.output_block.inner.addLayout(output_path)
        self.gen_folder_preview = label("", "hint")
        self.output_block.inner.addWidget(self.gen_folder_preview)
        self.save_on_generate = QCheckBox("Save .csr and .key to the domain folder")
        self.save_on_generate.setChecked(True)
        self.output_block.inner.addWidget(self.save_on_generate)

        _, footer = card(p)
        actions = QHBoxLayout()
        actions.addWidget(label("Private key stays local. Files are saved to a dedicated folder.", "hint"), 1)
        actions.addWidget(button("Generate CSR & Key", self._generate, primary=True))
        footer.addLayout(actions)
        p.addStretch(1)

        self.primary.textChanged.connect(self._update_generator)
        self.auto_www.toggled.connect(self._update_generator)
        self.gen_base.textChanged.connect(self._update_generator)
        self.key_kind.currentTextChanged.connect(self._key_type_changed)
        self.key_param.currentTextChanged.connect(self._update_generator)
        for w in self.fields.values():
            w.textChanged.connect(self._update_generator)

    def add_dns(self):
        value = self.dns_entry.text().strip()
        if not value:
            return
        try:
            value = core.normalize_dns(value)
        except ValueError as exc:
            self._error("Invalid DNS name", exc)
            return
        if not self.extra_sans.findItems(value, Qt.MatchFlag.MatchExactly):
            self.extra_sans.addItem(value)
        self.extra_sans.show()
        self.remove_dns_btn.show()
        self.dns_entry.clear()
        self._update_generator()

    def remove_dns(self):
        for item in self.extra_sans.selectedItems():
            self.extra_sans.takeItem(self.extra_sans.row(item))
        if self.extra_sans.count() == 0:
            self.extra_sans.hide()
            self.remove_dns_btn.hide()
        self._update_generator()

    def _extra_names(self) -> list[str]:
        return [self.extra_sans.item(i).text() for i in range(self.extra_sans.count())]

    def _key_type_changed(self, kind: str):
        self.key_param.clear()
        self.key_param.addItems(["2048", "3072", "4096"] if kind == "RSA" else ["P-256", "P-384"])
        self._update_generator()

    def _update_generator(self):
        if not hasattr(self, "san_preview"):
            return
        kind = self.key_kind.currentText()
        self.key_block.summary = f"{kind} · {self.key_param.currentText()}"
        self.key_block.set_open(self.key_block._is_open)
        try:
            primary = self.primary.text()
            sans = core.san_names(primary, self._extra_names(), self.auto_www.isChecked())
            folder = core.output_directory(self.gen_base.text(), primary)
            command = core.openssl_command({k: v.text() for k, v in self.fields.items()}, primary,
                                           self._extra_names(), self.auto_www.isChecked(),
                                           kind, self.key_param.currentText(), core.output_stem(primary))
            self.san_preview.setText("  •  ".join(sans))
            self.gen_folder_preview.setText(str(folder))
            self.pending_command = command
        except Exception as exc:
            self.san_preview.setText(f"Enter a valid domain: {exc}")
            self.gen_folder_preview.setText("Folder will be created automatically.")
            self.pending_command = "Complete the domain and settings to generate the Linux OpenSSL command."

    def _generate(self):
        try:
            if not self.gen_base.text().strip():
                raise ValueError("Choose a base output directory to avoid scattering output files.")
            csr, key = core.generate_csr({k: w.text() for k, w in self.fields.items()},
                                         self.primary.text(), self._extra_names(), self.auto_www.isChecked(),
                                         self.key_kind.currentText(), self.key_param.currentText())
            self.csr_data, self.generated_key_data = csr, key
            self.csr_view.setPlainText(csr.decode("ascii"))
            self.command_view.setPlainText(self.pending_command)
            self.key_visible.setChecked(False)
            self._set_key_visibility()
            self._result_tab(0)
            self.saved_path.setText("Generated locally. No files saved.")
            self.last_saved_csr = None
            self.last_saved_key = None
            self.last_saved_folder = None
            if self.save_on_generate.isChecked():
                directory = core.output_directory(self.gen_base.text(), self.primary.text())
                stem = core.output_stem(self.primary.text())
                if self._write(directory, {stem + ".csr": csr, stem + ".key": key}):
                    self.last_saved_csr = directory / (stem + ".csr")
                    self.last_saved_key = directory / (stem + ".key")
                    self.last_saved_folder = directory
                    self.dialog_paths.remember(str(directory))
                    self.saved_path.setText("Saved to  " + str(directory))
            self.navigate(1)
            self.statusBar().showMessage("CSR & private key generated", 6500)
        except Exception as exc:
            self._error("CSR generation failed", exc)

    def _build_results(self):
        p = self.result_page
        back = button("←  Back to settings", lambda: self.navigate(0))
        back.setMaximumWidth(190)
        p.addWidget(back)
        self._heading(p, "Certificate tools / 01", "Generation complete", "Review your CSR, private key, and Linux OpenSSL command.")
        _, summary = card(p)
        summary.addWidget(label("Output", "sectionTitle"))
        self.saved_path = label("", "muted")
        summary.addWidget(self.saved_path)
        summary.addWidget(button("Verify CSR / Key in Certificate Viewer", self._verify_generated))

        controls = QHBoxLayout()
        self.result_buttons = []
        for title, index in (("CSR", 0), ("Linux command", 1), ("Private key", 2)):
            b = QPushButton(title)
            b.setCheckable(True)
            b.clicked.connect(lambda _checked=False, n=index: self._result_tab(n))
            self.result_buttons.append(b)
            controls.addWidget(b)
        controls.addStretch(1)
        p.addLayout(controls)
        self.result_stack = QStackedWidget()
        p.addWidget(self.result_stack)

        csr_panel = QWidget()
        csr_layout = QVBoxLayout(csr_panel)
        csr_layout.setContentsMargins(0, 0, 0, 0)
        self.csr_view = small_code(lines=18)
        csr_layout.addWidget(self.csr_view)
        csr_layout.addLayout(row(button("Copy CSR", lambda: self._copy(self.csr_view.toPlainText(), "CSR")),
                                button("Save CSR As…", lambda: self._save_generated_as("csr")), stretch=True))
        self.result_stack.addWidget(csr_panel)

        cmd_panel = QWidget()
        cmd_layout = QVBoxLayout(cmd_panel)
        cmd_layout.setContentsMargins(0, 0, 0, 0)
        cmd_layout.addWidget(label("Equivalent Linux OpenSSL command (requires OpenSSL with -addext support).", "hint"))
        self.command_view = small_code(lines=17)
        cmd_layout.addWidget(self.command_view)
        cmd_layout.addLayout(row(button("Copy command", lambda: self._copy(self.command_view.toPlainText(), "OpenSSL command")), stretch=True))
        self.result_stack.addWidget(cmd_panel)

        key_panel = QWidget()
        key_layout = QVBoxLayout(key_panel)
        key_layout.setContentsMargins(0, 0, 0, 0)
        self.key_visible = QCheckBox("Reveal private key")
        self.key_visible.toggled.connect(self._set_key_visibility)
        key_layout.addWidget(self.key_visible)
        self.key_view = small_code(lines=16)
        key_layout.addWidget(self.key_view)
        key_layout.addWidget(label("Unencrypted PKCS#8 private key — keep the file protected by NTFS permissions.", "hint"))
        key_layout.addLayout(row(button("Copy key", self._copy_key),
                                button("Save key As…", lambda: self._save_generated_as("key")), stretch=True))
        self.result_stack.addWidget(key_panel)
        self._result_tab(0)
        p.addStretch(1)

    def _result_tab(self, index: int):
        self.result_stack.setCurrentIndex(index)
        for i, b in enumerate(self.result_buttons):
            b.setChecked(i == index)

    def _set_key_visibility(self):
        data = self.generated_key_data.decode("ascii") if self.generated_key_data and self.key_visible.isChecked() else "Private key is hidden. Enable ‘Reveal private key’ to display it."
        self.key_view.setPlainText(data)

    def _copy_key(self):
        if not self.generated_key_data:
            return
        if self._ask("Copy sensitive private key?", "Private keys should not remain on the clipboard. Copy anyway?"):
            self._copy(self.generated_key_data.decode("ascii"), "Private key")

    def _verify_generated(self):
        if not self.csr_data or not self.generated_key_data:
            self._notify("warning", "Nothing to inspect", "Generate a CSR and private key first.")
            return
        if self.last_saved_csr and self.last_saved_csr.is_file():
            self.inspect_csr.setText(str(self.last_saved_csr))
        if self.last_saved_key and self.last_saved_key.is_file():
            self.inspect_key.setText(str(self.last_saved_key))
        self.inspect_cert.clear()  # Quick verification is CSR/KEY only, not a stale CRT.
        self.navigate(2)
        self._inspect(use_generated=True)

    def _save_generated_as(self, extension: str):
        data = self.csr_data if extension == "csr" else self.generated_key_data
        if not data:
            self._notify("warning", "No generated data", "Generate a CSR first.")
            return
        try:
            stem = core.output_stem(self.primary.text())
            directory = core.output_directory(self.gen_base.text(), self.primary.text())
            suggest = directory / (stem + "." + extension)
            start_dir = directory if directory.is_dir() else Path(self.dialog_paths.initial())
            path, _ = QFileDialog.getSaveFileName(self, "Save " + extension.upper(), str(start_dir / suggest.name), "All files (*)")
            if path:
                output = Path(path)
                self.dialog_paths.remember(path)
                if self._write(output.parent, {output.name: data}):
                    if extension == "csr":
                        self.last_saved_csr = output
                    else:
                        self.last_saved_key = output
                    self.saved_path.setText("Saved to  " + str(output))
        except Exception as exc:
            self._error("Save failed", exc)

    def _build_inspector(self):
        p = self.inspect_page
        self._heading(p, "Certificate tools / 02", "Certificate Viewer",
                      "Verify CSR / private-key matching first; optionally inspect issued certificates.")
        _, source = card(p)
        source.addWidget(label("Load files", "sectionTitle"))
        source.addWidget(label("Choose a CSR and private key to verify they match. Add a CRT/PEM for extra comparisons.", "hint"))
        self.inspect_csr, _ = file_field("1. Certificate signing request (.csr)", CSR_FILTER, source,
                                         optional=True, tracker=self.dialog_paths)
        self.inspect_key, _ = file_field("2. Private key (.key)", KEY_FILTER, source,
                                         optional=True, tracker=self.dialog_paths)
        self.inspect_key_pass_block = Collapsible("Encrypted private key", "Passphrase if required")
        source.addWidget(self.inspect_key_pass_block)
        self.inspect_key_password = self._password()
        form_field("Existing key passphrase", self.inspect_key_password, self.inspect_key_pass_block.inner)
        self.inspect_cert, _ = file_field("3. Signed certificate (CRT / PEM)", CERT_FILTER, source,
                                          optional=True, tracker=self.dialog_paths)

        actionbar = QHBoxLayout()
        actionbar.addWidget(button("Verify / Compare", self._inspect, primary=True))
        actionbar.addWidget(button("Use generated CSR / Key", lambda: self._inspect(use_generated=True)))
        actionbar.addStretch(1)
        p.addLayout(actionbar)

        self.inspect_summary_card, summary = card(p)
        self.inspect_summary_card.hide()
        summary.addWidget(label("Verification summary", "sectionTitle"))
        self.inspect_summary = label("", "value")
        summary.addWidget(self.inspect_summary)
        self.inspect_summary_notes = label("", "muted")
        summary.addWidget(self.inspect_summary_notes)
        self.inspect_details = Collapsible("Full X.509 details", "Subject, SAN, signature, expiry and matching")
        p.addWidget(self.inspect_details)
        self.inspect_details.hide()
        self.inspect_text = small_code(lines=21)
        self.inspect_details.inner.addWidget(self.inspect_text)
        p.addStretch(1)

    @staticmethod
    def _password() -> QLineEdit:
        field = QLineEdit()
        field.setEchoMode(QLineEdit.EchoMode.Password)
        return field

    @staticmethod
    def _required_file(raw_path: str, title: str) -> Path:
        path = Path(raw_path.strip().strip('"')).expanduser()
        if not path.is_file():
            raise FileNotFoundError(f"{title} file not found:\n{path}\n\nClick Browse to select an existing file.")
        return path

    def _inspect(self, *, use_generated: bool = False):
        try:
            csr = None
            cert = None
            key = None
            certs = []
            if use_generated:
                if not self.csr_data or not self.generated_key_data:
                    raise ValueError("There is no generated CSR / key yet. Generate one first.")
                csr = core.parse_csr(self.csr_data)
                key = core.load_key(self.generated_key_data)
            elif self.inspect_csr.text().strip():
                csr = core.load_csr(self._required_file(self.inspect_csr.text(), "CSR"))
            if self.inspect_cert.text().strip():
                certs = core.parse_certificates(self._required_file(self.inspect_cert.text(), "Certificate").read_bytes())
                cert = next((c for c in certs if not core.is_ca(c)), certs[0])
            if not use_generated and self.inspect_key.text().strip():
                key = core.load_key(self._required_file(self.inspect_key.text(), "Private key").read_bytes(),
                                    self.inspect_key_password.text())
            if csr is None and cert is None:
                raise ValueError("Select a CSR and/or signed certificate first.")

            detail = []
            summary = []
            notes = []
            if csr:
                detail.extend(["=== CSR ===", core.csr_report(csr), ""])
                summary.append("CSR signature: " + ("VALID" if csr.is_signature_valid else "INVALID"))
                if not csr.is_signature_valid:
                    notes.append("The CSR signature is invalid.")
            if key is not None and csr:
                matched = core.matches_private_key(csr, key)
                summary.insert(0, "CSR / KEY: " + ("MATCH" if matched else "MISMATCH"))
                detail.append("CSR / KEY MATCH: " + ("YES" if matched else "NO"))
                if not matched:
                    notes.insert(0, "The private key does not match this CSR.")
            if cert:
                status, days = core.validity_info(cert)
                summary.append("Certificate: " + status)
                notes.append("Domain: " + (core.common_name(cert.subject) or "(no CN)"))
                notes.append("Issuer: " + (core.common_name(cert.issuer) or core.display_name(cert.issuer)))
                notes.append("Issued SANs: " + (", ".join(core.get_sans(cert)) or "(none)"))
                if len(certs) > 1:
                    notes.append(f"Loaded {len(certs)} certificates; inspecting the first server certificate for matching.")
                for i, item in enumerate(certs, 1):
                    detail.extend([f"=== CERTIFICATE {i}/{len(certs)} ===", core.cert_report(item), ""])
            if csr and cert:
                compare = core.compare_csr_cert(csr, cert)
                detail.extend(["=== CSR VS CERTIFICATE ===", compare, ""])
                covered = "Required names covered: YES" in compare
                pub_matches = "CSR / CRT Public Key: MATCH" in compare
                summary.append("CSR / CRT: " + ("MATCH" if covered and pub_matches else "REVIEW NEEDED"))
                if not covered:
                    notes.append("Some requested DNS names are missing from the certificate.")
                if not pub_matches:
                    notes.append("CSR and certificate public keys differ.")
            if key is not None and cert:
                matched = core.matches_private_key(cert, key)
                summary.append("CRT / KEY: " + ("MATCH" if matched else "MISMATCH"))
                detail.append("CRT / KEY MATCH: " + ("YES" if matched else "NO"))
            detail.append("NOTE: OS/browser trust-store acceptance and revocation are not tested.")
            self.inspect_summary.setText("    |    ".join(summary))
            self.inspect_summary_notes.setText("\n".join(notes))
            self.inspect_text.setPlainText("\n".join(detail))
            self.inspect_summary_card.show()
            self.inspect_details.show()
            self.inspect_details.set_open(False)
            self.statusBar().showMessage("Inspection complete", 6000)
        except Exception as exc:
            self._error("Inspection failed", exc)

    def _build_bundle_page(self):
        p = self.bundle_page
        self._heading(p, "Certificate tools / 03", "PEM / PFX Builder", "Combine certificate files for web servers, IIS, load balancers, and other TLS deployments.")

        self.import_drop = FileDrop("Import certificate files", "Drop CRT / PEM / TXT here, or select all files in one go.\nSupports CA Bundle or separate DigiCertCA + TrustedRoot files.", tracker=self.dialog_paths)
        self.import_drop.files_added.connect(self._import_files)
        p.addWidget(self.import_drop)
        self.bundle_import_panel, data = card(p)
        self.bundle_import_panel.hide()
        upper = QHBoxLayout()
        upper.addWidget(label("Imported certificates", "sectionTitle"))
        upper.addStretch(1)
        upper.addWidget(button("Add more", self.import_drop.choose_files))
        upper.addWidget(button("Remove selected", self._remove_selected))
        upper.addWidget(button("Clear", self._clear_imported))
        data.addLayout(upper)
        self.cert_table = QTableWidget(0, 4)
        self.cert_table.setHorizontalHeaderLabels(["Source", "Subject CN", "Role", "Expires (UTC)"])
        self.cert_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.cert_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.cert_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.cert_table.verticalHeader().hide()
        self.cert_table.setMinimumHeight(185)
        self.cert_table.setMaximumHeight(260)
        headers = self.cert_table.horizontalHeader()
        headers.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        headers.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        headers.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        headers.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        data.addWidget(self.cert_table)
        role_row = QHBoxLayout()
        role_row.addWidget(label("Selected certificate role:"))
        self.role_choice = QComboBox()
        self.role_choice.addItems(["Auto", "Server", "Intermediate CA", "Trusted Root", "Ignore"])
        role_row.addWidget(self.role_choice)
        role_row.addWidget(button("Apply", self._apply_role))
        role_row.addStretch(1)
        data.addLayout(role_row)
        data.addWidget(label("Auto-detection checks the X.509 certificate structure and issuer signatures, not only filenames.", "hint"))

        self.export_block = Collapsible("Export Options", "PEM by default; optional encrypted PFX")
        p.addWidget(self.export_block)
        self.include_root = QCheckBox("Include Trusted Root in chain")
        self.include_root.setChecked(True)
        self.export_block.inner.addWidget(self.include_root)
        self.make_pfx = QCheckBox("Also create encrypted PFX (for IIS / F5)")
        self.make_pfx.setChecked(False)
        self.export_block.inner.addWidget(self.make_pfx)
        self.pfx_options = QWidget()
        pfx_box = QVBoxLayout(self.pfx_options)
        pfx_box.setContentsMargins(0, 2, 0, 2)
        pfx_box.setSpacing(11)
        self.bundle_key, _ = file_field("Matching private key (.key / .pem)", KEY_FILTER, pfx_box,
                                        tracker=self.dialog_paths)
        self.bundle_key_pass = self._password()
        form_field("Existing key passphrase, if any", self.bundle_key_pass, pfx_box)
        self.bundle_pfx_password = self._password()
        form_field("New PFX password (at least 8 characters)", self.bundle_pfx_password, pfx_box)
        self.bundle_pfx_confirm = self._password()
        form_field("Confirm PFX password", self.bundle_pfx_confirm, pfx_box)
        self.pfx_format = QComboBox()
        self.pfx_format.addItems(["AES-256 / SHA-256 (recommended)", "Legacy 3DES / SHA-1 (compatibility only)"])
        form_field("PFX encryption", self.pfx_format, pfx_box)
        pfx_box.addWidget(label("Use 3DES only when the target F5/IIS version cannot import modern AES-encrypted PFX.", "hint"))
        self.export_block.inner.addWidget(self.pfx_options)
        self.pfx_options.setVisible(False)
        self.make_pfx.toggled.connect(self.pfx_options.setVisible)
        self.bundle_base = QLineEdit(self.desktop)
        base = QHBoxLayout()
        base.addWidget(self.bundle_base, 1)
        base.addWidget(button("Browse", lambda: self._folder_picker(self.bundle_base)))
        self.export_block.inner.addWidget(label("Base output folder"))
        self.export_block.inner.addLayout(base)
        self.export_block.inner.addWidget(label("Output folder will be generated from the domain CN as domain_YYYYMM.", "hint"))

        actions = QHBoxLayout()
        self.analyze_button = button("Analyze chain", self._analyze_bundle)
        self.export_button = button("Build PEM / PFX", self._build_bundle, primary=True)
        self.analyze_button.setEnabled(False)
        self.export_button.setEnabled(False)
        actions.addWidget(self.analyze_button)
        actions.addWidget(self.export_button)
        actions.addStretch(1)
        p.addLayout(actions)

        self.bundle_result_panel, summary = card(p)
        self.bundle_result_panel.hide()
        summary.addWidget(label("Certificate chain analysis", "sectionTitle"))
        self.bundle_summary = label("", "muted")
        summary.addWidget(self.bundle_summary)
        self.bundle_details = Collapsible("Detailed validation log", "Certificate chain and export report")
        p.addWidget(self.bundle_details)
        self.bundle_details.hide()
        self.bundle_report = small_code(lines=15)
        self.bundle_details.inner.addWidget(self.bundle_report)
        p.addStretch(1)

    def _import_files(self, paths: list[str]):
        existing = {core.cert_sha(x.certificate) for x in self.imported}
        skipped = []
        added = 0
        for path in paths:
            try:
                data = Path(path).read_bytes()
                # Support mixed selections; a private key is not an X.509 certificate.
                if b"-----BEGIN " in data and b"PRIVATE KEY-----" in data and not b"-----BEGIN CERTIFICATE-----" in data:
                    self.bundle_key.setText(path)
                    skipped.append(Path(path).name + " recognized as a private key; assigned to PFX options.")
                    self.make_pfx.setChecked(True)
                    self.export_block.set_open(True)
                    continue
                certs = core.parse_certificates(data)
                for cert in certs:
                    digest = core.cert_sha(cert)
                    if digest in existing:
                        skipped.append(f"Duplicate skipped: {Path(path).name} / {core.common_name(cert.subject)}")
                        continue
                    self.imported.append(core.ImportedCert(cert, Path(path).name))
                    existing.add(digest)
                    added += 1
            except Exception as exc:
                skipped.append(f"Skipped {Path(path).name}: {exc}")
        self._populate_table()
        if self.imported:
            self.bundle_import_panel.show()
        self._set_bundle_report(f"Imported {added} unique certificate(s).", "\n".join(skipped))
        self.statusBar().showMessage(f"Imported {added} unique certificate(s)", 6500)

    def _populate_table(self):
        self.cert_table.setRowCount(len(self.imported))
        ready = bool(self.imported)
        self.analyze_button.setEnabled(ready)
        self.export_button.setEnabled(ready)
        for index, item in enumerate(self.imported):
            cert = item.certificate
            attrs = (item.filename,
                     core.common_name(cert.subject) or core.display_name(cert.subject),
                     item.guessed_role if item.role == "Auto" else item.role + " (manual)",
                     cert.not_valid_after_utc.strftime("%Y-%m-%d"))
            for col, value in enumerate(attrs):
                cell = QTableWidgetItem(value)
                cell.setToolTip(value)
                self.cert_table.setItem(index, col, cell)

    def _selected_rows(self) -> list[int]:
        return sorted({i.row() for i in self.cert_table.selectedIndexes()}, reverse=True)

    def _remove_selected(self):
        for i in self._selected_rows():
            del self.imported[i]
        self._populate_table()
        if not self.imported:
            self.bundle_import_panel.hide()
            self.bundle_result_panel.hide()
            self.bundle_details.hide()

    def _clear_imported(self):
        self.imported.clear()
        self._populate_table()
        self.bundle_import_panel.hide()
        self.bundle_result_panel.hide()
        self.bundle_details.hide()

    def _apply_role(self):
        chosen = self._selected_rows()
        if not chosen:
            self._notify("information", "Select a certificate", "Select one or more certificate rows first.")
            return
        for i in chosen:
            self.imported[i].role = self.role_choice.currentText()
        self._populate_table()
        self.statusBar().showMessage("Certificate role override applied", 5000)

    def _set_bundle_report(self, summary: str, detail: str):
        self.bundle_summary.setText(summary)
        self.bundle_report.setPlainText(detail)
        self.bundle_result_panel.show()
        self.bundle_details.show()
        self.bundle_details.set_open(False)

    def _analyze_bundle(self):
        try:
            analysis = core.analyze_chain(self.imported)
            sequence = [analysis.leaf] + analysis.ordered_chain
            title = f"{core.common_name(analysis.leaf.subject)}  ·  {len(sequence)} certificate(s) in chain"
            if analysis.warnings:
                title += f"  ·  {len(analysis.warnings)} warning(s)"
            lines = ["ORDERED CHAIN (server → intermediate → root):"]
            for index, cert in enumerate(sequence, 1):
                lines.append(f" {index}. {core.common_name(cert.subject) or core.display_name(cert.subject)} — {core.validity_info(cert)[0]}")
            lines += ["", "WARNINGS:"] + ([" • " + w for w in analysis.warnings] if analysis.warnings else [" (none)"])
            lines += ["", "Chain issuer signatures checked. Trust store / revocation not tested."]
            self._set_bundle_report(title, "\n".join(lines))
            self.statusBar().showMessage("Certificate chain analyzed", 5000)
            return analysis
        except Exception as exc:
            self._error("Chain analysis failed", exc)
            return None

    def _build_bundle(self):
        analysis = self._analyze_bundle()
        if analysis is None:
            return
        try:
            if not self.bundle_base.text().strip():
                raise ValueError("Choose a base output directory to avoid scattering output files.")
            critical = [w for w in analysis.warnings if any(x in w for x in ("EXPIRED", "NOT YET VALID", "Incomplete chain"))]
            if critical:
                message = "This certificate chain has important warnings:\n\n" + "\n".join(critical) + "\n\nExport anyway?"
                if not self._ask("Certificate chain warning", message):
                    return
            pem = core.make_pem(analysis, include_root=self.include_root.isChecked())
            pfx = None
            password = ""
            if self.make_pfx.isChecked():
                keypath = self.bundle_key.text().strip()
                if not keypath:
                    self.export_block.set_open(True)
                    raise ValueError("Choose the matching private key under Export Options to build PFX.")
                password = self.bundle_pfx_password.text()
                if len(password) < 8:
                    raise ValueError("PFX password must be at least 8 characters.")
                if password != self.bundle_pfx_confirm.text():
                    raise ValueError("PFX password confirmation does not match.")
                legacy = self.pfx_format.currentIndex() == 1
                if legacy and not self._ask(
                    "Legacy PFX encryption", "Legacy 3DES/SHA-1 is weaker than AES-256. Continue only for an incompatible older importer."
                ):
                    return
                private_key = core.load_key(Path(keypath).read_bytes(), self.bundle_key_pass.text())
                pfx = core.make_pfx(analysis, private_key, password, self.include_root.isChecked(), legacy_3des=legacy)
            report = core.validate_outputs(pem, analysis, pfx, password, self.include_root.isChecked())
            cn = core.common_name(analysis.leaf.subject)
            if not cn:
                names = core.get_sans(analysis.leaf)
                if not names:
                    raise ValueError("Server certificate has no CN or DNS SAN for output naming.")
                cn = names[0]
            stem = core.output_stem(cn)
            folder = core.output_directory(self.bundle_base.text(), cn)
            outputs = {stem + ".pem": pem, stem + "_verification.txt": (report + "\n").encode("utf-8")}
            if pfx is not None:
                outputs[stem + ".pfx"] = pfx
            if not self._write(folder, outputs):
                self.statusBar().showMessage("Export cancelled; existing files were not overwritten", 6500)
                return
            self.last_bundle_pem, self.last_bundle_pfx = pem, pfx or b""
            self._set_bundle_report(f"Export complete · {len(outputs)} verified file(s)",
                                    "OUTPUT VERIFICATION\n" + report + "\n\nSAVED TO\n" + "\n".join(str(folder / n) for n in outputs))
            self.bundle_pfx_password.clear()
            self.bundle_pfx_confirm.clear()
            self.statusBar().showMessage(f"Export complete: {folder}", 8500)
            self.dialog_paths.remember(str(folder))
            self._notify("information", "PEM / PFX created", "Generated and verified:\n" + "\n".join(str(folder / n) for n in outputs))
        except Exception as exc:
            self._error("PEM / PFX build failed", exc)


def _log_unhandled_exception(exc_type, exc_value, exc_tb):
    """Local traceback only; never log CSR/PEM/key buffers."""
    try:
        root = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "SSL_Certificate_Toolkit" / "logs"
        root.mkdir(parents=True, exist_ok=True)
        with (root / "error.log").open("a", encoding="utf-8") as f:
            f.write(f"\n[{datetime.now().isoformat(timespec='seconds')}] Unhandled exception\n")
            traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
    except OSError:
        pass
    try:
        if QApplication.instance():
            box = QMessageBox()
            box.setWindowTitle("Unexpected error")
            box.setText("An unexpected application error occurred. See the local error.log file for details.")
            box.exec()
    except Exception:
        pass


def main():
    sys.excepthook = _log_unhandled_exception
    app = QApplication(sys.argv)
    app.setApplicationName("SSL Certificate Toolkit")
    app.setOrganizationName("SSL Certificate Toolkit")
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
