import base64
import logging
from io import BytesIO


logger = logging.getLogger(__name__)


def generate_qr_data_uri(payload: str) -> str | None:
    """Generate a PNG QR code as a data URI for embedding in HTML.

    Returns None if the qrcode dependency is not available.
    """
    try:
        import qrcode
    except Exception as exc:
        logger.warning("QR code library not available: %s", exc)
        return None

    try:
        qr = qrcode.QRCode(version=1, box_size=6, border=2)
        qr.add_data(payload)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        data_uri = f"data:image/png;base64,{encoded}"
        logger.info("Generated QR data URI for payload length=%d", len(payload or ""))
        return data_uri
    except Exception as exc:
        logger.exception("Failed to generate QR data URI: %s", exc)
        return None


