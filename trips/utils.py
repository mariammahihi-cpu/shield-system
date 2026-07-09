"""
دوال مساعدة لمنظومة Shield.
حالياً: توليد صورة QR Code كـ base64 لعرضها في صفحة تفاصيل الرحلة.
"""
import io
import base64
import qrcode


def generate_qr_code_base64(data: str) -> str:
    """
    تُحوّل نصاً (رابط المسح) إلى صورة QR وتُرجعها كسلسلة base64
    جاهزة للعرض مباشرة داخل وسم <img> في القالب.
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')

