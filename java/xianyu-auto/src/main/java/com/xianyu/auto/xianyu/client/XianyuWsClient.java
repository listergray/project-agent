package com.xianyu.auto.xianyu.client;

import com.xianyu.auto.common.util.JsonUtils;
import com.xianyu.auto.xianyu.constant.XianyuApiConst;
import com.xianyu.auto.xianyu.handler.MessageHandlerRegistry;
import com.xianyu.auto.xianyu.protocol.LwpMessage;
import lombok.extern.slf4j.Slf4j;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;

import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

/**
 * 闲鱼 WebSocket 客户端（对齐真实协议）
 */
@Slf4j
public class XianyuWsClient extends WebSocketClient {

    private final Long accountId;
    private final String deviceId;
    private final String wsToken;
    private final String myUserId;
    private final MessageHandlerRegistry handlerRegistry;
    private final int heartbeatIntervalSec;
    private final int heartbeatTimeoutSec;

    private final ScheduledExecutorService heartbeatScheduler;
    private final AtomicLong lastHeartbeatAt = new AtomicLong(0);
    private final AtomicBoolean registered = new AtomicBoolean(false);
    private final AtomicInteger reconnectAttempts = new AtomicInteger(0);

    private Runnable onCloseCallback;
    private Runnable onOpenCallback;
    /** reg 结果回调：true=成功，false=失败（如 deviceId/token 不匹配） */
    private java.util.function.Consumer<Boolean> onRegResultCallback;
    private volatile String pendingRegMid;

    public XianyuWsClient(Long accountId, String deviceId, String wsToken, String myUserId,
                          String cookie, MessageHandlerRegistry handlerRegistry,
                          int heartbeatIntervalSec, int heartbeatTimeoutSec) throws Exception {
        super(new URI(XianyuApiConst.WS_URL));
        this.accountId = accountId;
        this.deviceId = deviceId;
        this.wsToken = wsToken;
        this.myUserId = myUserId;
        this.handlerRegistry = handlerRegistry;
        this.heartbeatIntervalSec = heartbeatIntervalSec;
        this.heartbeatTimeoutSec = heartbeatTimeoutSec;
        this.heartbeatScheduler = Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "xianyu-ws-heartbeat-" + accountId);
            t.setDaemon(true);
            return t;
        });
        // 握手必须带 Cookie，否则只会心跳、收不到聊天推送
        if (cookie != null && !cookie.isEmpty()) {
            addHeader("Cookie", cookie);
        }
        addHeader("Origin", "https://www.goofish.com");
        addHeader("User-Agent", XianyuApiConst.USER_AGENT);
        addHeader("Pragma", "no-cache");
        addHeader("Cache-Control", "no-cache");
        addHeader("Accept-Language", "zh-CN,zh;q=0.9");
    }

    public void setOnCloseCallback(Runnable callback) {
        this.onCloseCallback = callback;
    }

    public void setOnOpenCallback(Runnable callback) {
        this.onOpenCallback = callback;
    }

    public void setOnRegResultCallback(java.util.function.Consumer<Boolean> callback) {
        this.onRegResultCallback = callback;
    }

    @Override
    public void onOpen(ServerHandshake handshake) {
        log.info("WebSocket 连接已建立: accountId={}, code={}, did={}",
                accountId, handshake.getHttpStatus(), deviceId);
        lastHeartbeatAt.set(System.currentTimeMillis());
        registered.set(false);
        pendingRegMid = null;

        sendRegMessage();
        // sync 等 reg 成功后再发；心跳可先发保活
        heartbeatScheduler.scheduleAtFixedRate(this::sendHeartbeat,
                heartbeatIntervalSec, heartbeatIntervalSec, TimeUnit.SECONDS);
        heartbeatScheduler.scheduleAtFixedRate(this::checkHeartbeatTimeout,
                heartbeatTimeoutSec * 2L, heartbeatTimeoutSec, TimeUnit.SECONDS);

        if (onOpenCallback != null) {
            onOpenCallback.run();
        }
    }

    private void sendRegMessage() {
        if (registered.get()) return;
        try {
            String mid = generateMid();
            Map<String, Object> headers = new LinkedHashMap<>();
            headers.put("cache-header", "app-key token ua wv");
            headers.put("app-key", XianyuApiConst.IM_APP_KEY);
            headers.put("token", wsToken);
            headers.put("ua", XianyuApiConst.IM_UA);
            headers.put("dt", "j");
            headers.put("wv", "im:3,au:3,sy:6");
            headers.put("sync", "0,0;0;0;");
            headers.put("did", deviceId);
            headers.put("mid", mid);

            Map<String, Object> message = new HashMap<>();
            message.put("lwp", XianyuApiConst.LWP_REG);
            message.put("headers", headers);

            pendingRegMid = mid;
            send(JsonUtils.toJson(message));
            log.info("已发送注册包: accountId={}, did={}, mid={}", accountId, deviceId, mid);
        } catch (Exception e) {
            log.error("发送注册包失败: accountId={}, error={}", accountId, e.getMessage(), e);
            notifyRegResult(false);
        }
    }

    private void notifyRegResult(boolean success) {
        if (success) {
            registered.set(true);
            pendingRegMid = null;
            heartbeatScheduler.schedule(this::sendSyncStatus, 200, TimeUnit.MILLISECONDS);
        } else {
            registered.set(false);
            pendingRegMid = null;
        }
        if (onRegResultCallback != null) {
            try {
                onRegResultCallback.accept(success);
            } catch (Exception e) {
                log.warn("reg 结果回调异常: accountId={}, error={}", accountId, e.getMessage());
            }
        }
    }

    /**
     * 判断是否为 /reg 的响应，并更新注册状态。
     * @return true 表示已消费该消息，调用方勿再当业务消息处理
     */
    private boolean handleRegResponse(LwpMessage lwp, String raw) {
        if (registered.get()) return false;

        boolean looksLikeReg = false;
        if (pendingRegMid != null && lwp.getHeaders() != null) {
            Object mid = lwp.getHeaders().get("mid");
            if (mid != null && pendingRegMid.equals(mid.toString())) {
                looksLikeReg = true;
            }
        }
        Map<String, Object> body = lwp.getBodyAsMap();
        if (body != null) {
            Object scope = body.get("scope");
            if ("reg".equals(String.valueOf(scope))) {
                looksLikeReg = true;
            }
            Object reason = body.get("reason");
            if (reason != null && reason.toString().toLowerCase().contains("device id")) {
                looksLikeReg = true;
            }
        }
        if (!looksLikeReg && XianyuApiConst.LWP_REG.equals(lwp.getLwp())) {
            looksLikeReg = true;
        }
        // 尚未注册时，带 code 且无 lwp 的首条响应，优先按 reg 结果处理
        if (!looksLikeReg && pendingRegMid != null && lwp.getCode() != null && lwp.getLwp() == null
                && !lwp.isSyncPushPackage()) {
            looksLikeReg = true;
        }
        if (!looksLikeReg) return false;

        Integer code = lwp.getCode();
        boolean ok = code != null && code == 200;
        if (ok) {
            log.info("IM 注册成功: accountId={}, code={}, did={}", accountId, code, deviceId);
            notifyRegResult(true);
        } else {
            String reason = body != null && body.get("reason") != null
                    ? body.get("reason").toString() : truncate(raw, 200);
            log.error("IM 注册失败: accountId={}, code={}, did={}, reason={}",
                    accountId, code, deviceId, reason);
            notifyRegResult(false);
        }
        return true;
    }

    private void sendSyncStatus() {
        try {
            long now = System.currentTimeMillis();
            Map<String, Object> ackItem = new LinkedHashMap<>();
            ackItem.put("pipeline", "sync");
            ackItem.put("tooLong2Tag", "PNM,1");
            ackItem.put("channel", "sync");
            ackItem.put("topic", "sync");
            ackItem.put("highPts", 0);
            ackItem.put("pts", now * 1000);
            ackItem.put("seq", 0);
            ackItem.put("timestamp", now);

            List<Object> body = new ArrayList<>();
            body.add(ackItem);

            Map<String, Object> message = new HashMap<>();
            message.put("lwp", XianyuApiConst.LWP_SYNC_STATUS);
            Map<String, Object> headers = new HashMap<>();
            headers.put("mid", generateMid());
            message.put("headers", headers);
            message.put("body", body);

            send(JsonUtils.toJson(message));
            log.debug("已发送同步请求: accountId={}", accountId);
        } catch (Exception e) {
            log.warn("发送同步请求失败: accountId={}, error={}", accountId, e.getMessage());
        }
    }

    private void sendHeartbeat() {
        try {
            Map<String, Object> message = new HashMap<>();
            message.put("lwp", XianyuApiConst.LWP_HEARTBEAT);
            Map<String, Object> headers = new HashMap<>();
            headers.put("mid", generateMid());
            message.put("headers", headers);
            send(JsonUtils.toJson(message));
        } catch (Exception e) {
            log.warn("发送心跳失败: accountId={}, error={}", accountId, e.getMessage());
        }
    }

    private void checkHeartbeatTimeout() {
        long now = System.currentTimeMillis();
        long last = lastHeartbeatAt.get();
        long diff = (now - last) / 1000;
        if (diff > heartbeatIntervalSec + heartbeatTimeoutSec) {
            log.warn("心跳超时: accountId={}, 最后心跳={}s 前", accountId, diff);
            try {
                close();
            } catch (Exception e) {
                log.warn("关闭超时连接失败: {}", e.getMessage());
            }
        }
    }

    @Override
    public void onMessage(String message) {
        if (message == null || message.isEmpty()) return;

        if (XianyuApiConst.LWP_HEARTBEAT.equals(message) || message.contains("\"lwp\":\"/!\"")) {
            lastHeartbeatAt.set(System.currentTimeMillis());
            return;
        }
        // 纯心跳 ACK：有 code/server-timestamp，无 body/lwp
        if (message.contains("\"server-timestamp\"") && !message.contains("\"lwp\"")
                && !message.contains("syncPushPackage") && !message.contains("\"body\"")) {
            lastHeartbeatAt.set(System.currentTimeMillis());
            return;
        }

        try {
            LwpMessage lwp = JsonUtils.fromJson(message, LwpMessage.class);
            if (lwp == null) {
                log.warn("无法解析 LWP 消息: {}", truncate(message, 500));
                return;
            }

            // 优先处理 /reg 响应（勿当成心跳 ACK）
            if (handleRegResponse(lwp, message)) {
                return;
            }

            // 心跳响应（code=200 + mid，无业务 body）
            if (lwp.getCode() != null && lwp.getCode() == 200 && lwp.getLwp() == null
                    && lwp.getBodyOrPayload() == null) {
                lastHeartbeatAt.set(System.currentTimeMillis());
                return;
            }

            log.info("收到业务消息: accountId={}, lwp={}, syncPush={}, msg={}",
                    accountId, lwp.getLwp(), lwp.isSyncPushPackage(), truncate(message, 800));

            // 回 ACK
            sendAck(lwp);

            // syncPush 可能无 lwp，仍需分发
            if (lwp.getLwp() == null && !lwp.isSyncPushPackage()) {
                return;
            }

            handlerRegistry.dispatch(accountId, lwp);
        } catch (Exception e) {
            log.error("处理消息失败: accountId={}, msg={}, error={}",
                    accountId, truncate(message, 200), e.getMessage(), e);
        }
    }

    /**
     * 对推送消息回 ACK，否则服务端可能停止推送
     */
    private void sendAck(LwpMessage lwp) {
        try {
            if (lwp.getHeaders() == null) return;
            Object mid = lwp.getHeaders().get("mid");
            if (mid == null) return;

            Map<String, Object> ackHeaders = new HashMap<>();
            ackHeaders.put("mid", mid.toString());
            Object sid = lwp.getHeaders().get("sid");
            ackHeaders.put("sid", sid != null ? sid.toString() : "");
            copyHeaderIfPresent(lwp.getHeaders(), ackHeaders, "app-key");
            copyHeaderIfPresent(lwp.getHeaders(), ackHeaders, "ua");
            copyHeaderIfPresent(lwp.getHeaders(), ackHeaders, "dt");

            Map<String, Object> ack = new HashMap<>();
            ack.put("code", 200);
            ack.put("headers", ackHeaders);
            send(JsonUtils.toJson(ack));
        } catch (Exception e) {
            log.debug("发送 ACK 失败: {}", e.getMessage());
        }
    }

    private void copyHeaderIfPresent(Map<String, Object> src, Map<String, Object> dst, String key) {
        Object v = src.get(key);
        if (v != null) {
            dst.put(key, v);
        }
    }

    @Override
    public void onClose(int code, String reason, boolean remote) {
        long lastHb = lastHeartbeatAt.get();
        long secondsSinceHb = (System.currentTimeMillis() - lastHb) / 1000;
        log.warn("WebSocket 关闭: accountId={}, code={}, reason={}, remote={}, 最后心跳={}s前",
                accountId, code, reason, remote, secondsSinceHb);
        shutdownHeartbeat();
        if (onCloseCallback != null) {
            onCloseCallback.run();
        }
    }

    @Override
    public void onError(Exception e) {
        log.error("WebSocket 异常: accountId={}, error={}", accountId, e.getMessage(), e);
    }

    /**
     * 发送聊天文本消息（真实协议 sendByReceiverScope）
     *
     * @param conversationId 会话 ID（可不带 @goofish）
     * @param buyerId        买家用户 ID
     * @param text           文本内容
     */
    public boolean sendChatMessage(String conversationId, String buyerId, String text) {
        if (myUserId == null || myUserId.isEmpty()) {
            log.error("发送失败：账号 userId(unb) 为空 accountId={}", accountId);
            return false;
        }
        if (buyerId == null || buyerId.isEmpty()) {
            log.error("发送失败：buyerId 为空 accountId={}, conv={}", accountId, conversationId);
            return false;
        }
        try {
            String cid = stripGoofish(conversationId);
            String toId = stripGoofish(buyerId);

            Map<String, Object> textPayload = new LinkedHashMap<>();
            textPayload.put("contentType", 1);
            Map<String, Object> textObj = new HashMap<>();
            textObj.put("text", text);
            textPayload.put("text", textObj);
            String dataBase64 = Base64.getEncoder().encodeToString(
                    JsonUtils.toJson(textPayload).getBytes(StandardCharsets.UTF_8));

            Map<String, Object> custom = new LinkedHashMap<>();
            custom.put("type", 1);
            custom.put("data", dataBase64);

            Map<String, Object> content = new LinkedHashMap<>();
            content.put("contentType", 101);
            content.put("custom", custom);

            Map<String, Object> msgBody = new LinkedHashMap<>();
            msgBody.put("uuid", generateUuid());
            msgBody.put("cid", cid + XianyuApiConst.GOOFISH_SUFFIX);
            msgBody.put("conversationType", 1);
            msgBody.put("content", content);
            msgBody.put("redPointPolicy", 0);
            Map<String, Object> extension = new HashMap<>();
            extension.put("extJson", "{}");
            msgBody.put("extension", extension);
            Map<String, Object> ctx = new HashMap<>();
            ctx.put("appVersion", "1.0");
            ctx.put("platform", "web");
            msgBody.put("ctx", ctx);
            msgBody.put("mtags", new HashMap<>());
            msgBody.put("msgReadStatusSetting", 1);

            Map<String, Object> receivers = new HashMap<>();
            List<String> actualReceivers = new ArrayList<>();
            actualReceivers.add(toId + XianyuApiConst.GOOFISH_SUFFIX);
            actualReceivers.add(myUserId + XianyuApiConst.GOOFISH_SUFFIX);
            receivers.put("actualReceivers", actualReceivers);

            List<Object> body = new ArrayList<>();
            body.add(msgBody);
            body.add(receivers);

            Map<String, Object> message = new HashMap<>();
            message.put("lwp", XianyuApiConst.LWP_MESSAGE_SEND_BY_SCOPE);
            Map<String, Object> headers = new HashMap<>();
            headers.put("mid", generateMid());
            message.put("headers", headers);
            message.put("body", body);

            send(JsonUtils.toJson(message));
            log.info("发送消息: accountId={}, conv={}, buyer={}, content={}",
                    accountId, cid, toId, truncate(text, 50));
            return true;
        } catch (Exception e) {
            log.error("发送消息失败: accountId={}, conv={}, error={}",
                    accountId, conversationId, e.getMessage(), e);
            return false;
        }
    }

    /** 兼容旧签名：buyerId 用 conversationId 顶替（不推荐） */
    public boolean sendChatMessage(String conversationId, String text) {
        return sendChatMessage(conversationId, conversationId, text);
    }

    public void shutdown() {
        shutdownHeartbeat();
        try {
            close();
        } catch (Exception ignored) {
        }
    }

    private void shutdownHeartbeat() {
        try {
            heartbeatScheduler.shutdownNow();
        } catch (Exception ignored) {
        }
    }

    public void resetReconnectAttempts() {
        reconnectAttempts.set(0);
    }

    public int incrementReconnectAttempts() {
        return reconnectAttempts.incrementAndGet();
    }

    public int getReconnectAttempts() {
        return reconnectAttempts.get();
    }

    public long getLastHeartbeatAt() {
        return lastHeartbeatAt.get();
    }

    public boolean isRegistered() {
        return registered.get();
    }

    public String getMyUserId() {
        return myUserId;
    }

    private static String generateMid() {
        long randomPart = (long) (Math.random() * 1000);
        return randomPart + System.currentTimeMillis() + " 0";
    }

    private static String generateUuid() {
        return "-" + System.currentTimeMillis() + "1";
    }

    private static String stripGoofish(String id) {
        if (id == null) return "";
        int idx = id.indexOf('@');
        return idx > 0 ? id.substring(0, idx) : id;
    }

    private String truncate(String s, int maxLen) {
        if (s == null) return null;
        return s.length() > maxLen ? s.substring(0, maxLen) + "..." : s;
    }
}
