"""Application-wide appearance and accent tokens, shared by Qt dialogs and widgets."""
ACCENTS={
 'blue':{'name':'Ocean Blue','light':'#2563EB','dark':'#60A5FA'},
 'teal':{'name':'Teal','light':'#0F766E','dark':'#2DD4BF'},
 'violet':{'name':'Violet','light':'#7C3AED','dark':'#A78BFA'},
 'amber':{'name':'Amber','light':'#B45309','dark':'#FBBF24'},
 'slate':{'name':'Slate','light':'#475569','dark':'#94A3B8'},
}
class ThemeManager:
    def __init__(self,settings):
        self.settings=settings
        self.accent_name=settings.value('appearance/accent','blue',type=str)
        if self.accent_name not in ACCENTS:self.accent_name='blue'
    def set_accent(self,name):
        if name not in ACCENTS:return
        self.accent_name=name
        self.settings.setValue('appearance/accent',name)
    def accent(self,dark):
        return ACCENTS[self.accent_name]['dark' if dark else 'light']
    def stylesheet(self,base,dark):
        # QSS is installed on QApplication, so new dialogs and popup widgets inherit it.
        from app import DARK,LIGHT
        base_color=(DARK if dark else LIGHT)['brand']
        accent=self.accent(dark)
        base=base.replace(base_color,accent)
        selected='#344C62' if dark else '#E6EDFF'
        return base+f'''
        QWidget#appearanceGroup {{background: {'#253449' if dark else '#E2EAF4'};border-radius:8px;}}
        QPushButton#appearanceOption {{border:0;background:transparent;border-radius:6px;padding:0;}}
        QPushButton#appearanceOption:checked {{background:{selected};border:1px solid {accent};}}
        QPushButton#appearanceOption:hover:!checked {{background:{'#344459' if dark else '#D4E0EF'};}}
        QDialog, QMessageBox, QInputDialog {{background:{'#1B2635' if dark else '#FFFFFF'};}}
        QToolTip {{color:{'#E8EFF9' if dark else '#16243A'};background:{'#243246' if dark else '#FFFFFF'};border:1px solid {accent};}}
        QMenu {{background:{'#1B2635' if dark else '#FFFFFF'};border:1px solid {accent};}}
        QMenu::item:selected {{background:{selected};}}
        '''
