"""DJ LAB SIAM — neon dark theme (colors + Qt stylesheet)."""

from __future__ import annotations

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget

# ---- palette ----------------------------------------------------------------
BG_0 = "#0b0b12"       # window base
BG_1 = "#12121c"       # panels
BG_2 = "#1b1b2b"       # raised controls
BORDER = "#2a2a48"

NEON_CYAN = "#00E5FF"
NEON_PINK = "#FF2D95"
NEON_PURPLE = "#7C4DFF"

TEXT = "#E8E8F0"
TEXT_MUTED = "#8A8AA0"

# Semantic colors used in the results tree.
KEEP = QColor("#00E676")     # green  — file being kept
DELETE = QColor("#FF3B6B")   # pink   — marked for deletion
META = QColor("#FFB300")     # amber  — metadata-match group (be careful)

STYLESHEET = f"""
QWidget {{
    background-color: {BG_0};
    color: {TEXT};
    font-size: 13px;
    font-family: "SF Pro Text", "Segoe UI", "Helvetica Neue", sans-serif;
}}
QMainWindow, QDialog {{ background-color: {BG_0}; }}

#appTitle {{ font-size: 21px; font-weight: 800; color: {TEXT}; letter-spacing: 0.5px; }}
#appBrand {{ font-size: 11px; color: {NEON_CYAN}; letter-spacing: 4px; font-weight: 800; }}
#sectionLabel {{ color: {TEXT_MUTED}; font-size: 11px; font-weight: 700; letter-spacing: 1px; }}
#summaryLabel {{ color: #9a9ab5; font-size: 12px; }}
#creditLabel {{ color: #5a5a72; font-size: 11px; font-weight: 700; letter-spacing: 1px; }}
#footerBrand {{ color: #3f3f56; font-size: 11px; font-weight: 700; letter-spacing: 2px; }}

QPushButton {{
    background-color: {BG_2};
    border: 1px solid {BORDER};
    border-radius: 10px;
    padding: 8px 15px;
    color: {TEXT};
}}
QPushButton:hover {{ border-color: {NEON_CYAN}; color: {NEON_CYAN}; }}
QPushButton:pressed {{ background-color: #23233a; }}
QPushButton:disabled {{ color: #55556a; border-color: #22223a; }}

QPushButton#primary {{
    border: 0px; border-radius: 12px; padding: 10px 24px; font-weight: 800;
    color: {BG_0};
    background-color: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {NEON_CYAN}, stop:1 {NEON_PURPLE});
}}
QPushButton#primary:hover {{
    background-color: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #2af0ff, stop:1 #916bff);
}}
QPushButton#primary:disabled {{ background-color: #23233a; color: #55556a; }}

QPushButton#danger {{
    border: 1px solid {NEON_PINK}; color: #ff6f97; font-weight: 800;
    border-radius: 12px; padding: 10px 22px;
    background-color: rgba(255,45,149,0.08);
}}
QPushButton#danger:hover {{ background-color: rgba(255,45,149,0.20); color: #ffffff; }}
QPushButton#danger:disabled {{ border-color:#3a2230; color:#6a3a4a; background: transparent; }}

QProgressBar {{
    background-color: #16161f; border: 1px solid {BORDER}; border-radius: 8px;
    min-height: 16px; text-align: center; color: #cfcfe0; font-size: 11px;
}}
QProgressBar::chunk {{
    border-radius: 7px;
    background-color: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {NEON_CYAN}, stop:1 {NEON_PINK});
}}

QListWidget, QTreeView {{
    background-color: {BG_1}; border: 1px solid #23233a; border-radius: 10px; outline: 0;
}}
QTreeView::item, QListWidget::item {{ padding: 4px; border-radius: 6px; }}
QTreeView::item:selected, QListWidget::item:selected {{
    background-color: rgba(0,229,255,0.14); color: {TEXT};
}}
QTreeView::item:hover, QListWidget::item:hover {{ background-color: rgba(124,77,255,0.10); }}

QHeaderView::section {{
    background-color: #171725; color: #9a9ab5; padding: 6px 8px; border: 0px;
    border-bottom: 1px solid #23233a; font-weight: 700;
}}

QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{
    width: 16px; height: 16px; border-radius: 4px; border: 1px solid #3a3a55; background: #14141f;
}}
QCheckBox::indicator:checked {{ background: {NEON_CYAN}; border-color: {NEON_CYAN}; }}

QLineEdit {{
    background-color: #14141f; border: 1px solid {BORDER}; border-radius: 8px;
    padding: 6px 10px; color: {TEXT}; selection-background-color: {NEON_PURPLE};
}}
QLineEdit:focus {{ border-color: {NEON_CYAN}; }}

QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #2f2f48; border-radius: 5px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {NEON_CYAN}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: #2f2f48; border-radius: 5px; min-width: 30px; }}

QTextBrowser {{ background-color: {BG_1}; border: 1px solid #23233a; border-radius: 10px; }}
QToolTip {{ background-color: #14141f; color: {TEXT}; border: 1px solid {NEON_CYAN}; padding: 4px; }}
"""


def apply_theme(app) -> None:
    """Apply the DJ LAB SIAM stylesheet to the whole application."""
    app.setStyleSheet(STYLESHEET)


def neon_glow(widget: QWidget, color: str = NEON_CYAN, radius: int = 20) -> None:
    """Attach a soft neon glow (drop shadow with no offset) to a widget."""
    effect = QGraphicsDropShadowEffect(widget)
    effect.setBlurRadius(radius)
    effect.setOffset(0, 0)
    glow = QColor(color)
    glow.setAlpha(200)
    effect.setColor(glow)
    widget.setGraphicsEffect(effect)
