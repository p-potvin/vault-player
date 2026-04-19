"""
Centralized Theme Manager for VaultWares projects.

Synced from: https://github.com/p-potvin/vault-themes (Brand/theme_manager.py)

Handles theme definitions, validation, accessibility checks,
and token export helpers for UI consumers.

Rules (from vault-themes AGENTS.md):
  - Never hardcode ad-hoc colors; always use a named theme token.
  - Theme mode must be explicit: 'light' or 'dark'.
  - Every theme must define at least 'background' and 'accent' role colors.
  - WCAG AA body text contrast target: >= 4.5:1.
  - WCAG AA large text/UI contrast target: >= 3.0:1.
  - Theme names are Title Case; IDs are kebab-case.
"""

from dataclasses import dataclass
from typing import List, Dict
import re


@dataclass
class VaultTheme:
    name: str
    mode: str
    primary: str
    accent: str
    slug: str


class VaultThemeManager:
    """
    Centralized Theme manager for VaultWares projects.
    Handles theme definitions, validation, accessibility checks,
    and token export helpers for UI consumers.
    """
    _HEX_COLOR_PATTERN = re.compile(r"^#(?:[0-9a-fA-F]{6})$")

    def __init__(self):
        self._themes = [
            VaultTheme("Vintage Velvet", "light", "#F5F5DC", "#800020", "vintage-velvet"),
            VaultTheme("Cyberpunk Cinder", "dark", "#073642", "#CB4B16", "cyberpunk-cinder"),
            VaultTheme("Golden Slate", "dark", "#4A5459", "#D4AF37", "golden-slate"),
            VaultTheme("Modern Monolith", "light", "#FAF9F6", "#333333", "modern-monolith"),
            VaultTheme("Crimson Bloom", "dark", "#8B0000", "#FFC0CB", "crimson-bloom"),
            VaultTheme("Ocean Mist", "light", "#D3D3D3", "#006994", "ocean-mist"),
            VaultTheme("Neon Void", "dark", "#222222", "#00FFFF", "neon-void"),
            VaultTheme("Royal Tangerine", "dark", "#4B0082", "#F28500", "royal-tangerine"),
            VaultTheme("Amethyst Frost", "light", "#FDFDFD", "#800080", "amethyst-frost"),
        ]

    def get_themes(self) -> List[VaultTheme]:
        return self._themes

    def get_theme(self, index: int) -> VaultTheme:
        if 0 <= index < len(self._themes):
            return self._themes[index]
        return self._themes[1]  # Default to Cyberpunk Cinder (index 1)

    def get_theme_by_slug(self, slug: str) -> VaultTheme:
        normalized = slug.strip().lower()
        for theme in self._themes:
            if theme.slug == normalized:
                return theme
        return self._themes[1]  # Default to Cyberpunk Cinder

    def validate_theme(self, theme: VaultTheme) -> bool:
        if theme.mode not in {"light", "dark"}:
            return False
        if not self._HEX_COLOR_PATTERN.match(theme.primary):
            return False
        if not self._HEX_COLOR_PATTERN.match(theme.accent):
            return False
        return True

    def export_theme_tokens(self, theme: VaultTheme) -> Dict[str, str]:
        """
        Returns a token map that can be consumed by UI layers.
        """
        if not self.validate_theme(theme):
            theme = self._themes[1]

        background = theme.primary
        surface = self._blend_hex(theme.primary, theme.accent, 0.08)
        surface_elevated = self._blend_hex(theme.primary, theme.accent, 0.14)

        if theme.mode == "dark":
            text_primary = "#F8FAFC"
            text_secondary = "#CBD5E1"
            border_subtle = self._blend_hex(theme.primary, "#FFFFFF", 0.18)
            focus_ring = self._blend_hex(theme.accent, "#FFFFFF", 0.22)
        else:
            text_primary = "#111827"
            text_secondary = "#4B5563"
            border_subtle = self._blend_hex(theme.primary, "#111827", 0.12)
            focus_ring = self._blend_hex(theme.accent, "#111827", 0.15)

        return {
            "theme_name": theme.name,
            "theme_slug": theme.slug,
            "mode": theme.mode,
            "background": background,
            "surface": surface,
            "surface_elevated": surface_elevated,
            "text_primary": text_primary,
            "text_secondary": text_secondary,
            "accent": theme.accent,
            "accent_hover": self._blend_hex(theme.accent, "#000000", 0.14) if theme.mode == "light" else self._blend_hex(theme.accent, "#FFFFFF", 0.14),
            "border_subtle": border_subtle,
            "focus_ring": focus_ring,
            "success": "#16A34A",
            "warning": "#D97706",
            "danger": "#DC2626",
        }

    def check_contrast(self, background_hex: str, foreground_hex: str) -> Dict[str, float | bool]:
        """
        Returns contrast ratio and WCAG AA pass/fail checks.
        """
        bg = self._hex_to_rgb(background_hex)
        fg = self._hex_to_rgb(foreground_hex)
        ratio = self._contrast_ratio(bg, fg)
        return {
            "ratio": ratio,
            "aa_text": ratio >= 4.5,
            "aa_large": ratio >= 3.0,
        }

    @staticmethod
    def get_glass_rgba(hex_color: str, alpha: int) -> str:
        """Converts hex to rgba for glass-ui elements."""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f"rgba({r}, {g}, {b}, {alpha})"

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
        cleaned = hex_color.strip().lstrip("#")
        if len(cleaned) != 6:
            raise ValueError(f"Invalid hex color: {hex_color}")
        return tuple(int(cleaned[i:i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def _blend_hex(base_hex: str, mix_hex: str, ratio: float) -> str:
        base_r, base_g, base_b = VaultThemeManager._hex_to_rgb(base_hex)
        mix_r, mix_g, mix_b = VaultThemeManager._hex_to_rgb(mix_hex)

        r = round(base_r + (mix_r - base_r) * ratio)
        g = round(base_g + (mix_g - base_g) * ratio)
        b = round(base_b + (mix_b - base_b) * ratio)

        return f"#{r:02X}{g:02X}{b:02X}"

    @staticmethod
    def _relative_luminance(rgb: tuple[int, int, int]) -> float:
        def channel_to_linear(value: int) -> float:
            c = value / 255.0
            if c <= 0.03928:
                return c / 12.92
            return ((c + 0.055) / 1.055) ** 2.4

        r, g, b = rgb
        r_lin = channel_to_linear(r)
        g_lin = channel_to_linear(g)
        b_lin = channel_to_linear(b)

        return (0.2126 * r_lin) + (0.7152 * g_lin) + (0.0722 * b_lin)

    @staticmethod
    def _contrast_ratio(rgb_a: tuple[int, int, int], rgb_b: tuple[int, int, int]) -> float:
        lum_a = VaultThemeManager._relative_luminance(rgb_a)
        lum_b = VaultThemeManager._relative_luminance(rgb_b)
        lighter = max(lum_a, lum_b)
        darker = min(lum_a, lum_b)
        return round((lighter + 0.05) / (darker + 0.05), 2)
