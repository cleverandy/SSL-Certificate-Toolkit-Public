"""SSL Certificate Toolkit — PySide6 / Qt, Fluent-inspired Windows GUI.

GUI only: cryptographic operations live in core.py. All operations are local.
"""
from __future__ import annotations

import sys
import os
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt, Signal, QUrl, QSettings, QThread, QSize, QRectF, QLineF
from PySide6.QtGui import QDesktopServices, QFont, QGuiApplication, QIcon, QPixmap, QPainter, QPen, QColor
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMainWindow,
    QMessageBox, QPlainTextEdit, QPushButton, QScrollArea, QSizePolicy,
    QStackedWidget, QTableWidget, QTableWidgetItem, QToolButton,
    QVBoxLayout, QWidget, QAbstractItemView, QHeaderView, QSplashScreen, QProgressBar,
)

import core
import live_ssl
import watch_store
import activity_log
import website_safety
import csv
from email.message import EmailMessage
from export_picture import ExportPictureDialog


APP_VERSION = "3.4.0"
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


def vector_icon(name: str, color: str = '#536987', size: int = 20) -> QIcon:
    """Render consistent resolution-independent line icons at 2x for HiDPI."""
    scale = 3
    pix = QPixmap(size * scale, size * scale)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.scale(scale, scale)
    painter.setPen(QPen(QColor(color), 1.75, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    if name == 'certificate':
        painter.drawRoundedRect(QRectF(4, 2.5, 12, 15), 2, 2)
        painter.drawLine(7, 7, 13, 7); painter.drawLine(7, 10, 12, 10)
        painter.drawLine(7, 13, 10, 13)
    elif name == 'viewer':
        painter.drawRoundedRect(3, 3, 14, 14, 2, 2)
        painter.drawEllipse(QRectF(6.2, 6.2, 7.5, 7.5))
        painter.drawLine(13, 13, 17, 17)
    elif name == 'files':
        painter.drawRoundedRect(5, 5, 12, 12, 1.5, 1.5)
        painter.drawLine(8, 8, 14, 8); painter.drawLine(8, 11, 14, 11)
        painter.drawLine(3, 13, 3, 3); painter.drawLine(3, 3, 13, 3)
    elif name == 'shield':
        from PySide6.QtGui import QPainterPath
        path = QPainterPath()
        path.moveTo(10, 2); path.lineTo(16.5, 4.5); path.lineTo(16.5, 9.5)
        path.cubicTo(16.5, 13.5, 14, 16.2, 10, 18)
        path.cubicTo(6, 16.2, 3.5, 13.5, 3.5, 9.5)
        path.lineTo(3.5, 4.5); path.closeSubpath()
        painter.drawPath(path)
        painter.drawLine(7, 10, 9, 12); painter.drawLine(9, 12, 13.5, 7.5)
    elif name == 'info':
        painter.drawEllipse(3, 3, 14, 14)
        painter.drawPoint(10, 7); painter.drawLine(10, 10, 10, 14)
    elif name == 'chevron-right':
        painter.drawLine(8, 5, 13, 10); painter.drawLine(13, 10, 8, 15)
    elif name == 'chevron-down':
        painter.drawLine(5, 8, 10, 13); painter.drawLine(10, 13, 15, 8)
    elif name == 'monitor':
        painter.drawRoundedRect(3, 4, 14, 10, 1.3, 1.3)
        painter.drawLine(10, 14, 10, 17); painter.drawLine(7, 17, 13, 17)
    elif name == 'sun':
        painter.drawEllipse(7, 7, 6, 6)
        for a,b,c,d in [(10,2,10,5),(10,15,10,18),(2,10,5,10),(15,10,18,10),
                        (4.3,4.3,6.4,6.4),(13.6,13.6,15.7,15.7),
                        (4.3,15.7,6.4,13.6),(13.6,6.4,15.7,4.3)]:
            painter.drawLine(QLineF(a,b,c,d))
    elif name == 'moon':
        from PySide6.QtGui import QPainterPath
        path = QPainterPath()
        path.moveTo(13,3.4); path.cubicTo(5,2,2.5,9,6,14)
        path.cubicTo(9,18.2,15.3,16.5,17,11)
        path.cubicTo(14.5,13,10.7,11.6,10.2,8.6)
        path.cubicTo(9.8,6.4,11.2,4.7,13,3.4)
        painter.drawPath(path)
    painter.end()
    pix.setDevicePixelRatio(scale)
    return QIcon(pix)


def english_datetime(value: datetime, fmt: str = '%d %B %Y · %H:%M') -> str:
    """Use numeric UTC offsets; never OS-localized time zone names."""
    local = value.astimezone()
    offset = local.utcoffset()
    if offset is None:
        suffix = 'UTC'
    else:
        minutes = int(offset.total_seconds() // 60)
        sign = '+' if minutes >= 0 else '-'
        minutes = abs(minutes)
        suffix = f'UTC{sign}{minutes // 60:02d}:{minutes % 60:02d}'
    return local.strftime(fmt) + ' (' + suffix + ')'


def qt_style(dark: bool) -> str:
    c = DARK if dark else LIGHT
    check_image = (Path(__file__).resolve().parent / "assets" / "check_white.png").as_posix()
    return f"""
    QWidget {{font-family: 'Segoe UI', sans-serif;
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
    QLabel#detailValue {{font-size: 10pt; font-weight: 550;}}
    QLineEdit, QComboBox, QPlainTextEdit, QListWidget, QTableWidget {{
        background: {c['field']}; border: 1px solid {c['line']}; border-radius: 8px;
        padding: 8px; selection-background-color: {c['selected']};
    }}
    QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus {{border: 1px solid {c['brand']};}}
    QComboBox {{ min-height: 22px; padding-right: 30px; }}
    QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right;
        width: 26px; border-left: 1px solid {c['line']};
        border-top-right-radius: 8px; border-bottom-right-radius: 8px; background: {c['field']}; }}
    QComboBox::drop-down:hover {{background: {c['hover']};}}
    QComboBox::down-arrow {{image: url('{(Path(__file__).resolve().parent / 'assets' / 'chevron_down.png').as_posix()}');
        width: 12px; height: 12px;}}
    QComboBox QAbstractItemView {{border: 1px solid {c['line']}; border-radius: 6px;
        outline: none; background: {c['field']}; color: {c['text']};
        padding: 5px; selection-background-color: {c['selected']};
        selection-color: {c['text']};}}
    QComboBox QAbstractItemView::item {{min-height: 30px; padding: 6px 9px;}}
    QComboBox QAbstractItemView::item:selected {{background: {c['selected']}; color: {c['text']};}}
    QPushButton, QToolButton {{background: {c['surface']}; border: 1px solid {c['line']};
         border-radius: 8px; padding: 9px 14px; font-weight: 500;}}
    QPushButton:hover, QToolButton:hover {{background: {c['hover']};}}
    QPushButton:disabled {{color: {c['muted']};}}
    QPushButton#primary {{background: {c['brand']}; color: {'#0D1829' if dark else '#FFFFFF'};
         border: 1px solid {c['brand']}; font-weight: 700; padding: 11px 18px;}}
    QPushButton#primary:hover {{background: {'#A2C1FF' if dark else '#0F4DBE'};}}
    QToolButton#embeddedInspect {{background: {c['hover']}; border: 1px solid {c['line']};
        border-radius: 6px; font-weight: 650; padding: 5px 7px; color: {c['text']};}}
    QToolButton#embeddedInspect:hover {{border: 1px solid {c['brand']};}}
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
    QScrollBar:vertical {{background: {"#344459" if dark else "#E8EDF4"}; width: 10px; border: none; border-radius: 5px;}}
    QScrollBar::handle:vertical {{background: {"#73839A" if dark else "#A8B6C8"}; border-radius: 5px; min-height: 24px; margin: 1px;}}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{height: 0; background: none;}}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{background: none;}}
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
        self.toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toggle.setIconSize(QSize(17, 17))
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
        self.toggle.setText(self.title + ("" if state or not self.summary else f"    ·    {self.summary}"))
        self.toggle.setIcon(vector_icon('chevron-down' if state else 'chevron-right'))
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


class DomainInput(QLineEdit):
    """One-line domain input with a real embedded action on the right."""
    def __init__(self, text: str = ''):
        super().__init__(text)
        self.inspect_button = QToolButton(self)
        self.inspect_button.setObjectName('embeddedInspect')
        self.inspect_button.setText('SSL Checker')
        # Keep the action text visible; no icon-only replacement.
        self.inspect_button.setToolTip('Inspect this domain and compare its live certificate with the draft CSR')
        self.inspect_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.inspect_button.setFixedWidth(126)
        self.setTextMargins(0, 0, 135, 0)
        self.setMinimumHeight(43)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.inspect_button.move(self.width() - self.inspect_button.width() - 7,
                                 (self.height() - self.inspect_button.sizeHint().height()) // 2)


class SSLInspectWorker(QThread):
    success = Signal(object)
    failure = Signal(str)
    def __init__(self, target: str, parent=None):
        super().__init__(parent)
        self.target = target

    def run(self):
        try:
            self.success.emit(live_ssl.inspect(self.target))
        except Exception as exc:
            self.failure.emit(str(exc)[:750])


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"SSL Certificate Toolkit · v{APP_VERSION}")
        self.resize(1260, 850)
        self.setMinimumSize(900, 680)
        self.settings = QSettings('SSLToolkit', 'SSL Certificate Toolkit')
        self.theme_mode = self.settings.value('appearance/theme', 'system', type=str)
        if self.theme_mode not in ('system','light','dark'):
            self.theme_mode = 'system'
        self.dark = self._theme_is_dark()
        self.live_result = None
        self._previous_fingerprint = {}
        self.live_worker = None
        self.watch_items = watch_store.read_watchlist()
        self.watch_active = {}
        self.watch_queue = []
        self.watch_refreshing = False
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
        sidenav.addWidget(label("SSL Toolkit", "appTitle"))
        sidenav.addWidget(label("CERTIFICATE WORKSPACE", "kicker"))
        sidenav.addSpacing(28)

        self.nav_buttons: list[QPushButton] = []
        for name, idx, icon_name in (("Generate CSR", 0, 'certificate'),
                                     ("Certificate Viewer", 2, 'viewer'),
                                     ("PEM / PFX Builder", 3, 'files'),
                                     ("Live SSL Checker", 5, 'shield'),
                                     ("SSL Watch List", 6, 'shield'),
                                     ("Activity Log", 7, 'files'),
                                     ("About", 4, 'info')):
            b = QPushButton(name)
            b.setProperty('icon_name', icon_name)
            b.setIcon(vector_icon(icon_name))
            b.setIconSize(QSize(20, 20))
            b.setObjectName("nav")
            b.setCheckable(True)
            b.setMinimumHeight(48)
            b.clicked.connect(lambda _checked=False, n=idx: self.navigate(n))
            sidenav.addWidget(b)
            self.nav_buttons.append(b)
        sidenav.addStretch(1)
        sidenav.addWidget(horizontal_line())
        sidenav.addWidget(label("Local processing · no uploads", "hint"))
        sidenav.addWidget(label('Appearance', 'hint'))
        self.theme_button = QPushButton()
        self.theme_button.setIconSize(QSize(19, 19))
        self.theme_button.clicked.connect(self._theme_changed)
        self._update_theme_button()
        sidenav.addWidget(self.theme_button)
        sidenav.addWidget(label(f"v{APP_VERSION}  •  PySide6", "footer"))
        sidenav.addWidget(label("Developed by cleverandy", "footer"))

        self.pages = QStackedWidget()
        shell.addWidget(self.pages, 1)
        self.gen_page = self._page()
        self.result_page = self._page()
        self.inspect_page = self._page()
        self.bundle_page = self._page()
        self.about_page = self._page()
        self.live_page = self._page()
        self.watch_page = self._page()
        self.activity_page = self._page()
        self._build_generator()
        self._build_results()
        self._build_inspector()
        self._build_bundle_page()
        self._build_about_page()
        self._build_live_page()
        self._build_watch_page()
        self._build_activity_page()
        self.apply_theme()
        QGuiApplication.styleHints().colorSchemeChanged.connect(self._system_theme_changed)
        self.navigate(0)
        self.statusBar().showMessage("Ready · cryptographic operations run on this computer")
        self._update_generator()
        if self.settings.value("watch/refresh_on_startup", True, type=bool):
            from PySide6.QtCore import QTimer
            QTimer.singleShot(350, self.refresh_all_watch)

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

    def _theme_is_dark(self):
        if self.theme_mode == 'dark':
            return True
        if self.theme_mode == 'light':
            return False
        return QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark

    def _theme_changed(self):
        modes = ('system', 'light', 'dark')
        self.theme_mode = modes[(modes.index(self.theme_mode) + 1) % len(modes)]
        self.settings.setValue('appearance/theme', self.theme_mode)
        self._update_theme_button()
        self.dark = self._theme_is_dark()
        self.apply_theme()

    def _update_theme_button(self):
        names = {'system': ('System', 'monitor'), 'light': ('Light', 'sun'), 'dark': ('Dark', 'moon')}
        title, symbol = names[self.theme_mode]
        self.theme_button.setText(title)
        self.theme_button.setIcon(vector_icon(symbol))

    def _system_theme_changed(self, _scheme):
        if self.theme_mode == 'system':
            self.dark = self._theme_is_dark()
            self.apply_theme()

    def apply_theme(self):
        QApplication.instance().setProperty("ssl_dark", self.dark)
        QApplication.instance().setStyleSheet(qt_style(self.dark))
        # Update any already displayed SSL health labels when switching appearance.
        if getattr(self, 'live_result', None) is not None and hasattr(self, 'live_health'):
            palette = ({'valid': '#49D795', 'warning': '#FFD166', 'critical': '#FF827D'}
                       if self.dark else {'valid': '#14804A', 'warning': '#A66B12', 'critical': '#B42318'})
            color = palette[self.live_result.health]
            self.live_health.setStyleSheet('color:' + color)
            self.live_expiry.setStyleSheet('color:' + color + '; font-weight: 800;')
            self.live_remaining.setStyleSheet('color:' + color)
        ink = DARK['text'] if self.dark else LIGHT['muted']
        for b in getattr(self, 'nav_buttons', []):
            b.setIcon(vector_icon(b.property('icon_name'), ink))
        if hasattr(self, 'theme_button'):
            self._update_theme_button()
        if hasattr(self, 'watch_table'):
            self._update_watch_table()
        for section in getattr(self, '_disclosures', []):
            section.set_open(section._is_open)

    def navigate(self, page_idx: int):
        self.pages.setCurrentIndex(page_idx)
        target = {0:0,1:0,2:1,3:2,5:3,6:4,7:5,4:6}.get(page_idx, 0)
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
            ("Processing", "Local certificate/key operations; live SSL checker connects directly to chosen hosts"),
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
            "• Live TLS inspection, DNS lookup, CSR SAN comparison and picture export\n"
            "• Local file processing, plus system / light / dark appearance"
        ))

        _, assurances = card(p)
        assurances.addWidget(label("SECURITY & CERTIFICATION", "sectionTitle"))
        assurances.addWidget(label(
            "The application processes certificate material locally and does not upload private keys "
            "or certificate files to a server. The optional Live SSL Checker makes outbound DNS/TLS "
            "connections to user-specified hosts but does not download web pages. "
            "Generated private keys may be unencrypted; store them "
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
        self.primary = DomainInput("www.example.com")
        self.primary.setPlaceholderText("e.g. www.example.com")
        self.primary.inspect_button.clicked.connect(self.open_ssl_checker)
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
        self.remove_dns_btn = button("Remove", self.remove_dns)
        self.remove_dns_btn.setEnabled(False)
        dns_line.addWidget(self.remove_dns_btn)
        main.addLayout(dns_line)
        self.extra_sans = QListWidget()
        self.extra_sans.setMaximumHeight(104)
        self.extra_sans.hide()
        self.extra_sans.itemSelectionChanged.connect(self._update_remove_dns)
        main.addWidget(self.extra_sans)
        main.addWidget(label("SAN preview", "hint"))
        self.san_preview = label("", "muted")
        main.addWidget(self.san_preview)

        self.subject_block = Collapsible("Certificate Subject", "editable defaults")
        p.addWidget(self.subject_block)
        self.fields = {}
        self.remember_subject = QCheckBox('Remember these subject defaults')
        self.remember_subject.setChecked(self.settings.value('subject/remember', False, type=bool))
        for name, key in (("Country (C)", "C"), ("State / Province (ST)", "ST"),
                          ("City / Locality (L)", "L"), ("Organization (O)", "O"),
                          ("Organizational Unit (OU)", "OU")):
            initial = self.settings.value('subject/' + key, core.DEFAULT_SUBJECT[key], type=str) if self.remember_subject.isChecked() else core.DEFAULT_SUBJECT[key]
            input_ = QLineEdit(initial)
            input_.setMaxLength(128 if key != 'C' else 2)
            self.fields[key] = input_
            form_field(name, input_, self.subject_block.inner)
        self.subject_block.inner.addWidget(self.remember_subject)
        subject_actions = QHBoxLayout()
        subject_actions.addWidget(button('Save Subject Defaults', self.save_subject_defaults))
        subject_actions.addWidget(button('Reset Defaults', self.reset_subject_defaults))
        subject_actions.addStretch(1)
        self.subject_block.inner.addLayout(subject_actions)

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
            w.editingFinished.connect(self._save_subject_if_enabled)
        self.remember_subject.toggled.connect(self._remember_subject_changed)

    def _remember_subject_changed(self, checked: bool):
        self.settings.setValue('subject/remember', checked)
        if checked:
            self.save_subject_defaults(quiet=True)

    def _save_subject_if_enabled(self):
        if self.remember_subject.isChecked():
            self.save_subject_defaults(quiet=True)

    def save_subject_defaults(self, quiet: bool = False):
        try:
            values = {key: w.text().strip() for key, w in self.fields.items()}
            if len(values['C']) != 2 or not values['C'].isascii() or not values['C'].isalpha():
                raise ValueError('Country (C) must be exactly two letters.')
            for value in values.values():
                if any(ord(c) < 32 or ord(c) == 127 for c in value):
                    raise ValueError('Subject fields must not contain control characters.')
            self.settings.setValue('subject/remember', True)
            self.remember_subject.setChecked(True)
            for key, value in values.items():
                self.settings.setValue('subject/' + key, value.upper() if key == 'C' else value)
            if not quiet:
                self.statusBar().showMessage('Certificate Subject defaults saved for future sessions.', 6000)
        except ValueError as exc:
            if not quiet:
                self._error('Cannot save subject defaults', exc)

    def reset_subject_defaults(self):
        for key, widget in self.fields.items():
            widget.setText(core.DEFAULT_SUBJECT[key])
        if self.remember_subject.isChecked():
            self.save_subject_defaults(quiet=True)
        self._update_generator()

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
        self._update_remove_dns()
        self.dns_entry.clear()
        self._update_generator()

    def remove_dns(self):
        for item in self.extra_sans.selectedItems():
            self.extra_sans.takeItem(self.extra_sans.row(item))
        if self.extra_sans.count() == 0:
            self.extra_sans.hide()
        self._update_remove_dns()
        self._update_generator()

    def _update_remove_dns(self):
        self.remove_dns_btn.setEnabled(bool(self.extra_sans.selectedItems()))

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
            if self.last_saved_folder:
                activity_log.record('CSR + KEY Generated', self.primary.text(), str(self.last_saved_folder))
            else:
                activity_log.record('CSR Generated (memory only)', self.primary.text(), '')
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
                certs = core.parse_certificates(core.read_limited(self._required_file(self.inspect_cert.text(), "Certificate")))
                cert = next((c for c in certs if not core.is_ca(c)), certs[0])
            if not use_generated and self.inspect_key.text().strip():
                key = core.load_key(core.read_limited(self._required_file(self.inspect_key.text(), "Private key"), 1024*1024),
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

    # --- Live TLS certificate inspector ---
    def _build_live_page(self):
        p = self.live_page
        self.live_back = button('←  Back to Generate CSR', lambda: self.navigate(0))
        p.addWidget(self.live_back, alignment=Qt.AlignmentFlag.AlignLeft)
        self._heading(p, 'Certificate tools / 04', 'Live Certificate Inspector',
                      'Inspect the observed TLS endpoint and compare its SANs with the CSR form. No web page is downloaded.')
        _, input_box = card(p)
        input_box.addWidget(label('Website URL or hostname', 'sectionTitle'))
        query_row = QHBoxLayout()
        self.live_input = QLineEdit()
        self.live_input.setPlaceholderText('www.example.com or https://www.example.com:443')
        self.live_input.returnPressed.connect(self.run_live_check)
        query_row.addWidget(self.live_input, 1)
        self.live_inspect = button('Inspect / Recheck', self.run_live_check, primary=True)
        query_row.addWidget(self.live_inspect)
        input_box.addLayout(query_row)
        input_box.addWidget(label('Every check starts fresh DNS lookup and TLS connections; no HTTP content, cookies or downloads. CDN nodes can serve different certificates.', 'hint'))
        self.watch_add = QCheckBox('Add to SSL Watch List after successful inspection')
        input_box.addWidget(self.watch_add)
        self.live_progress = label('Enter a hostname and click Inspect.', 'muted')
        input_box.addWidget(self.live_progress)

        _, safety=card(p)
        safety.addWidget(label('WEBSITE SAFETY INDICATORS (OFFLINE)', 'sectionTitle'))
        safety.addWidget(label('Not a malware or phishing reputation check. No website content is fetched.', 'hint'))
        self.safety_indicators=label('Inspect a website to see basic URL indicators.', 'muted')
        safety.addWidget(self.safety_indicators)

        self.live_health_frame, health = card(p)
        health.addWidget(label('CERTIFICATE HEALTH', 'kicker'))
        self.live_health = label('Not inspected', 'sectionTitle')
        health.addWidget(self.live_health)
        health.addWidget(label('Certificate Expiry Date', 'hint'))
        self.live_expiry = label('—', 'pageTitle')
        health.addWidget(self.live_expiry)
        self.live_remaining = label('', 'value')
        health.addWidget(self.live_remaining)
        self.live_health_detail = label('', 'muted')
        health.addWidget(self.live_health_detail)
        health.addWidget(horizontal_line())
        self.live_remarks = label('Remarks: Not checked.', 'hint')
        health.addWidget(self.live_remarks)
        self.live_health_frame.hide()

        self.live_details_frame, details = card(p)
        details.addWidget(label('OBSERVED CERTIFICATE DETAILS', 'sectionTitle'))
        self.detail_fields = {}
        detail_grid = QGridLayout()
        detail_grid.setHorizontalSpacing(26)
        detail_grid.setVerticalSpacing(14)
        keys = [('Target', 'target'), ('Connected IP', 'ip'),
                ('Issuer', 'issuer'), ('Subject CN', 'cn'),
                ('Certificate Type', 'type'), ('TLS Version', 'tls'),
                ('Resolved A / AAAA', 'resolved'), ('CNAME', 'cname'),
                ('TLS Cipher', 'cipher'), ('Not Before', 'not_before'),
                ('SHA-256 Fingerprint', 'fingerprint')]
        for index, (heading, key) in enumerate(keys):
            column = (index % 2) if index < 10 else 0
            line_no = (index // 2) if index < 10 else 5
            detail = QVBoxLayout()
            detail.setSpacing(4)
            detail.addWidget(label(heading, 'hint'))
            value = label('', 'detailValue')
            value.setWordWrap(True)
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            value.setMinimumWidth(0)
            detail.addWidget(value)
            self.detail_fields[key] = value
            detail_grid.addLayout(detail, line_no, column, 1, 2 if index == 10 else 1)
        detail_grid.setColumnStretch(0, 1)
        detail_grid.setColumnStretch(1, 1)
        details.addLayout(detail_grid)
        details.addWidget(horizontal_line())
        details.addWidget(label('CERTIFICATE SUBJECT', 'sectionTitle'))
        self.live_subject_details = label('', 'muted')
        self.live_subject_details.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        details.addWidget(self.live_subject_details)
        details.addWidget(label('DNS / SAN NAMES', 'sectionTitle'))
        self.live_sans = label('', 'muted')
        self.live_sans.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        details.addWidget(self.live_sans)
        self.live_details_frame.hide()

        self.live_compare_frame, compare = card(p)
        compare.addWidget(label('COMPARE WITH CSR', 'sectionTitle'))
        compare.addWidget(label('Live certificate health and CSR changes are evaluated separately. A removed SAN is a review item, not proof the deployed certificate is broken.', 'hint'))
        chooser = QHBoxLayout()
        chooser.addWidget(label('Comparison source:'))
        self.live_source = QComboBox()
        self.live_source.addItems(['Draft CSR form', 'Generated CSR (last generated)'])
        self.live_source.currentIndexChanged.connect(self.update_live_compare)
        chooser.addWidget(self.live_source)
        chooser.addStretch(1)
        compare.addLayout(chooser)
        self.live_comparison = label('', 'muted')
        compare.addWidget(self.live_comparison)
        control = QHBoxLayout()
        self.live_import = button('Import Live SANs to CSR Generator', self.import_live_sans)
        control.addWidget(self.live_import)
        control.addWidget(button('Import Certificate Subject', self.import_live_subject))
        control.addStretch(1)
        compare.addLayout(control)
        self.live_compare_frame.hide()

        self.live_export_frame, actions = card(p)
        actions.addWidget(label('CERTIFICATE VERIFICATION PICTURE', 'sectionTitle'))
        actions.addWidget(label('Export a compact report containing the checked domain, expiry date, trust, hostname match, timestamp and optional checker contact.', 'hint'))
        actions.addWidget(button('Export Picture Preview…', self.show_picture_preview, primary=True),
                          alignment=Qt.AlignmentFlag.AlignLeft)
        self.live_export_frame.hide()
        p.addStretch(1)

    def open_ssl_checker(self):
        try:
            # Unlike CSR issuance, only a real host can be inspected; wildcards are not connectable.
            target = live_ssl.parse_target(self.primary.text())
            self.live_input.setText(target.host if target.port == 443 else f'{target.host}:{target.port}')
        except ValueError as exc:
            self._error('Invalid SSL checker target', exc)
            return
        self.navigate(5)
        self.run_live_check()

    def run_live_check(self):
        if self.live_worker is not None and self.live_worker.isRunning():
            return
        try:
            target = live_ssl.parse_target(self.live_input.text())
        except ValueError as exc:
            self._error('Invalid SSL checker target', exc)
            return
        self.live_result = None
        self.live_health_frame.hide()
        self.live_details_frame.hide()
        self.live_compare_frame.hide()
        self.live_export_frame.hide()
        self.live_progress.setText('Checking ' + target.host + '…  fresh DNS + TLS connection')
        self.live_inspect.setEnabled(False)
        self.live_worker = SSLInspectWorker(self.live_input.text(), self)
        self.live_worker.success.connect(self._live_success)
        self.live_worker.failure.connect(self._live_failure)
        self.live_worker.finished.connect(self._live_finished)
        self.live_worker.start()

    def _live_finished(self):
        self.live_inspect.setEnabled(True)

    def _live_failure(self, message: str):
        self.live_result = None
        self.live_progress.setText('Unable to verify: ' + message + '\nConnection/DNS failures do not prove a certificate is invalid.')
        self.statusBar().showMessage('Live SSL inspection failed', 6000)

    def _live_success(self, result: live_ssl.LiveResult):
        self.live_result = result
        self.safety_indicators.setText('\n'.join('• '+note for note in website_safety.assess_target(
            result.target.host+':'+str(result.target.port))))
        if self.watch_add.isChecked():
            self.add_watch_target(result.target.host + ':' + str(result.target.port), result)
            self.watch_add.setChecked(False)
        self.live_progress.setText('Fresh check completed at ' + english_datetime(result.checked_at, '%d %b %Y · %H:%M:%S'))
        endpoint_key = (result.target.host, result.target.port, result.connected_ip)
        previous = self._previous_fingerprint.get(endpoint_key)
        self._previous_fingerprint[endpoint_key] = result.fingerprint
        color = ({'valid': '#49D795', 'warning': '#FFD166', 'critical': '#FF827D'} if self.dark else {'valid': '#14804A', 'warning': '#A66B12', 'critical': '#B42318'})[result.health]
        status = ('Valid & Trusted' if result.health == 'valid' else
                  'Renewal Recommended' if result.health == 'warning' else 'Certificate Issue / Urgent Renewal')
        self.live_health.setText(status)
        self.live_health.setStyleSheet('color:' + color)
        self.live_expiry.setText(english_datetime(result.expires_at))
        self.live_expiry.setStyleSheet('color:' + color + '; font-weight: 800;')
        self.live_remaining.setText(f'{result.remaining_days} full days remaining')
        self.live_remaining.setStyleSheet('color:' + color)
        self.live_health_detail.setText('Hostname: ' + ('MATCH' if result.hostname_ok else 'MISMATCH') +
            '    |    Trust: ' + ('TRUSTED' if result.trust_ok else 'NOT TRUSTED'))
        remarks = list(result.issues)
        if result.health == 'warning':
            remarks.append('Renew within 30 days.')
        if result.health == 'critical' and not result.issues:
            remarks.append('Urgent renewal: 15 days or less remaining.')
        remarks.extend(result.remarks)
        if previous and previous != result.fingerprint:
            remarks.append('Certificate CHANGED since the previous check of this endpoint (SHA-256 fingerprint differs).')
        self.live_remarks.setText('Remarks:\n' + ('\n'.join('• ' + item for item in remarks) if remarks else 'No validity/trust issues detected on the connected endpoint.'))
        entries = {
            'target': f'{result.target.host}:{result.target.port}', 'ip': result.connected_ip,
            'resolved': ', '.join(result.resolved_ips),
            'cname': ', '.join(result.cnames) if result.cnames else '(none observed)',
            'issuer': result.issuer, 'cn': result.subject_cn,
            'type': result.certificate_type, 'tls': result.tls_version,
            'cipher': result.cipher, 'fingerprint': result.fingerprint,
            'not_before': result.not_before.strftime('%d %B %Y · %H:%M UTC'),
        }
        for key, text in entries.items():
            self.detail_fields[key].setText(text)
        from cryptography.x509.oid import NameOID
        subject_keys=[('CN',NameOID.COMMON_NAME),('O',NameOID.ORGANIZATION_NAME),
                      ('OU',NameOID.ORGANIZATIONAL_UNIT_NAME),('C',NameOID.COUNTRY_NAME),
                      ('ST',NameOID.STATE_OR_PROVINCE_NAME),('L',NameOID.LOCALITY_NAME)]
        self.live_subject_details.setText('\n'.join(
            f'{name}: '+(', '.join(x.value for x in result.certificate.subject.get_attributes_for_oid(oid)) or 'Not included')
            for name,oid in subject_keys))
        self.live_sans.setText('\n'.join('• ' + x for x in result.sans) if result.sans else '(no DNS SAN)')
        self.live_health_frame.show()
        self.live_details_frame.show()
        self.live_compare_frame.show()
        self.live_export_frame.show()
        self.update_live_compare()

    def update_live_compare(self):
        if self.live_result is None or not hasattr(self, 'live_comparison'):
            return
        try:
            if self.live_source.currentIndex() == 1:
                if not self.csr_data:
                    self.live_comparison.setText('No generated CSR exists. Switch to Draft CSR form, or generate a CSR first.')
                    return
                csr = core.parse_csr(self.csr_data)
                proposal = tuple(core.get_sans(csr))
                source = 'Generated CSR (actual PEM)'
            else:
                proposal = tuple(core.san_names(self.primary.text(), self._extra_names(), self.auto_www.isChecked()))
                source = 'Draft CSR (current editable form)'
            retained, added, removed = live_ssl.compare_sans(self.live_result.sans, proposal)
            result = self.live_result
            current_host_covered = any(core.dns_covers(n, result.target.host) for n in proposal)
            self.live_comparison.setText(
                f'Source: {source}\n'
                f'Current inspected hostname in proposed CSR: {"COVERED" if current_host_covered else "NOT COVERED — CHECK BEFORE RENEWAL"}\n\n'
                'Retained / covered: ' + (', '.join(retained) or '(none)') + '\n'
                'New SANs: ' + (', '.join(added) or '(none)') + '\n'
                'Removed / no longer covered (review): ' + (', '.join(removed) or '(none)') + '\n\n'
                'Note: A change in SANs can be intentional and does not alter the health of the current live certificate.')
        except Exception as exc:
            self.live_comparison.setText('CSR comparison unavailable: ' + str(exc))

    def import_live_sans(self):
        if self.live_result is None:
            return
        names = list(self.live_result.sans)
        if not names:
            self._notify('warning', 'No SANs', 'The observed certificate has no DNS SANs.')
            return
        if not self._ask('Import observed SANs?',
                         'Merge observed certificate DNS names into Generate CSR?\n\n' +
                         '\n'.join(names[:40]) + ('\n… (more)' if len(names) > 40 else '') +
                         '\n\nExisting CSR fields will not be erased. Any wildcard primary name must be checked manually.'):
            return
        try:
            existing = set(self._extra_names())
            primary = core.normalize_dns(self.primary.text())
            if len(names) > 100:
                raise ValueError('Too many SANs to import (maximum 100).')
            for raw in names:
                value = core.normalize_dns(raw)
                if value != primary and value not in existing:
                    self.extra_sans.addItem(value)
                    existing.add(value)
            if self.extra_sans.count():
                self.extra_sans.show()
                self._update_remove_dns()
            self._update_generator()
            self.update_live_compare()
            self.navigate(0)
        except Exception as exc:
            self._error('SAN import failed', exc)

    def import_live_subject(self):
        """Import only Subject fields actually present in the observed certificate."""
        if self.live_result is None:
            return
        from cryptography.x509.oid import NameOID
        mapping = {'C': NameOID.COUNTRY_NAME, 'ST': NameOID.STATE_OR_PROVINCE_NAME,
                   'L': NameOID.LOCALITY_NAME, 'O': NameOID.ORGANIZATION_NAME,
                   'OU': NameOID.ORGANIZATIONAL_UNIT_NAME}
        candidate = {}
        for key, oid in mapping.items():
            attributes = self.live_result.certificate.subject.get_attributes_for_oid(oid)
            if attributes and str(attributes[0].value).strip():
                candidate[key] = str(attributes[0].value).strip()
        if not candidate:
            self._notify('information', 'No Subject attributes',
                         'This certificate does not provide Country, State, City, Organization or Unit fields. Existing defaults were preserved.')
            return
        preview = '\n'.join(f'{key}: {value}' for key, value in candidate.items())
        if not self._ask('Import observed Certificate Subject?',
                         'Copy the following fields into the CSR subject form?\n\n' + preview +
                         '\n\nFields not provided will remain unchanged. The CSR domain and SANs are not modified.'):
            return
        for key, value in candidate.items():
            self.fields[key].setText(value[:self.fields[key].maxLength()])
        self._save_subject_if_enabled()
        self._update_generator()
        self.subject_block.set_open(True)
        self.navigate(0)
        self.statusBar().showMessage('Certificate Subject imported from live certificate.', 6000)

    def show_picture_preview(self):
        if self.live_result is None:
            self._notify('warning','Nothing to export','Complete a live inspection first.')
            return
        try:
            target = live_ssl.parse_target(self.live_input.text())
        except ValueError as exc:
            self._error('Invalid checker target', exc)
            return
        if target != self.live_result.target:
            self._notify('warning','Recheck required','The hostname or port was changed. Inspect again before exporting.')
            return
        dialog = ExportPictureDialog(self, self.live_result)
        dialog.exec()

    def closeEvent(self, event):
        if self.live_worker is not None and self.live_worker.isRunning():
            event.ignore()
            self.statusBar().showMessage('SSL inspection is still running; close after it finishes.', 5000)
            return
        super().closeEvent(event)

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
                data = core.read_limited(Path(path))
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
                private_key = core.load_key(core.read_limited(Path(keypath), 1024*1024), self.bundle_key_pass.text())
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
            activity_log.record('PEM + PFX Exported' if pfx is not None else 'PEM Exported', cn, str(folder))
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



    # --- V3.4 Watch List (bounded queue, independent of live checker) ---
    def _build_watch_page(self):
        p=self.watch_page
        self._heading(p, 'Certificate tools / 05', 'SSL Watch List',
                      'Local saved targets. Connection failures never erase the last successful certificate result.')
        _, area=card(p)
        controls=QHBoxLayout()
        controls.addWidget(button('Refresh All', self.refresh_all_watch, primary=True))
        controls.addWidget(button('Add Website', self._watch_prompt_add))
        controls.addStretch(1)
        area.addLayout(controls)
        self.watch_progress=label('Ready', 'muted')
        area.addWidget(self.watch_progress)
        self.watch_table=QTableWidget(0,5)
        self.watch_table.setHorizontalHeaderLabels(['Website','Connection','Certificate Expiry','Days Left','Details'])
        self.watch_table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.Stretch)
        self.watch_table.horizontalHeader().setSectionResizeMode(4,QHeaderView.ResizeMode.ResizeToContents)
        self.watch_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.watch_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.watch_table.setMinimumHeight(260)
        area.addWidget(self.watch_table)
        self.watch_details=QPlainTextEdit()
        self.watch_details.setReadOnly(True)
        self.watch_details.setMaximumHeight(180)
        self.watch_details.setPlaceholderText('Select a website to view last known certificate and connection details.')
        area.addWidget(self.watch_details)
        self.watch_table.itemSelectionChanged.connect(self._show_watch_details)
        actions=QHBoxLayout()
        actions.addWidget(button('Refresh Selected',self.refresh_selected_watch))
        actions.addWidget(button('Inspect Selected',self.inspect_selected_watch))
        actions.addWidget(button('Email Reminder',self.email_watch_reminder))
        actions.addWidget(button('Remove Selected',self.remove_selected_watch))
        actions.addStretch(1)
        area.addLayout(actions)
        p.addStretch(1)
        _, opts=card(p)
        self.watch_auto=QCheckBox('Refresh automatically when the application starts')
        self.watch_auto.setChecked(self.settings.value('watch/refresh_on_startup',True,type=bool))
        self.watch_auto.toggled.connect(lambda value:self.settings.setValue('watch/refresh_on_startup',value))
        opts.addWidget(self.watch_auto)
        opts.addWidget(label('Maximum 3 concurrent TLS checks. The next website starts when a check finishes.', 'hint'))
        self._update_watch_table()

    def _watch_prompt_add(self):
        from PySide6.QtWidgets import QInputDialog
        raw,ok=QInputDialog.getText(self,'Add website','HTTPS hostname or URL:')
        if ok and raw.strip():
            try: self.add_watch_target(raw)
            except Exception as exc: self._error('Invalid watch target',exc)

    def add_watch_target(self, raw, result=None):
        key=watch_store.watch_key(raw)
        found=next((x for x in self.watch_items if x['target']==key),None)
        if found is None:
            if len(self.watch_items)>=watch_store.MAX_WATCHED: raise ValueError('Maximum 100 watched websites.')
            found={'target':key,'last_good':None,'last_attempt':'','error':'Not checked'}
            self.watch_items.append(found)
        if result is not None:
            found['last_good']=watch_store.snapshot(result)
            found['last_attempt']=result.checked_at.isoformat()
            found['error']=''
        watch_store.save_watchlist(self.watch_items)
        self._update_watch_table()

    def _selected_watch(self):
        row=self.watch_table.currentRow()
        return self.watch_items[row] if 0<=row<len(self.watch_items) else None

    def _update_watch_table(self):
        if not hasattr(self,'watch_table'): return
        self.watch_table.setRowCount(len(self.watch_items))
        for row,item in enumerate(self.watch_items):
            days=watch_store.remaining_days(item)
            good=item.get('last_good')
            connection=('Checking…' if item['target'] in self.watch_active else
                        'Unreachable / Unknown' if item.get('error') else 'Connected (last check)')
            expiry=good.get('expires_at','')[:10] if good else 'Not checked'
            vals=[item['target'],connection,expiry,str(days) if days is not None else '—','Expand below']
            for col,value in enumerate(vals):
                cell=QTableWidgetItem(value)
                if col in (2,3) and days is not None:
                    from PySide6.QtGui import QBrush
                    color='#FF827D' if self.dark else '#B42318'
                    if days>15: color=('#FFD166' if self.dark else '#A66B12') if days<=30 else ('#49D795' if self.dark else '#14804A')
                    cell.setForeground(QBrush(QColor(color)))
                self.watch_table.setItem(row,col,cell)
        self.watch_progress.setText(f'{len(self.watch_active)} checking · {len(self.watch_queue)} queued · {len(self.watch_items)} watched')

    def _show_watch_details(self):
        item=self._selected_watch()
        if not item: self.watch_details.clear(); return
        good=item.get('last_good') or {}
        lines=[f'Target: {item["target"]}',f'Latest attempt: {item.get("last_attempt") or "Never"}',
               f'Connection status: {item.get("error") or "Last attempt succeeded"}',
               f'Last successful check: {good.get("checked_at","Never")}',
               f'Last known expiry: {good.get("expires_at","Unknown")}',
               f'Issuer: {good.get("issuer","Unknown")}',f'Subject CN: {good.get("subject_cn","Unknown")}',
               f'Certificate type: {good.get("certificate_type","Unknown")}',
               f'Hostname match: {good.get("hostname_ok","Unknown")}',f'Trusted: {good.get("trust_ok","Unknown")}',
               f'SHA-256: {good.get("fingerprint","Unknown")}',
               'SANs: '+', '.join(good.get('sans',[]))]
        if item.get('error'): lines.append('WARNING: Certificate details are historical, NOT a current verification.')
        self.watch_details.setPlainText('\n'.join(lines))

    def refresh_all_watch(self):
        if self.watch_active or self.watch_queue: return
        self.watch_queue=[item['target'] for item in self.watch_items]
        self._next_watch_checks()

    def refresh_selected_watch(self):
        item=self._selected_watch()
        if item and item['target'] not in self.watch_queue and item['target'] not in self.watch_active:
            self.watch_queue.append(item['target']);self._next_watch_checks()

    def _next_watch_checks(self):
        while len(self.watch_active)<3 and self.watch_queue:
            key=self.watch_queue.pop(0)
            worker=SSLInspectWorker(key,self)
            self.watch_active[key]=worker
            worker.success.connect(lambda result,k=key:self._watch_success(k,result))
            worker.failure.connect(lambda message,k=key:self._watch_failure(k,message))
            worker.finished.connect(lambda k=key:self._watch_finished(k))
            worker.start()
        self._update_watch_table()

    def _watch_success(self,key,result):
        item=next((x for x in self.watch_items if x['target']==key),None)
        if item:
            item['last_good']=watch_store.snapshot(result)
            item['last_attempt']=result.checked_at.isoformat();item['error']=''
            watch_store.save_watchlist(self.watch_items)
            self._update_watch_table();self._show_watch_details()

    def _watch_failure(self,key,message):
        item=next((x for x in self.watch_items if x['target']==key),None)
        if item:
            item['last_attempt']=datetime.now(timezone.utc).isoformat()
            item['error']=message[:350]
            watch_store.save_watchlist(self.watch_items)
            self._update_watch_table();self._show_watch_details()

    def _watch_finished(self,key):
        worker=self.watch_active.pop(key,None)
        if worker: worker.deleteLater()
        self._next_watch_checks()

    def remove_selected_watch(self):
        item=self._selected_watch()
        if item and self._ask('Remove website','Remove '+item['target']+' from the watch list?'):
            self.watch_items.remove(item)
            self.watch_queue=[x for x in self.watch_queue if x!=item['target']]
            watch_store.save_watchlist(self.watch_items)
            self._update_watch_table();self._show_watch_details()

    def inspect_selected_watch(self):
        item=self._selected_watch()
        if item:
            self.live_input.setText(item['target']);self.navigate(5);self.run_live_check()

    def email_watch_reminder(self):
        item=self._selected_watch()
        if not item: return
        good=item.get('last_good')
        if not good:
            QMessageBox.information(self,'No certificate','Check the website successfully before creating a reminder.')
            return
        days=watch_store.remaining_days(item)
        message=EmailMessage()
        message['Subject']='SSL Certificate Expiry Notice - '+item['target']
        checker=self.settings.value('export/checker_name','',type=str)
        contact=self.settings.value('export/checker_email','',type=str)
        body=(f'Website: {item["target"]}\nLast known certificate expiry: {good.get("expires_at")}\n'
              f'Days remaining (based on saved certificate): {days}\n'
              f'Last successful check: {good.get("checked_at")}\n'
              f'Latest connection attempt: {item.get("last_attempt")}\n'
              f'Current connection: {"Unreachable / unknown" if item.get("error") else "Last check succeeded"}\n'
              f'SSL Checked by: {checker}\nContact Email: {contact}\n'
              'This is a draft; confirm the recipient and current certificate status before sending.\n')
        message.set_content(body)
        # Optional PNG from the certificate verification picture, selected explicitly.
        attach=QMessageBox.question(self,'Attach verification picture?',
            'Attach a previously exported SSL verification PNG to the email draft?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if attach==QMessageBox.StandardButton.Yes:
            picture,_=QFileDialog.getOpenFileName(self,'Select verification picture','','PNG (*.png)')
            if picture:
                image_path=Path(picture)
                if image_path.stat().st_size>5*1024*1024:
                    QMessageBox.warning(self,'Image too large','Maximum attachment size is 5 MB.')
                    return
                if image_path.read_bytes()[:8]!=b'\x89PNG\r\n\x1a\n':
                    QMessageBox.warning(self,'Invalid picture','Selected file is not a PNG.')
                    return
                message.add_attachment(image_path.read_bytes(),maintype='image',subtype='png',filename=image_path.name)
        path,_=QFileDialog.getSaveFileName(self,'Save email draft',
            str(Path.home()/(item['target'].replace(':','_')+'_ssl_reminder.eml')),'Email draft (*.eml)')
        if path:
            Path(path).write_bytes(message.as_bytes())
            activity_log.record('Email Draft Exported',item['target'],path)
            QMessageBox.information(self,'Email draft saved','Open the .eml file in your email application, review the recipient and verify the attached picture if any.')

    # --- V3.4 Activity Log ---
    def _build_activity_page(self):
        p=self.activity_page
        self._heading(p,'Certificate tools / 06','Certificate Activity Log',
                      'Local record of generated CSR/KEY and exported PEM/PFX files. No private key content is logged.')
        _,area=card(p)
        actions=QHBoxLayout()
        actions.addWidget(button('Refresh',self.refresh_activity))
        actions.addWidget(button('Export CSV',self.export_activity_csv))
        actions.addWidget(button('Clear Log',self.clear_activity))
        actions.addStretch(1)
        area.addLayout(actions)
        self.activity_table=QTableWidget(0,5)
        self.activity_table.setHorizontalHeaderLabels(['Time (UTC)','Operation','Domain','Output Location','Result'])
        self.activity_table.horizontalHeader().setSectionResizeMode(3,QHeaderView.ResizeMode.Stretch)
        self.activity_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.activity_table.setMinimumHeight(350)
        area.addWidget(self.activity_table)
        p.addStretch(1)
        self.refresh_activity()

    def refresh_activity(self):
        if not hasattr(self,'activity_table'): return
        rows=activity_log.recent()
        self.activity_table.setRowCount(len(rows))
        for i,row in enumerate(rows):
            for j,value in enumerate(row): self.activity_table.setItem(i,j,QTableWidgetItem(str(value)))

    def export_activity_csv(self):
        path,_=QFileDialog.getSaveFileName(self,'Export activity log',str(Path.home()/'ssl_activity_log.csv'),'CSV (*.csv)')
        if path:
            with open(path,'w',encoding='utf-8-sig',newline='') as f:
                writer=csv.writer(f);writer.writerow(['Time (UTC)','Operation','Domain','Output Location','Result'])
                for row in activity_log.recent(1000): writer.writerow(['\''+str(v) if str(v)[:1] in '=+-@' else v for v in row])

    def clear_activity(self):
        if self._ask('Clear activity log','Permanently clear local activity history?'):
            activity_log.clear();self.refresh_activity()


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
    splash_pix = QPixmap(520, 240)
    splash_pix.fill(QColor('#172437'))
    painter = QPainter(splash_pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.setPen(QPen(QColor('#49D795'), 2.4))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    from PySide6.QtGui import QPainterPath
    shield_path = QPainterPath()
    shield_path.moveTo(23, 48); shield_path.lineTo(32, 51)
    shield_path.lineTo(32, 61); shield_path.cubicTo(32, 68, 27, 73, 23, 76)
    shield_path.cubicTo(19, 73, 14, 68, 14, 61)
    shield_path.lineTo(14, 51); shield_path.closeSubpath()
    painter.drawPath(shield_path)
    painter.drawLine(18, 61, 22, 65); painter.drawLine(22, 65, 29, 57)
    painter.setPen(QColor('#F1F5FC'))
    title_font = QFont('Segoe UI', 19, QFont.Weight.Bold)
    painter.setFont(title_font)
    painter.drawText(QRectF(47, 42, 440, 52), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                     'SSL Certificate Toolkit')
    painter.setFont(QFont('Segoe UI', 11))
    painter.setPen(QColor('#B7C6D9'))
    painter.drawText(QRectF(35, 101, 450, 30), f'Version {APP_VERSION}  ·  CSR / SSL Inspector')
    painter.drawText(QRectF(35, 180, 450, 30), 'Developed by cleverandy')
    painter.end()
    splash = QSplashScreen(splash_pix)
    splash.show()
    app.processEvents()
    window = MainWindow()
    window.show()
    splash.finish(window)
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
