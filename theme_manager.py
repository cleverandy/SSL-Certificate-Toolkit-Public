"""Application-wide appearance and accent tokens, shared by Qt dialogs and widgets."""
ACCENTS = {
    'system': {'name': 'System', 'light': '#0078D4', 'dark': '#60CDFF'},
    'blue': {'name': 'Blue', 'light': '#2563EB', 'dark': '#60A5FA'},
    'cyan': {'name': 'Cyan', 'light': '#0891B2', 'dark': '#22D3EE'},
    'teal': {'name': 'Teal', 'light': '#0F766E', 'dark': '#2DD4BF'},
    'green': {'name': 'Green', 'light': '#059669', 'dark': '#34D399'},
    'purple': {'name': 'Purple', 'light': '#7C3AED', 'dark': '#A78BFA'},
    'pink': {'name': 'Pink', 'light': '#DB2777', 'dark': '#F472B6'},
    'red': {'name': 'Red', 'light': '#DC2626', 'dark': '#F87171'},
    'orange': {'name': 'Orange', 'light': '#EA580C', 'dark': '#FB923C'},
    'gold': {'name': 'Gold', 'light': '#CA8A04', 'dark': '#FACC15'},
    'slate': {'name': 'Slate', 'light': '#475569', 'dark': '#94A3B8'},
}


def windows_accent_color(dark=False):
    """Read Windows DWM colorization color; gracefully fall back elsewhere."""
    import sys
    if sys.platform == 'win32':
        try:
            import ctypes
            color = ctypes.c_uint32()
            opaque = ctypes.c_int()
            hr = ctypes.windll.dwmapi.DwmGetColorizationColor(
                ctypes.byref(color), ctypes.byref(opaque))
            if hr == 0:
                rgb = color.value & 0xFFFFFF
                if rgb not in (0x000000, 0xFFFFFF):
                    return f'#{rgb:06X}'
        except (AttributeError, OSError, ValueError):
            pass
    return '#60CDFF' if dark else '#0078D4'

class ThemeManager:
    def __init__(self,settings):
        self.settings=settings
        self.accent_name=settings.value('appearance/accent','system',type=str)
        if self.accent_name not in ACCENTS:self.accent_name='system'
        self.accent_name = {'violet':'purple', 'amber':'orange'}.get(self.accent_name,self.accent_name)
    def set_accent(self,name):
        if name not in ACCENTS:return
        self.accent_name=name
        self.settings.setValue('appearance/accent',name)
    def accent(self,dark):
        return (windows_accent_color(dark) if self.accent_name == 'system'
                else ACCENTS[self.accent_name]['dark' if dark else 'light'])
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
