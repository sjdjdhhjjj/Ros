import socket
import ssl
import threading

def secure_server():
    # 生成自签名证书指令 (在控制台运行一次):
    # openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
    
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

    bind_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bind_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    bind_socket.bind(('0.0.0.0', 4444))
    bind_socket.listen(5)
    
    print("[*] SSL 加密服务端已启动，等待安全连接...")
    while True:
        client_sock, addr = bind_socket.accept()
        secure_sock = context.wrap_socket(client_sock, server_side=True)
        threading.Thread(target=handle_client, args=(secure_sock, addr), daemon=True).start()

def handle_client(sock, addr):
    print(f"[+] 收到加密会话来自: {addr}")
    # 后续收发逻辑与之前相同...