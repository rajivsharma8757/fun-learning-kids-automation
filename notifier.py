import os
import sys
import subprocess

def send_notification(title, message, error=False):
    """
    Sends a native Windows desktop notification.
    Uses Windows Action Center Toast Notification with NotifyIcon balloon fallback.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    ps_script = os.path.join(base_dir, "notifier.ps1")
    
    # Also log to console
    prefix = "❌" if error else "🔔"
    try:
        print(f"{prefix} [{title}]: {message}")
    except Exception:
        pass

    if os.path.exists(ps_script):
        try:
            subprocess.run([
                "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                "-File", ps_script,
                "-Title", str(title),
                "-Message", str(message),
                "-Type", "Error" if error else "Info"
            ], capture_output=True, timeout=12)
            return True
        except Exception as e:
            try:
                print(f"⚠️ Notification error: {e}")
            except Exception:
                pass
            return False
    return False

if __name__ == "__main__":
    send_notification("Fun Learning Kids", "Desktop Notifications Active!")
