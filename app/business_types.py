# app/config/business_types.py

"""
تنظیمات مرکزی انواع کسب‌وکار

تمام اطلاعات مربوط به نوع کسب‌وکارها در این فایل نگهداری می‌شود
تا در بخش‌های مختلف پروژه از یک مرجع مشترک استفاده شود.

در آینده می‌توان اطلاعات بیشتری مثل:
- تصویر پیش‌فرض
- تصویر هدر
- آیکون
- فونت
- تم
- دسته‌بندی‌های پیشنهادی
- متن‌های پیش‌فرض
و ... را به هر نوع کسب‌وکار اضافه کرد.
"""


BUSINESS_TYPES = {

    "restaurant": {
        "name": "رستوران",
        "icon": "🍽️",

        "theme": {
            "primary": "#dc2648",
            "primary_dark": "#b91c1c",
            "primary_light": "#fef2f2",
            "accent": "#f97316",
        },

        "default_image": None,
        "default_description": None,
        "suggested_categories": [],
    },


    "cafe": {
        "name": "کافه شاپ",
        "icon": "☕",

        "theme": {
            "primary": "#8b5e3c",
            "primary_dark": "#6f4528",
            "primary_light": "#faf5f0",
            "accent": "#d4a373",
        },

        "default_image": None,
        "default_description": None,
        "suggested_categories": [],
    },


    "fastfood": {
        "name": "فست‌فود",
        "icon": "🍔",

        "theme": {
            "primary": "#f97316",
            "primary_dark": "#ea580c",
            "primary_light": "#fff7ed",
            "accent": "#dc2626",
        },

        "default_image": None,
        "default_description": None,
        "suggested_categories": [],
    },


    "juice": {
        "name": "آبمیوه و بستنی",
        "icon": "🧃",

        "theme": {
            "primary": "#0d9488",
            "primary_dark": "#0f766e",
            "primary_light": "#f0fdfa",
            "accent": "#22c55e",
        },

        "default_image": None,
        "default_description": None,
        "suggested_categories": [],
    },


    "bakery": {
        "name": "نانوایی",
        "icon": "🥖",

        "theme": {
            "primary": "#b45309",
            "primary_dark": "#92400e",
            "primary_light": "#fffbeb",
            "accent": "#f59e0b",
        },

        "default_image": None,
        "default_description": None,
        "suggested_categories": [],
    },


    "pastry": {
        "name": "قنادی و شیرینی‌فروشی",
        "icon": "🍰",

        "theme": {
            "primary": "#db2777",
            "primary_dark": "#be185d",
            "primary_light": "#fdf2f8",
            "accent": "#a855f7",
        },

        "default_image": None,
        "default_description": None,
        "suggested_categories": [],
    },


    "beauty": {
        "name": "آرایشگاه و زیبایی",
        "icon": "💇",

        "theme": {
            "primary": "#b08d57",
            "primary_dark": "#8c6b35",
            "primary_light": "#faf7f0",
            "accent": "#111827",
        },

        "default_image": None,
        "default_description": None,
        "suggested_categories": [],
    },


    "shop": {
        "name": "فروشگاه",
        "icon": "🛍️",

        "theme": {
            "primary": "#2563eb",
            "primary_dark": "#1d4ed8",
            "primary_light": "#eff6ff",
            "accent": "#7c3aed",
        },

        "default_image": None,
        "default_description": None,
        "suggested_categories": [],
    },


    "pharmacy": {
        "name": "داروخانه",
        "icon": "💊",

        "theme": {
            "primary": "#059669",
            "primary_dark": "#047857",
            "primary_light": "#ecfdf5",
            "accent": "#0d9488",
        },

        "default_image": None,
        "default_description": None,
        "suggested_categories": [],
    },


    "services": {
        "name": "خدماتی",
        "icon": "🔧",

        "theme": {
            "primary": "#475569",
            "primary_dark": "#334155",
            "primary_light": "#f8fafc",
            "accent": "#2563eb",
        },

        "default_image": None,
        "default_description": None,
        "suggested_categories": [],
    },


    "other": {
        "name": "سایر",
        "icon": "📦",

        "theme": {
            "primary": "#6366f1",
            "primary_dark": "#4f46e5",
            "primary_light": "#eef2ff",
            "accent": "#8b5cf6",
        },

        "default_image": None,
        "default_description": None,
        "suggested_categories": [],
    },

}


# ---------------------------------------------------------
# توابع کمکی
# ---------------------------------------------------------

def get_business_type(business_type):
    """
    دریافت تنظیمات یک نوع کسب‌وکار.
    اگر نوع ناشناخته باشد، تنظیمات 'other' برگردانده می‌شود.
    """

    return BUSINESS_TYPES.get(
        business_type,
        BUSINESS_TYPES["other"]
    )


def get_business_type_name(business_type):
    """
    دریافت نام فارسی نوع کسب‌وکار.
    """

    return get_business_type(business_type)["name"]


def get_business_type_icon(business_type):
    """
    دریافت آیکون نوع کسب‌وکار.
    """

    return get_business_type(business_type)["icon"]


def get_business_type_theme(business_type):
    """
    دریافت تنظیمات رنگ و تم.
    """

    return get_business_type(business_type)["theme"]


def get_business_type_choices():
    """
    آماده‌سازی لیست انواع کسب‌وکار برای استفاده در فرم‌ها.

    خروجی:
    [
        {
            "value": "restaurant",
            "name": "رستوران",
            "icon": "🍽️"
        },
        ...
    ]
    """

    return [
        {
            "value": key,
            "name": data["name"],
            "icon": data["icon"],
        }
        for key, data in BUSINESS_TYPES.items()
    ]