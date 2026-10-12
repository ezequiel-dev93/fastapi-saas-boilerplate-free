"""
Paleta de colores oficial del sistema de diseño (Design Tokens).
Sincronizado entre Backend (Emails Jinja2, Dev Tools) y Frontend (Tailwind CSS v4).
"""

from typing import Any, Dict, Final, TypedDict


class DarkPalette(TypedDict):
    postes_black: str
    acid_yellow: str
    hot_orange: str
    flash_white: str
    concrete_gray: str


class LightPalette(TypedDict):
    off_white: str
    smoke_gray: str
    charcoal: str
    neon_lime: str
    acid_green: str


DARK_PALETTE: Final[DarkPalette] = {
    "postes_black": "#111111",
    "acid_yellow": "#D7FF00",
    "hot_orange": "#FF6A00",
    "flash_white": "#FFFFFF",
    "concrete_gray": "#5A5A5A",
}

LIGHT_PALETTE: Final[LightPalette] = {
    "off_white": "#F4F6EC",
    "smoke_gray": "#A6AF68",
    "charcoal": "#171A16",
    "neon_lime": "#9EFF00",
    "acid_green": "#C6FF00",
}

DESIGN_SYSTEM: Final[Dict[str, Any]] = {
    "dark": DARK_PALETTE,
    "light": LIGHT_PALETTE,
}
