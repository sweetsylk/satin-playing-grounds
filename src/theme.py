"""
Style and themes and stuff
"""

PINK = "#fc1c6e"
DARK_BG = "#1e1e1e"
PANEL_BG = "#333"
BORDER = "#444"
TEXT = "white"

ACCENT_BUTTON_STYLE = (
    f"font-size: 14px; font-weight: bold; background-color: {PINK}; color: {TEXT};"
)
NEUTRAL_BUTTON_STYLE = (
    f"font-size: 14px; font-weight: bold; background-color: {PANEL_BG}; color: {TEXT};"
)

DRAG_VALUE_BOX_STYLE = f"""
    QLabel {{
        background-color: {DARK_BG};
        border: 1px solid {BORDER};
        border-radius: 4px;
        color: {PINK};
        font-size: 14px;
        font-weight: bold;
        padding: 4px 15px;
    }}
    QLabel:hover {{
        border: 1px solid {PINK};
        background-color: #2a2a2a;
    }}
"""

TAB_WIDGET_STYLE = f"""
    QTabWidget::pane {{
        border: 1px solid {BORDER};
        background: {DARK_BG};
        border-radius: 4px;
    }}
    QTabBar::tab {{
        background: {PANEL_BG};
        color: #aaa;
        padding: 8px 20px;
        font-size: 14px;
        font-weight: bold;
        border: 1px solid {BORDER};
        border-bottom: none;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        background: {DARK_BG};
        color: {PINK};
        border-bottom: 2px solid {DARK_BG};
    }}
    QTabBar::tab:hover:!selected {{
        background: {BORDER};
        color: {TEXT};
    }}
    QWidget {{
        background: {DARK_BG};
        color: {TEXT};
    }}
"""


def toggle_style(is_on: bool) -> str:
    return ACCENT_BUTTON_STYLE if is_on else NEUTRAL_BUTTON_STYLE


def play_button_style(is_active: bool) -> str:
    return ACCENT_BUTTON_STYLE if is_active else NEUTRAL_BUTTON_STYLE