package com.mycompany.myapp3;

import java.io.BufferedReader;
import java.io.InputStreamReader;

public class CommandExecutor {
    public static String execute(String jsonCmd) {
        try {
            // 简化处理，实际可解析 JSON
            // 这里执行 "id" 命令作为示例[span_2](start_span)[span_2](end_span)
            Process process = Runtime.getRuntime().exec("id");
            BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
            String line;
            StringBuilder result = new StringBuilder();
            while ((line = reader.readLine()) != null) {
                result.append(line).append("\n");
            }
            return result.toString();
        } catch (Exception e) {
            return "执行错误: " + e.getMessage();
        }
    }
}