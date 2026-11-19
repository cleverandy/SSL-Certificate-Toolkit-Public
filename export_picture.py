"""Private, local PNG/clipboard report rendering. No web or HTML content is loaded."""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path
from datetime import timezone

from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import (QApplication, QDialog, QFileDialog, QFrame,
                                QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
                                QVBoxLayout, QWidget)

from PySide6.QtGui import QPainter, QPainterPath, QPen, QColor, QPixmap

from live_ssl import LiveResult

from app_version import APP_VERSION


def shield_check_pixmap(color: str, size: int = 22) -> QPixmap:
    """Draw a crisp vector shield/check at 3x, independent of platform fonts."""
    scale = 3
    pixmap = QPixmap(size * scale, size * scale)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    painter.scale(size / 20 * scale, size / 20 * scale)
    painter.setPen(QPen(QColor(color), 1.7, Qt.PenStyle.SolidLine,
                        Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    path = QPainterPath()
    path.moveTo(10, 2); path.lineTo(16.5, 4.5); path.lineTo(16.5, 9.5)
    path.cubicTo(16.5, 13.5, 14, 16.2, 10, 18)
    path.cubicTo(6, 16.2, 3.5, 13.5, 3.5, 9.5)
    path.lineTo(3.5, 4.5); path.closeSubpath()
    painter.drawPath(path)
    painter.drawLine(7, 10, 9, 12); painter.drawLine(9, 12, 13.5, 7.5)
    painter.end()
    pixmap.setDevicePixelRatio(scale)
    return pixmap



def clean_name(value: str) -> str:
    value = ' '.join(value.strip().split())
    if len(value) > 60:
        raise ValueError('SSL Checked by must be 60 characters or fewer.')
    for ch in value:
        cat = unicodedata.category(ch)
        if not (cat[0] in ('L', 'M', 'N') or ch in " .,_-'&()"):
            raise ValueError('Name contains unsupported characters (including control/bidirectional formatting).')
    return value


def clean_email(value: str) -> str:
    value = value.strip()
    if not value:
        return ''
    if len(value) > 120 or not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+", value):
        raise ValueError('Enter a valid email address of no more than 120 characters.')
    return value


def l(text: str, *, bold: bool = False, size: int = 10, color: str = '') -> QLabel:
    out = QLabel(text)
    out.setTextFormat(Qt.TextFormat.PlainText)
    out.setWordWrap(True)
    out.setStyleSheet(f"color: {color or ('#E8EFF9' if QApplication.instance() and QApplication.instance().property('ssl_dark') else '#17263D')}; font-size: {size}pt; font-weight: {'700' if bold else '400'}; background: transparent;")
    return out


def pair(parent: QVBoxLayout, title: str, value: str, *, ink: str, muted: str):
    line = QHBoxLayout()
    line.setSpacing(14)
    key = l(title, size=9, color=muted)
    key.setMinimumWidth(128)
    val = l(value, size=9, bold=True, color=ink)
    val.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    line.addWidget(key)
    line.addWidget(val, 1)
    parent.addLayout(line)


class ExportPictureDialog(QDialog):
    def __init__(self, parent: QWidget, result: LiveResult):
        super().__init__(parent)
        self.result = result
        self.ui_dark = bool(getattr(parent, 'dark', False))
        self.setObjectName('exportDialog')
        self.setStyleSheet(self._dialog_style())
        self.settings = QSettings('SSLToolkit', 'SSL Certificate Toolkit')
        self.setWindowTitle('Export Certificate Verification Picture')
        self.setMinimumWidth(740)
        self.resize(800, 780)
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 16, 22, 20)
        root.setSpacing(12)
        back = QPushButton('←  Back to SSL Checker')
        back.clicked.connect(self.reject)
        root.addWidget(back, alignment=Qt.AlignmentFlag.AlignLeft)
        title = l('Export Picture Preview', size=17, bold=True)
        root.addWidget(title)
        fields = QHBoxLayout()
        name_col = QVBoxLayout()
        name_col.addWidget(l('SSL Checked by (optional)', size=9))
        self.name = QLineEdit(self.settings.value('export/checker_name', '', type=str))
        self.name.setMaxLength(60)
        self.name.setPlaceholderText('Name or team')
        name_col.addWidget(self.name)
        fields.addLayout(name_col, 1)
        email_col = QVBoxLayout()
        email_col.addWidget(l('Contact Email (optional)', size=9))
        self.email = QLineEdit(self.settings.value('export/checker_email', '', type=str))
        self.email.setMaxLength(120)
        self.email.setPlaceholderText('support@example.com')
        self.saved_name = self.name.text()
        self.saved_email = self.email.text()
        email_col.addWidget(self.email)
        fields.addLayout(email_col, 1)
        root.addLayout(fields)
        self.form_error = l('', size=9, color='#FFAAA3' if self.ui_dark else '#B42318')
        root.addWidget(self.form_error)
        self.form_error.hide()
        # The signature is committed only when Save is clicked. No per-keystroke redraw.
        self.save_details_btn = QPushButton('Save')
        self.save_details_btn.setToolTip('Save signature details and update the picture preview')
        self.save_details_btn.clicked.connect(self.save_details)
        root.addWidget(self.save_details_btn, alignment=Qt.AlignmentFlag.AlignRight)
        root.addWidget(l('Only the card below is saved or copied. Input boxes and buttons are excluded.', size=8, color='#9BAAC0' if self.ui_dark else '#68788F'))
        self.picture = QFrame()
        self.picture.setObjectName('pictureCard')
        self.picture.setFixedWidth(690)
        self.picture_layout = QVBoxLayout(self.picture)
        self.picture_layout.setContentsMargins(27, 23, 27, 22)
        self.picture_layout.setSpacing(11)
        card_wrap = QHBoxLayout()
        card_wrap.addStretch(1)
        card_wrap.addWidget(self.picture)
        card_wrap.addStretch(1)
        root.addLayout(card_wrap)
        controls = QHBoxLayout()
        controls.addWidget(l('Picture Theme', size=9, color='#9BAAC0' if self.ui_dark else '#68788F'))
        self.light_btn = QPushButton('Light')
        self.dark_btn = QPushButton('Dark')
        for btn in (self.light_btn, self.dark_btn):
            btn.setCheckable(True)
            btn.setMinimumWidth(72)
            controls.addWidget(btn)
        self.theme_mode = 'Light'
        self.light_btn.clicked.connect(lambda: self.set_picture_theme('Light'))
        self.dark_btn.clicked.connect(lambda: self.set_picture_theme('Dark'))
        controls.addStretch(1)
        self.copy_btn = QPushButton('Copy Picture')
        self.save_btn = QPushButton('Save Picture')
        controls.addWidget(self.copy_btn)
        controls.addWidget(self.save_btn)
        root.addLayout(controls)
        self.copy_btn.clicked.connect(self.copy_picture)
        self.save_btn.clicked.connect(self.save_picture)
        self.preview_dirty = True
        self.name.textChanged.connect(self._mark_dirty)
        self.email.textChanged.connect(self._mark_dirty)
        self._set_theme_buttons()
        self._draw()

    def _dialog_style(self) -> str:
        """Apply a complete Qt dialog palette; avoid Windows native light controls in dark mode."""
        dark = self.ui_dark
        bg = '#101722' if dark else '#F5F7FB'
        field = '#243246' if dark else '#FFFFFF'
        text = '#E8EFF9' if dark else '#16243A'
        muted = '#9BAAC0' if dark else '#68788F'
        border = '#344459' if dark else '#DFE6F0'
        hover = '#30435B' if dark else '#E6EEFB'
        return f"""
        QDialog#exportDialog {{background: {bg}; color: {text};}}
        QDialog#exportDialog QLabel {{background: transparent;}}
        QDialog#exportDialog QLineEdit {{background: {field}; color: {text};
            border: 1px solid {border}; border-radius: 8px; padding: 9px;}}
        QDialog#exportDialog QLineEdit:focus {{border: 1px solid {'#80AAFF' if dark else '#175CD3'};}}
        QDialog#exportDialog QPushButton {{background: {field}; color: {text};
            border: 1px solid {border}; border-radius: 8px; padding: 9px 14px;}}
        QDialog#exportDialog QPushButton:hover {{background: {hover};}}
        QDialog#exportDialog QPushButton:checked {{background: {hover};
            border: 1px solid {'#80AAFF' if dark else '#175CD3'};}}
        QDialog#exportDialog QPushButton:disabled {{color: {muted};}}
        QDialog#exportDialog QScrollBar:vertical {{background: {'#344459' if dark else '#E8EDF4'};
            width: 10px; border: none; border-radius: 5px;}}
        QDialog#exportDialog QScrollBar::handle:vertical {{background: {'#73839A' if dark else '#A8B6C8'};
            border-radius: 5px; min-height: 24px;}}
        QDialog#exportDialog QScrollBar::add-line:vertical,
        QDialog#exportDialog QScrollBar::sub-line:vertical {{height: 0; background: none;}}
        """

    def _validate(self) -> tuple[str, str]:
        return clean_name(self.name.text()), clean_email(self.email.text())

    def _mark_dirty(self, *_args):
        self.preview_dirty = True
        self.save_details_btn.setText('Save *')

    def _set_theme_buttons(self):
        self.light_btn.setChecked(self.theme_mode == 'Light')
        self.dark_btn.setChecked(self.theme_mode == 'Dark')

    def set_picture_theme(self, theme: str):
        if theme not in ('Light', 'Dark'):
            return
        self.theme_mode = theme
        self._set_theme_buttons()
        self._draw()

    def save_details(self) -> bool:
        try:
            name, email = self._validate()
        except ValueError as exc:
            self.form_error.setText(str(exc))
            self.form_error.show()
            return False
        self.settings.setValue('export/checker_name', name)
        self.settings.setValue('export/checker_email', email)
        self.saved_name, self.saved_email = name, email
        self._draw()
        return True

    def _draw(self):
        # Never re-create every QLabel for each keystroke: draw only by explicit request.
        self.preview_dirty = (self.name.text() != self.saved_name or self.email.text() != self.saved_email)
        self.save_details_btn.setText('Save *' if self.preview_dirty else 'Save')
        while self.picture_layout.count():
            item = self.picture_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
            elif item.layout() is not None:
                def clear_layout(layout):
                    while layout.count():
                        child = layout.takeAt(0)
                        if child.widget():
                            child.widget().deleteLater()
                        elif child.layout():
                            clear_layout(child.layout())
                clear_layout(item.layout())
        dark = self.theme_mode == 'Dark'
        ink, muted, bg, line = ('#E8EFF9', '#9BAAC0', '#1B2635', '#344459') if dark else ('#16243A', '#68788F', '#FFFFFF', '#DFE6F0')
        color = ({'valid':'#49D795','warning':'#FFD166','critical':'#FF827D'} if dark else {'valid':'#14804A','warning':'#A76B0D','critical':'#C43129'})[self.result.health]
        self.picture.setStyleSheet(f'QFrame#pictureCard {{background: {bg}; border: 1px solid {line}; border-radius: 14px;}}')
        header = QHBoxLayout()
        header.setSpacing(8)
        shield = QLabel()
        shield.setPixmap(shield_check_pixmap(color, 22))
        shield.setFixedSize(24, 24)
        header.addWidget(shield)
        header_title = l('SSL Certificate Verification', bold=True, size=13, color=ink)
        header_title.setWordWrap(False)
        header.addWidget(header_title, 1)
        header.addStretch(1)
        product = QVBoxLayout()
        product.setSpacing(1)
        product_name = l('SSL Certificate Toolkit', size=8, bold=True, color=muted)
        product_name.setAlignment(Qt.AlignmentFlag.AlignRight)
        product_version = l(f'v{APP_VERSION}', size=8, color=muted)
        product_version.setAlignment(Qt.AlignmentFlag.AlignRight)
        product.addWidget(product_name)
        product.addWidget(product_version)
        header.addLayout(product)
        self.picture_layout.addLayout(header)
        self.picture_layout.addWidget(l('VERIFIED DOMAIN', size=8, color=muted))
        self.picture_layout.addWidget(l(self.result.target.host, size=15, bold=True, color=ink))
        self.picture_layout.addWidget(l('CERTIFICATE EXPIRY DATE', size=8, color=muted))
        expiry = self.result.expires_at.astimezone(timezone.utc).strftime('%d %B %Y · %H:%M UTC')
        self.picture_layout.addWidget(l(expiry, size=18, bold=True, color=color))
        status = ('Valid & Trusted' if self.result.health == 'valid' else
                  'Expiring Soon' if self.result.health == 'warning' else 'Certificate Issue / Expiring Soon')
        if self.result.health == 'critical' and self.result.issues:
            status = 'Certificate Issue'
        self.picture_layout.addWidget(l(f'{status}  ·  {self.result.remaining_days} full days remaining', size=10, bold=True, color=color))
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet('background:' + line)
        self.picture_layout.addWidget(divider)
        pair(self.picture_layout, 'Issuer', self.result.issuer, ink=ink, muted=muted)
        pair(self.picture_layout, 'Certificate Type', self.result.certificate_type, ink=ink, muted=muted)
        pair(self.picture_layout, 'Hostname Match', 'Passed' if self.result.hostname_ok else 'FAILED', ink=ink, muted=muted)
        pair(self.picture_layout, 'Certificate Trust', 'Trusted' if self.result.trust_ok else 'NOT TRUSTED', ink=ink, muted=muted)
        messages = list(self.result.issues)
        if self.result.health == 'warning':
            messages.insert(0, 'Certificate renewal is recommended within 30 days.')
        elif self.result.health == 'critical' and not messages:
            messages.insert(0, 'Certificate expires in 15 days or less; renewal is urgent.')
        if messages:
            self.picture_layout.addWidget(l('REMARKS', size=8, bold=True, color=color))
            self.picture_layout.addWidget(l('\n'.join('• ' + x for x in messages), size=9, color=ink))
        rule = QFrame()
        rule.setFixedHeight(1)
        rule.setStyleSheet('background:' + line)
        self.picture_layout.addWidget(rule)
        pair(self.picture_layout, 'Checked At', self.result.checked_at.astimezone(timezone.utc).strftime('%d %b %Y · %H:%M:%S UTC'), ink=ink, muted=muted)
        try:
            name, email = clean_name(self.saved_name), clean_email(self.saved_email)
            error = ''
        except ValueError as exc:
            name = email = ''
            error = str(exc)
        if name:
            pair(self.picture_layout, 'SSL Checked by', name, ink=ink, muted=muted)
        if email:
            pair(self.picture_layout, 'Contact Email', email, ink=ink, muted=muted)
        self.form_error.setText(error)
        self.form_error.setVisible(bool(error))
        self.copy_btn.setEnabled(not error)
        self.save_btn.setEnabled(not error)
        self.setToolTip(error)
        self.picture.adjustSize()
        self.adjustSize()

    def _render(self):
        name, email = self._validate()
        if self.preview_dirty and not self.save_details():
            raise ValueError('Please correct the signature details before exporting.')
        self.picture.ensurePolished()
        QApplication.processEvents()
        return self.picture.grab()

    def copy_picture(self):
        try:
            QApplication.clipboard().setPixmap(self._render())
        except Exception as exc:
            QMessageBox.warning(self, 'Copy failed', str(exc))
            return
        QMessageBox.information(self, 'Copied', 'Certificate verification picture copied to clipboard.')

    def save_picture(self):
        safe_host = re.sub(r'[^A-Za-z0-9._-]', '_', self.result.target.host)
        timestamp = self.result.checked_at.strftime('%Y%m%d_%H%M%S')
        default = str(Path.home() / f'SSL_Verification_{safe_host}_{timestamp}.png')
        path, _ = QFileDialog.getSaveFileName(self, 'Save certificate picture', default, 'PNG images (*.png)')
        if path:
            if not path.lower().endswith('.png'):
                path += '.png'
            try:
                if not self._render().save(path, 'PNG'):
                    raise IOError('PNG could not be written.')
            except (OSError, ValueError) as exc:
                QMessageBox.warning(self, 'Save failed', str(exc))
                return
            QMessageBox.information(self, 'Saved', 'Certificate verification picture saved.')
