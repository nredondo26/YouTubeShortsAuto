"""Notification system - Desktop push and email notifications."""

import os
import sys
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, List
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

NOTIFICATIONS_FILE = os.path.join(ROOT_DIR, "notifications.json")


def _load_notifications() -> dict:
    """Load notifications config."""
    if os.path.exists(NOTIFICATIONS_FILE):
        with open(NOTIFICATIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "desktop_enabled": True,
        "email_enabled": False,
        "email_config": {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "sender_email": "",
            "sender_password": "",
            "recipient_email": "",
        },
        "notify_on": {
            "video_generated": True,
            "video_uploaded": True,
            "error_occurred": True,
        }
    }


def _save_notifications(data: dict):
    """Save notifications config."""
    with open(NOTIFICATIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_notification_config() -> dict:
    """Get notification configuration."""
    return _load_notifications()


def update_notification_config(config: dict):
    """Update notification configuration."""
    _save_notifications(config)


def send_desktop_notification(title: str, message: str, urgency: str = "normal") -> bool:
    """Send a desktop notification.
    
    Args:
        title: Notification title
        message: Notification message
        urgency: 'low', 'normal', or 'critical'
    
    Returns:
        True if successful, False otherwise
    """
    config = _load_notifications()
    if not config.get("desktop_enabled", True):
        return False
    
    try:
        # Windows 10/11 toast notifications
        if sys.platform == "win32":
            try:
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(
                    title,
                    message,
                    duration=10,
                    threaded=True
                )
                return True
            except ImportError:
                # Fallback to PowerShell notification
                ps_script = f'''
                [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
                [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom, ContentType = WindowsRuntime] | Out-Null
                
                $template = @"
                <toast>
                    <visual>
                        <binding template="ToastText02">
                            <text id="1">{title}</text>
                            <text id="2">{message}</text>
                        </binding>
                    </visual>
                </toast>
                "@
                
                $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
                $xml.LoadXml($template)
                $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
                [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("YouTubeShortsAuto").Show($toast)
                '''
                import subprocess
                subprocess.run(["powershell", "-Command", ps_script], capture_output=True)
                return True
        
        # macOS notifications
        elif sys.platform == "darwin":
            import subprocess
            subprocess.run([
                "osascript", "-e",
                f'display notification "{message}" with title "{title}"'
            ])
            return True
        
        # Linux notifications
        else:
            import subprocess
            subprocess.run([
                "notify-send", title, message
            ])
            return True
            
    except Exception as e:
        print(f"Desktop notification error: {e}")
        return False


def send_email_notification(subject: str, body: str, is_html: bool = False) -> bool:
    """Send an email notification.
    
    Args:
        subject: Email subject
        body: Email body (plain text or HTML)
        is_html: Whether body is HTML
    
    Returns:
        True if successful, False otherwise
    """
    config = _load_notifications()
    if not config.get("email_enabled", False):
        return False
    
    email_config = config.get("email_config", {})
    smtp_server = email_config.get("smtp_server", "")
    smtp_port = email_config.get("smtp_port", 587)
    sender_email = email_config.get("sender_email", "")
    sender_password = email_config.get("sender_password", "")
    recipient_email = email_config.get("recipient_email", "")
    
    if not all([smtp_server, sender_email, sender_password, recipient_email]):
        return False
    
    try:
        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject
        
        if is_html:
            msg.attach(MIMEText(body, "html"))
        else:
            msg.attach(MIMEText(body, "plain"))
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        print(f"Email notification error: {e}")
        return False


def notify_video_generated(topic: str, account: str, video_path: str = ""):
    """Send notification when video is generated."""
    config = _load_notifications()
    if not config.get("notify_on", {}).get("video_generated", True):
        return
    
    title = "Video Generado"
    message = f"Nuevo video generado: {topic}\nCuenta: {account}"
    
    send_desktop_notification(title, message)
    send_email_notification(
        subject=f"YouTubeShortsAuto: {title}",
        body=f"<h2>{title}</h2><p>{message}</p><p>Ruta: {video_path}</p>",
        is_html=True
    )


def notify_video_uploaded(title: str, url: str, account: str):
    """Send notification when video is uploaded."""
    config = _load_notifications()
    if not config.get("notify_on", {}).get("video_uploaded", True):
        return
    
    notification_title = "Video Subido"
    message = f"Video subido: {title}\nURL: {url}\nCuenta: {account}"
    
    send_desktop_notification(notification_title, message)
    send_email_notification(
        subject=f"YouTubeShortsAuto: {notification_title}",
        body=f"<h2>{notification_title}</h2><p>{message}</p>",
        is_html=True
    )


def notify_error(error_msg: str, context: str = ""):
    """Send notification when error occurs."""
    config = _load_notifications()
    if not config.get("notify_on", {}).get("error_occurred", True):
        return
    
    title = "Error en YouTubeShortsAuto"
    message = f"Error: {error_msg}"
    if context:
        message += f"\nContexto: {context}"
    
    send_desktop_notification(title, message, urgency="critical")
    send_email_notification(
        subject=f"YouTubeShortsAuto: {title}",
        body=f"<h2 style='color:red;'>{title}</h2><p>{message}</p>",
        is_html=True
    )


if __name__ == "__main__":
    config = get_notification_config()
    print("Notification config:")
    print(json.dumps(config, indent=2))
