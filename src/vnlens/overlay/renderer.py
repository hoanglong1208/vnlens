from dataclasses import dataclass

from PyQt6.QtCore import QRect, Qt
from PyQt6.QtGui import QColor, QFont, QPainter

from ..config.schema import OverlayConfig

_BG_COLOR = QColor(10, 10, 20)
_ACCENT_COLOR = QColor(0xE9, 0x45, 0x60)
ACCENT_WIDTH = 3
PADDING_X = 14
PADDING_Y = 10
_RADIUS = 6
_SHADOW_OFFSET = 1


@dataclass
class TextStyle:
    font_size: int
    text_color: QColor
    bg_opacity: float
    shadow: bool

    @classmethod
    def from_config(cls, config: OverlayConfig) -> "TextStyle":
        return cls(
            font_size=config.font_size,
            text_color=QColor(config.text_color),
            bg_opacity=config.opacity,
            shadow=config.shadow,
        )


def font_for(style: TextStyle) -> QFont:
    font = QFont("Noto Sans")
    font.setPixelSize(style.font_size)
    return font


def draw(painter: QPainter, rect: QRect, text: str, style: TextStyle) -> None:
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    bg = QColor(_BG_COLOR)
    bg.setAlphaF(style.bg_opacity)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(bg)
    painter.drawRoundedRect(rect, _RADIUS, _RADIUS)

    accent = QRect(rect.left(), rect.top(), ACCENT_WIDTH, rect.height())
    painter.setBrush(_ACCENT_COLOR)
    painter.drawRect(accent)

    text_rect = rect.adjusted(
        ACCENT_WIDTH + PADDING_X, PADDING_Y, -PADDING_X, -PADDING_Y
    )
    painter.setFont(font_for(style))
    # AlignTop so text longer than the 3-line cap loses its tail, not both ends.
    flags = int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop) | int(
        Qt.TextFlag.TextWordWrap
    )

    if style.shadow:
        shadow_rect = text_rect.translated(_SHADOW_OFFSET, _SHADOW_OFFSET)
        painter.setPen(QColor(0, 0, 0, 200))
        painter.drawText(shadow_rect, flags, text)

    painter.setPen(style.text_color)
    painter.drawText(text_rect, flags, text)
