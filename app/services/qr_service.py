# =========================================================
# QR Code Service
# =========================================================

from pathlib import Path
from flask import current_app
import qrcode
from PIL import Image, ImageDraw, ImageFont

from app.business_types import (
    get_business_type,
)


# =========================================================
# Generate Simple QR Code
# =========================================================

def generate_qr_code(url, filename):

    upload_folder = Path(
        "app/static/uploads/qr"
    )

    upload_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )

    qr.add_data(url)
    qr.make(fit=True)

    image = qr.make_image(
        fill_color="black",
        back_color="white"
    )

    file_path = upload_folder / filename

    image.save(file_path)

    return f"uploads/qr/{filename}"


# =========================================================
# Generate QR Printable Card
# =========================================================

def generate_qr_card(
    url,
    business_name,
    business_type,
    filename
):

    upload_folder = Path(
        "app/static/uploads/qr"
    )

    upload_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    # =====================================================
    # Business Theme
    # =====================================================

    business_config = get_business_type(
        business_type
    )

    theme = business_config["theme"]

    primary_color = theme["primary"]
    primary_dark_color = theme["primary_dark"]
    primary_light_color = theme["primary_light"]

    type_name = business_config["name"]
    type_icon = business_config["icon"]

    # =====================================================
    # QR Code
    # =====================================================

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=4,
    )

    qr.add_data(url)
    qr.make(fit=True)

    qr_image = qr.make_image(
        fill_color="black",
        back_color="white"
    ).convert("RGB")

    # =====================================================
    # Card Size
    # =====================================================

    card_width = 1000
    card_height = 1250

    card = Image.new(
        "RGB",
        (
            card_width,
            card_height
        ),
        "white"
    )

    draw = ImageDraw.Draw(card)

    # =====================================================
    # Fonts
    # =====================================================

    font_folder = Path(
        "app/static/font"
    )

    bold_font_path = (
        font_folder /
        "Vazirmatn-Bold.woff2"
    )

    regular_font_path = (
        font_folder /
        "Vazirmatn-Regular.woff2"
    )

    if bold_font_path.exists():

        title_font = ImageFont.truetype(
            str(bold_font_path),
            55
        )

        type_font = ImageFont.truetype(
            str(bold_font_path),
            32
        )

        guide_font = ImageFont.truetype(
            str(bold_font_path),
            30
        )

    else:

        title_font = ImageFont.load_default()
        type_font = ImageFont.load_default()
        guide_font = ImageFont.load_default()

    if regular_font_path.exists():

        text_font = ImageFont.truetype(
            str(regular_font_path),
            28
        )

    else:

        text_font = ImageFont.load_default()

    # =====================================================
    # Main Card Border / Background
    # =====================================================

    draw.rounded_rectangle(
        (
            20,
            20,
            card_width - 20,
            card_height - 20
        ),
        radius=45,
        fill="white",
        outline=primary_light_color,
        width=4
    )

    # =====================================================
    # Header
    # =====================================================

    header_height = 190

    draw.rounded_rectangle(
        (
            20,
            20,
            card_width - 20,
            header_height
        ),
        radius=45,
        fill=primary_color
    )

    # پایین هدر را صاف می‌کنیم تا گوشه پایین گرد نباشد
    draw.rectangle(
        (
            20,
            header_height - 45,
            card_width - 20,
            header_height
        ),
        fill=primary_color
    )
 
    # =====================================================
    # Business Name
    # =====================================================

    # حداکثر عرض مجاز نام
    max_title_width = 850

    # اندازه اولیه فونت
    title_size = 55

    # کوچک کردن فونت برای نام‌های بلند
    while title_size >= 32:

        if bold_font_path.exists():

            current_title_font = ImageFont.truetype(
                str(bold_font_path),
                title_size
            )

        else:

            current_title_font = ImageFont.load_default()

        title_box = draw.textbbox(
            (0, 0),
            business_name,
            font=current_title_font
        )

        title_width = (
            title_box[2] -
            title_box[0]
        )

        if title_width <= max_title_width:
            break

        title_size -= 2

    draw.text(
        (
            (card_width - title_width) / 2,
            60

        ),
        business_name,
        fill="white",
        font=current_title_font
    )

    # =====================================================
    # QR Area
    # =====================================================

    qr_size = 690

    qr_image = qr_image.resize(
        (
            qr_size,
            qr_size
        )
    )

    qr_x = (
        card_width -
        qr_size
    ) // 2

    qr_y = 230

# =====================================================
# QR Frame
# =====================================================

    qr_frame_padding = 22

    # قاب سفید با حاشیه رنگ کسب‌وکار
    draw.rounded_rectangle(
        (
            qr_x - qr_frame_padding,
            qr_y - qr_frame_padding,
            qr_x + qr_size + qr_frame_padding,
            qr_y + qr_size + qr_frame_padding
        ),
        radius=28,
        fill="white",
        outline=primary_color,
        width=5
    )

    # قرار دادن QR روی قاب
    card.paste(
        qr_image,
        (
            qr_x,
            qr_y
        )
    )
    # =====================================================
    # Scan Guide
    # =====================================================

    guide_text = (
        "برای مشاهده منو اسکن کنید"
    )
     
    guide_box = draw.textbbox(
        (0, 0),
        guide_text,
        font=guide_font
    )

    guide_width = (
        guide_box[2] -
        guide_box[0]
    )

    draw.text(
        (
            (card_width - guide_width) / 2,
           995    
        ),
        guide_text,
        fill=primary_dark_color,
        font=guide_font
    )
     # =====================================================
    # Footer / Platform Advertisement
    # =====================================================

    # نام سامانه
   # نام سامانه
    platform_name = "MenuCi"

    # شعار تبلیغاتی کوتاه و ظریف
    platform_slogan = "منوی دیجیتال، ساده و حرفه‌ای"

    # آدرس سایت از تنظیمات پروژه
    platform_url = current_app.config["MENUCI_URL"]

    # -----------------------------------------------------
    # Footer Accent Line
    # -----------------------------------------------------

    footer_line_y = 1095

    draw.rounded_rectangle(
        (
            180,
            footer_line_y,
            card_width - 180,
            footer_line_y + 7
        ),
        radius=4,
        fill=primary_color
    )

    # -----------------------------------------------------
    # Platform Name
    # -----------------------------------------------------

    platform_name_font = (
        ImageFont.truetype(
            str(bold_font_path),
            24
        )
        if bold_font_path.exists()
        else ImageFont.load_default()
    )

    name_box = draw.textbbox(
        (0, 0),
        platform_name,
        font=platform_name_font
    )

    name_width = (
        name_box[2] -
        name_box[0]
    )

    draw.text(
        (
            (card_width - name_width) / 2,
            1120
        ),
        platform_name,
        fill=primary_dark_color,
        font=platform_name_font
    )

    # -----------------------------------------------------
    # Platform Slogan
    # -----------------------------------------------------

    slogan_font = (
        ImageFont.truetype(
            str(regular_font_path),
            18
        )
        if regular_font_path.exists()
        else ImageFont.load_default()
    )

    slogan_box = draw.textbbox(
        (0, 0),
        platform_slogan,
        font=slogan_font
    )

    slogan_width = (
        slogan_box[2] -
        slogan_box[0]
    )

    draw.text(
        (
            (card_width - slogan_width) / 2,
            1152
        ),
        platform_slogan,
        fill="#888888",
        font=slogan_font
    )

    # -----------------------------------------------------
    # Platform Website
    # -----------------------------------------------------

    website_font = (
        ImageFont.truetype(
            str(bold_font_path),
            19
        )
        if bold_font_path.exists()
        else ImageFont.load_default()
    )

    website_box = draw.textbbox(
        (0, 0),
        platform_url,
        font=website_font
    )

    website_width = (
        website_box[2] -
        website_box[0]
    )

    draw.text(
        (
            (card_width - website_width) / 2,
            1180
        ),
        platform_url,
        fill=primary_color,
        font=website_font
    )
    # =====================================================
    # Save
    # =====================================================

    file_path = (
        upload_folder /
        filename
    )

    card.save(
        file_path,
        "PNG"
    )

    return f"uploads/qr/{filename}"