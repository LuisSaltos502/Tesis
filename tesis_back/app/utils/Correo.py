import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def send_alert_email(
    *,
    to_email: str,
    subject: str,
    reasons: List[str],
    sensor_mac: str,
    gateway_mac: Optional[str] = None,
    telemetry: Optional[dict] = None,
) -> bool:
    """
    Envía un correo de alerta.
    Retorna True si se envió, False si falló (y loguea el error).
    """

    smtp_host = getattr(settings, "SMTP_HOST", None)
    smtp_port = getattr(settings, "SMTP_PORT", None)
    smtp_user = getattr(settings, "SMTP_USER", None)
    smtp_pass = getattr(settings, "SMTP_PASSWORD", None)
    from_name = getattr(settings, "SMTP_FROM_NAME", "Tesis Water Monitor")

    if not all([smtp_host, smtp_port, smtp_user, smtp_pass]):
        logger.error("[EMAIL] Faltan variables SMTP en .env (HOST/PORT/USER/PASSWORD).")
        return False

    # Construcción del correo
    msg = MIMEMultipart()
    msg["From"] = f"{from_name} <{smtp_user}>"
    msg["To"] = to_email
    msg["Subject"] = subject

    reasons_text = "\n".join(f"- {r}" for r in reasons) if reasons else "- (sin detalle)"
    body_lines = [
        "Se detectó una condición anómala en un sensor del sistema de monitoreo.",
        "",
        f"Sensor MAC: {sensor_mac}",
    ]
    if gateway_mac:
        body_lines.append(f"Gateway MAC: {gateway_mac}")

    body_lines.append("")
    body_lines.append("Razones detectadas:")
    body_lines.append(reasons_text)

    if telemetry:
        body_lines.append("")
        body_lines.append("Última telemetría recibida:")
        for k, v in telemetry.items():
            body_lines.append(f"- {k}: {v}")

    body_lines.append("")
    body_lines.append("Este es un mensaje automático.")

    msg.attach(MIMEText("\n".join(body_lines), "plain", "utf-8"))

    # Envío SMTP
    try:
        with smtplib.SMTP(smtp_host, int(smtp_port), timeout=15) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [to_email], msg.as_string())

        logger.info("[EMAIL] Enviado a=%s sensor=%s", to_email, sensor_mac)
        return True

    except Exception as e:
        logger.exception("[EMAIL] Falló envío a=%s sensor=%s err=%s", to_email, sensor_mac, e)
        return False
