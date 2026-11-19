"""Editable renewal reminder; uses the existing picture renderer when a fresh LiveResult exists."""
from datetime import datetime,timezone
from pathlib import Path
import tempfile
import uuid
from urllib.parse import urlencode
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QPlainTextEdit,QPushButton,QMessageBox
from export_picture import ExportPictureDialog

class EmailComposer(QDialog):
    def __init__(self,parent,item,result,settings):
        super().__init__(parent)
        self.item=item;self.result=result;self.settings=settings
        self.setWindowTitle('SSL Renewal Reminder');self.resize(680,570)
        layout=QVBoxLayout(self)
        layout.addWidget(QLabel('Recipient'))
        self.recipient=QLineEdit();self.recipient.setPlaceholderText('recipient@example.com');layout.addWidget(self.recipient)
        layout.addWidget(QLabel('Subject'))
        self.subject=QLineEdit('SSL Certificate Expiry Notice - '+item['target']);layout.addWidget(self.subject)
        good=item['last_good']
        stale=bool(item.get('error')) or result is None
        expires=good.get('expires_at','Unknown')[:10]
        body=(f'Hello,\n\nThe SSL certificate for {item["target"]} expires on {expires}.\n'
              'Please arrange renewal before the expiry date.\n\n'
              +('Note: The certificate information is from the last successful check and may be outdated.\n\n' if stale else '')
              +'The SSL verification picture is included when supported by your email application.\n\nBest regards,\n')
        layout.addWidget(QLabel('Message (editable)'))
        self.message=QPlainTextEdit(body);layout.addWidget(self.message)
        if result is None:
            notice=QLabel('No fresh matching Live SSL Checker result. Recheck the website to generate a verification picture.');notice.setWordWrap(True);layout.addWidget(notice)
        else:
            notice=QLabel('The existing SSL Checker picture renderer will generate the PNG automatically.');notice.setWordWrap(True);layout.addWidget(notice)
        buttons=QHBoxLayout()
        for title,fn in [('Open in Outlook',self.open_outlook),('Open Default Email App',self.open_mailto),('Close',self.reject)]:
            b=QPushButton(title);b.clicked.connect(fn);buttons.addWidget(b)
        layout.addLayout(buttons)
    def picture_png(self):
        if self.result is None:return None
        dialog=ExportPictureDialog(self.parent(),self.result)
        # Use persisted verification identity; never require manually selecting a PNG.
        pixmap=dialog._render()
        path=Path(tempfile.gettempdir())/('SSL_Verification_'+uuid.uuid4().hex+'.png')
        if not pixmap.save(str(path),'PNG'):raise OSError('Failed to generate PNG')
        dialog.deleteLater()
        return path
    def open_outlook(self):
        try:
            import win32com.client
            outlook=win32com.client.Dispatch('Outlook.Application')
            mail=outlook.CreateItem(0)
            mail.To=self.recipient.text().strip();mail.Subject=self.subject.text();mail.Body=self.message.toPlainText()
            picture=self.picture_png()
            if picture:mail.Attachments.Add(str(picture))
            mail.Display()
        except Exception as exc:
            QMessageBox.warning(self,'Outlook integration unavailable',
                'Classic Outlook and pywin32 are required for direct image attachment.\n'+str(exc))
    def open_mailto(self):
        from urllib.parse import quote
        # mailto cannot attach files; do not claim otherwise.
        url='mailto:'+quote(self.recipient.text().strip(),safe='@')+'?'+urlencode({'subject':self.subject.text(),'body':self.message.toPlainText()})
        if not QDesktopServices.openUrl(QUrl(url)):
            QMessageBox.warning(self,'Email application unavailable','No default mail application could be opened.')
        if self.result:
            QMessageBox.information(self,'Attachment limitation','Default mail apps cannot receive PNG attachments via mailto. Use Classic Outlook for automatic attachment.')
