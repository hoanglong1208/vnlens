BG = "#1a1a2e"
SURFACE = "#16213e"
BORDER = "#2a2f55"
ACCENT = "#e94560"
TEXT = "#eaeaea"
TEXT_DIM = "#8892a4"

QSS = f"""
QDialog, QWizard {{
    background: {BG};
}}
QWizard QWidget {{
    background: transparent;
}}
QLabel {{
    color: {TEXT};
}}
QLabel[dim="true"] {{
    color: {TEXT_DIM};
}}
QMenu {{
    background: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
}}
QMenu::item {{
    padding: 6px 24px;
}}
QMenu::item:selected {{
    background: {ACCENT};
}}
QMenu::item:disabled {{
    color: {TEXT_DIM};
}}
QPushButton {{
    background: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 6px 16px;
}}
QPushButton:hover {{
    border-color: {ACCENT};
}}
QPushButton:default {{
    background: {ACCENT};
    border: none;
}}
QPushButton:disabled {{
    color: {TEXT_DIM};
}}
QLineEdit, QComboBox {{
    background: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 5px 8px;
}}
QComboBox QAbstractItemView {{
    background: {SURFACE};
    color: {TEXT};
    selection-background-color: {ACCENT};
}}
QListWidget {{
    background: {SURFACE};
    color: {TEXT};
    border: none;
    outline: none;
}}
QListWidget::item {{
    padding: 10px 16px;
}}
QListWidget::item:selected {{
    background: {ACCENT};
    color: white;
}}
QCheckBox, QRadioButton {{
    color: {TEXT};
}}
QSlider::groove:horizontal {{
    height: 4px;
    background: {BORDER};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {ACCENT};
    width: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}
"""
