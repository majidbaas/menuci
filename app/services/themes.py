THEMES = {
    "restaurant": {
        "primary": "#9f1239",
        "primary_light": "#fff1f2",
        "background": "#fffaf5",
        "text": "#292524",
        "muted": "#78716c",
    },

    "cafe": {
        "primary": "#92400e",
        "primary_light": "#fffbeb",
        "background": "#faf7f2",
        "text": "#292524",
        "muted": "#78716c",
    },

    "fast_food": {
        "primary": "#dc2626",
        "primary_light": "#fef2f2",
        "background": "#fff7ed",
        "text": "#292524",
        "muted": "#78716c",
    },

    "juice_icecream": {
        "primary": "#16a34a",
        "primary_light": "#f0fdf4",
        "background": "#f7fee7",
        "text": "#1c1917",
        "muted": "#78716c",
    },

    "pastry": {
        "primary": "#db2777",
        "primary_light": "#fdf2f8",
        "background": "#fff7fb",
        "text": "#292524",
        "muted": "#78716c",
    },

    "bakery": {
        "primary": "#a16207",
        "primary_light": "#fefce8",
        "background": "#fffbeb",
        "text": "#292524",
        "muted": "#78716c",
    },

    "barbershop": {
        "primary": "#111827",
        "primary_light": "#f3f4f6",
        "background": "#f9fafb",
        "text": "#111827",
        "muted": "#6b7280",
    },

    "store": {
        "primary": "#2563eb",
        "primary_light": "#eff6ff",
        "background": "#f8fafc",
        "text": "#1e293b",
        "muted": "#64748b",
    },
}


DEFAULT_THEME = {
    "primary": "#2563eb",
    "primary_light": "#eff6ff",
    "background": "#f8fafc",
    "text": "#1e293b",
    "muted": "#64748b",
}


def get_theme(business_type):
    return THEMES.get(
        business_type,
        DEFAULT_THEME
    )