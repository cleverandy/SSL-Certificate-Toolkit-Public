"""Independently expandable watch-list website card."""
from datetime import datetime
from PySide6.QtCore import Signal,Qt
from PySide6.QtWidgets import QFrame,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QCheckBox,QWidget

class WatchCard(QFrame):
    selected=Signal(str)
    refresh_requested=Signal(str)
    inspect_requested=Signal(str)
    email_requested=Signal(str)
    def __init__(self,item,days,checking=False,expanded=False,dark=False,parent=None):
        super().__init__(parent)
        self.item=item;self.expanded=expanded
        self.setObjectName('card')
        self.setFrameShape(QFrame.Shape.StyledPanel)
        root=QVBoxLayout(self);root.setContentsMargins(12,10,12,10);root.setSpacing(7)
        row=QHBoxLayout();root.addLayout(row)
        self.selector=QCheckBox();self.selector.setToolTip('Select website')
        self.selector.toggled.connect(lambda checked:self.selected.emit(item['target']) if checked else None)
        row.addWidget(self.selector)
        name=QLabel(item['target']);name.setToolTip(item['target']);name.setMinimumWidth(100)
        row.addWidget(name,5)
        good=item.get('last_good') or {}
        expiry=good.get('expires_at','')[:10] or 'Not checked'
        date=QLabel(expiry);date.setMinimumWidth(90);row.addWidget(date)
        left=QLabel('—' if days is None else f'{days}d' if days>=0 else 'Expired')
        left.setFixedWidth(54);left.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if days is not None:
            color=('#FF827D' if dark else '#B42318') if days<=15 else ('#FFD166' if dark else '#A66B12') if days<=30 else ('#49D795' if dark else '#14804A')
            left.setStyleSheet('color:'+color+';font-weight:700;')
        row.addWidget(left)
        connection=QLabel('🔌' if not item.get('error') and good else '○')
        connection.setToolTip('Checking' if checking else ('Unreachable / unknown' if item.get('error') else 'Last check connected'))
        connection.setStyleSheet('color:'+('#4B9EF0' if good and not item.get('error') else '#8995A6'))
        connection.setFixedWidth(28);row.addWidget(connection)
        expand=QPushButton('⌃' if expanded else '⌄');expand.setToolTip('Collapse details' if expanded else 'Expand details')
        expand.setFixedWidth(30);row.addWidget(expand)
        self.details=QWidget();details=QVBoxLayout(self.details);details.setContentsMargins(8,6,8,4)
        def detail(key,value):
            lbl=QLabel(f'{key}: {value}');lbl.setWordWrap(True);lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            details.addWidget(lbl)
        detail('Issuer',good.get('issuer','Unknown'))
        detail('Subject CN',good.get('subject_cn','Unknown'))
        detail('Last successful check',good.get('checked_at','Never'))
        detail('Last attempt',item.get('last_attempt') or 'Never')
        detail('Connection',item.get('error') or ('Last check succeeded' if good else 'Not checked'))
        detail('Trust',good.get('trust_ok','Unknown'))
        detail('Hostname match',good.get('hostname_ok','Unknown'))
        detail('SHA-256',good.get('fingerprint','Unknown'))
        detail('SANs',', '.join(good.get('sans',[])) or 'Unknown')
        if item.get('error') and good:detail('WARNING','Historical certificate; not a current verification')
        actions=QHBoxLayout()
        for title,signal in [('Refresh',self.refresh_requested),('Inspect',self.inspect_requested),('Email Reminder',self.email_requested)]:
            btn=QPushButton(title);btn.clicked.connect(lambda _=False,sig=signal:sig.emit(item['target']));actions.addWidget(btn)
        actions.addStretch();details.addLayout(actions)
        root.addWidget(self.details);self.details.setVisible(expanded)
        expand.clicked.connect(lambda:self.toggle(expand))
    def toggle(self,button):
        self.expanded=not self.expanded;self.details.setVisible(self.expanded)
        button.setText('⌃' if self.expanded else '⌄')
    def set_selected(self,yes):
        self.selector.blockSignals(True);self.selector.setChecked(yes);self.selector.blockSignals(False)
