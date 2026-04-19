"""
VaultWares Brand — theme manager and brand token definitions.

Synced from: https://github.com/p-potvin/vault-themes (Brand/)

This package provides the centralized VaultThemeManager and VaultTheme
dataclass used by all VaultWares projects to enforce consistent theming,
WCAG accessibility compliance, and brand token usage.

Usage:
    from Brand.theme_manager import VaultThemeManager

    manager = VaultThemeManager()
    theme = manager.get_theme_by_slug("golden-slate")
    tokens = manager.export_theme_tokens(theme)
"""
