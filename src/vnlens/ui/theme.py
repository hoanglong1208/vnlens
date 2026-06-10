BG = "#1a1a2e"
SIDEBAR_BG = "#16162a"
SURFACE = "#222742"
BORDER = "#2e3458"
ACCENT = "#e94560"
ACCENT_HOVER = "#f25c75"
TEXT = "#eaeaea"
TEXT_DIM = "#8892a4"

QSS = f"""
QDialog, QWizard {{
    background: {BG};
}}
QLabel {{
    color: {TEXT};
    background: transparent;
}}
QLabel[dim="true"] {{
    color: {TEXT_DIM};
}}
QLabel#pageTitle {{
    font-size: 17px;
    font-weight: 600;
}}
QLabel#brand {{
    font-size: 19px;
    font-weight: 700;
    color: {ACCENT};
}}

QMenu {{
    background: {SIDEBAR_BG};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 4px;
}}
QMenu::item {{
    padding: 7px 26px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background: {ACCENT};
    color: white;
}}
QMenu::item:disabled {{
    color: {TEXT_DIM};
}}
QMenu::separator {{
    height: 1px;
    background: {BORDER};
    margin: 4px 8px;
}}

QPushButton {{
    background: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 7px 18px;
}}
QPushButton:hover {{
    border-color: {ACCENT};
    color: white;
}}
QPushButton:pressed {{
    background: {BORDER};
}}
QPushButton:disabled {{
    color: {TEXT_DIM};
}}
QPushButton#primary {{
    background: {ACCENT};
    border: none;
    color: white;
    font-weight: 600;
    padding: 7px 26px;
}}
QPushButton#primary:hover {{
    background: {ACCENT_HOVER};
}}

QLineEdit, QComboBox {{
    background: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: {ACCENT};
}}
QLineEdit:focus, QComboBox:focus {{
    border-color: {ACCENT};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    background: {SIDEBAR_BG};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 6px;
    selection-background-color: {ACCENT};
    outline: none;
}}

QListWidget#nav {{
    background: transparent;
    border: none;
    outline: none;
}}
QListWidget#nav::item {{
    min-height: 38px;
    padding-left: 14px;
    border-left: 3px solid transparent;
    color: {TEXT_DIM};
}}
QListWidget#nav::item:hover {{
    background: rgba(233, 69, 96, 0.08);
    color: {TEXT};
}}
QListWidget#nav::item:selected {{
    background: rgba(233, 69, 96, 0.16);
    border-left: 3px solid {ACCENT};
    color: white;
}}

QCheckBox, QRadioButton {{
    color: {TEXT};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {BORDER};
    border-radius: 4px;
    background: {SURFACE};
}}
QCheckBox::indicator:hover {{
    border-color: {ACCENT};
}}
QCheckBox::indicator:checked {{
    background: {ACCENT};
    border-color: {ACCENT};
}}
QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border: 1px solid {BORDER};
    border-radius: 8px;
    background: {SURFACE};
}}
QRadioButton::indicator:hover {{
    border-color: {ACCENT};
}}
QRadioButton::indicator:checked {{
    border: 5px solid {ACCENT};
    background: white;
}}

QSlider::groove:horizontal {{
    height: 4px;
    background: {BORDER};
    border-radius: 2px;
}}
QSlider::sub-page:horizontal {{
    height: 4px;
    background: {ACCENT};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: white;
    width: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}
QSlider::handle:horizontal:hover {{
    background: {ACCENT_HOVER};
}}

QFrame#divider {{
    background: {BORDER};
    max-height: 1px;
    border: none;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 8px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QToolTip {{
    background: {SIDEBAR_BG};
    color: {TEXT};
    border: 1px solid {BORDER};
    padding: 4px 8px;
}}
"""
