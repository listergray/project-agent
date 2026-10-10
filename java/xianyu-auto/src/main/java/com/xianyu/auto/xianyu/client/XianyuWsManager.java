package com.xianyu.auto.xianyu.client;

import com.xianyu.auto.account.entity.Account;
import com.xianyu.auto.account.service.AccountService;
import com.xianyu.auto.common.exception.BusinessException;
import com.xianyu.auto.common.security.DeviceIdGenerator;
import com.xianyu.auto.xianyu.auth.CookieManager;
import com.xianyu.auto.xianyu.auth.TokenRefresher;
import com.xianyu.auto.xianyu.config.XianyuProperties;
import com.xianyu.auto.xianyu.handler.MessageHandlerRegistry;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

/**
 * 闲鱼 WebSocket 多账号连接管理器
 * 职责：
 *  - 每账号独立 XianyuWsClient 实例（线程隔离、故障隔离）
 *  - connect(accountId): 加载账号 → ensureWsToken → 创建 client → 启动
 *  - reconnect(accountId): 指数退避调度（1s→2s→4s→8s→16s→30s，0-1s 抖动）
 *  - disconnect(accountId): 优雅关闭
 *  - sendChatMessage(accountId, conv, text): 转发到对应账号的 client
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class XianyuWsManager {

    private final AccountService accountService;
    private final TokenRefresher tokenRefresher;
    private final CookieManager cookieManager;
    private final MessageHandlerRegistry handlerRegistry;
    private final XianyuProperties properties;

    /** 账号 → WS 客户端映射 */
    private final ConcurrentMap<Long, XianyuWsClient> clients = new ConcurrentHashMap<>();

    /** 重连调度器 */
    private final ScheduledExecutorService reconnectScheduler =
            new ScheduledThreadPoolExecutor(2, r -> {
                Thread t = new Thread(r, "xianyu-ws-reconnect");
                t.setDaemon(true);
                return t;
            });

    /**
     * 启动连接
     */
    public synchronized void connect(Long accountId) {
        Account account = accountService.loadFullAccount(accountId);
        if (account == null) {
            throw new BusinessException("账号不存在");
        }
        if (!account.canConnect()) {
            throw new BusinessException("账号不可连接（已禁用或 Cookie 未录入）");
        }
        if (clients.containsKey(accountId)) {
            log.info("账号已存在连接，先断开旧连接: accountId={}", accountId);
            disconnect(accountId);
        }

        try {
            accountService.updateStatus(accountId, Account.STATUS_CONNECTING, null);

            String cookie = cookieManager.getCookie(accountId);
            if (cookie == null || cookie.isEmpty()) {
                throw new BusinessException("Cookie 为空，请重新录入");
            }

            String myUserId = account.getUserId();
            if (myUserId == null || myUserId.isEmpty()) {
                myUserId = cookieManager.getUnb(accountId);
            }
            if (myUserId == null || myUserId.isEmpty()) {
                throw new BusinessException("账号缺少用户 ID(unb)，请重新录入 Cookie");
            }

            // 对齐网页端 did（UUID-userId），并落库
            String deviceId = DeviceIdGenerator.ensureWithUserId(account.getDeviceId(), myUserId);
            if (!deviceId.equals(account.getDeviceId())) {
                account.setDeviceId(deviceId);
                accountService.updateById(account);
                // did 变更后旧 token 不可用
                accountService.updateWsToken(accountId, null);
            }
            // 未过期则复用；过期或缺失才 loginToken
            String wsToken = tokenRefresher.ensureWsToken(accountId);
            account = accountService.loadFullAccount(accountId);
            final String finalDeviceId = account.getDeviceId();
            cookie = cookieManager.getCookie(accountId);

            // 创建客户端实例（握手带 Cookie）
            XianyuWsClient client = new XianyuWsClient(
                    accountId, finalDeviceId, wsToken, myUserId, cookie, handlerRegistry,
                    properties.getHeartbeatIntervalSec(),
                    properties.getHeartbeatTimeoutSec());

            // 设置连接关闭回调（触发重连）
            client.setOnCloseCallback(() -> handleDisconnect(accountId));

            // 仅 TCP 连上；真正可用要等 reg 成功
            client.setOnOpenCallback(() ->
                    log.info("WebSocket TCP 已连接，等待注册: accountId={}, did={}", accountId, finalDeviceId));

            client.setOnRegResultCallback(success -> {
                try {
                    if (success) {
                        accountService.updateStatus(accountId, Account.STATUS_ONLINE, null);
                        accountService.touchKeepalive(accountId);
                        client.resetReconnectAttempts();
                        log.info("账号 IM 注册成功: accountId={}", accountId);
                    } else {
                        // 清掉失效 token，关闭连接触发重连（会重新 loginToken）
                        accountService.updateWsToken(accountId, null);
                        accountService.updateStatus(accountId, Account.STATUS_ERROR,
                                "IM注册失败: deviceId与token不匹配，将自动重试");
                        log.error("账号 IM 注册失败: accountId={}, did={}，关闭连接以重试",
                                accountId, finalDeviceId);
                        try {
                            client.close();
                        } catch (Exception ignored) {
                        }
                    }
                } catch (Exception e) {
                    log.warn("更新注册状态失败: accountId={}, error={}", accountId, e.getMessage());
                }
            });

            // 异步连接（避免阻塞）
            client.connect();
            clients.put(accountId, client);

            log.info("启动 WebSocket 连接: accountId={}, deviceId={}", accountId, finalDeviceId);
        } catch (Exception e) {
            log.error("启动连接失败: accountId={}, error={}", accountId, e.getMessage(), e);
            accountService.updateStatus(accountId, Account.STATUS_ERROR, "启动连接失败: " + e.getMessage());
            throw new BusinessException("启动连接失败: " + e.getMessage(), e);
        }
    }

    /**
     * 断开连接
     */
    public synchronized void disconnect(Long accountId) {
        XianyuWsClient client = clients.remove(accountId);
        if (client != null) {
            client.setOnCloseCallback(null);  // 防止 close 回调触发重连
            client.shutdown();
            accountService.updateStatus(accountId, Account.STATUS_OFFLINE, null);
            log.info("已断开连接: accountId={}", accountId);
        }
    }

    /**
     * 处理连接断开事件（由 XianyuWsClient.onClose 回调触发）
     */
    private void handleDisconnect(Long accountId) {
        XianyuWsClient client = clients.remove(accountId);
        if (client != null) {
            int attempts = client.incrementReconnectAttempts();
            long delay = computeReconnectDelay(attempts);
            log.info("计划重连: accountId={}, attempts={}, delayMs={}", accountId, attempts, delay);

            reconnectScheduler.schedule(() -> {
                try {
                    if (!clients.containsKey(accountId)) {
                        connect(accountId);
                    }
                } catch (Exception e) {
                    log.warn("重连失败: accountId={}, error={}", accountId, e.getMessage());
                }
            }, delay, TimeUnit.MILLISECONDS);
        }
    }

    /**
     * 计算重连延迟（指数退避 1s→2s→4s→8s→16s→30s，0-1s 抖动）
     */
    private long computeReconnectDelay(int attempt) {
        long base;
        if (attempt <= 1) base = 1_000L;
        else if (attempt == 2) base = 2_000L;
        else if (attempt == 3) base = 4_000L;
        else if (attempt == 4) base = 8_000L;
        else if (attempt == 5) base = 16_000L;
        else base = 30_000L;
        // 0-1s 抖动
        long jitter = (long) (Math.random() * 1000);
        return base + jitter;
    }

    /**
     * 判断账号是否在线
     */
    public boolean isAccountOnline(Long accountId) {
        XianyuWsClient client = clients.get(accountId);
        return client != null && client.isOpen();
    }

    /**
     * 发送聊天消息
     *
     * @param buyerId 买家用户 ID（必填，用于 actualReceivers）
     */
    public boolean sendChatMessage(Long accountId, String conversationId, String buyerId, String text) {
        XianyuWsClient client = clients.get(accountId);
        if (client == null || !client.isOpen()) {
            log.warn("发送消息失败：账号未连接 accountId={}", accountId);
            return false;
        }
        return client.sendChatMessage(conversationId, buyerId, text);
    }

    /**
     * 兼容旧调用：无 buyerId 时用 conversationId 顶替
     */
    public boolean sendChatMessage(Long accountId, String conversationId, String text) {
        return sendChatMessage(accountId, conversationId, conversationId, text);
    }

    /**
     * 查询账号连接状态
     */
    public Map<String, Object> getStatus(Long accountId) {
        Map<String, Object> status = new HashMap<>();
        XianyuWsClient client = clients.get(accountId);
        if (client == null) {
            status.put("connected", false);
            status.put("registered", false);
            status.put("reconnectAttempts", 0);
        } else {
            status.put("connected", client.isOpen());
            status.put("registered", client.isRegistered());
            status.put("lastHeartbeatAt", client.getLastHeartbeatAt());
            status.put("reconnectAttempts", client.getReconnectAttempts());
        }
        return status;
    }

    /**
     * 获取所有账号连接状态
     */
    public Map<Long, Map<String, Object>> getAllStatus() {
        Map<Long, Map<String, Object>> result = new HashMap<>();
        for (Long accountId : clients.keySet()) {
            result.put(accountId, getStatus(accountId));
        }
        return result;
    }

    /**
     * 启动时自动连接 auto_start=1 的账号
     */
    @PostConstruct
    public void autoStartConnect() {
        reconnectScheduler.schedule(() -> {
            try {
                List<Account> accounts = accountService.listAutoStartAccounts();
                log.info("启动自动连接: {} 个账号", accounts.size());
                for (Account account : accounts) {
                    try {
                        connect(account.getId());
                    } catch (Exception e) {
                        log.warn("自动连接失败: accountId={}, error={}", account.getId(), e.getMessage());
                    }
                }
            } catch (Exception e) {
                log.error("自动启动连接任务异常", e);
            }
        }, 10_000L, TimeUnit.MILLISECONDS);  // 等 TokenRefresher 初始化完成后启动
    }

    @PreDestroy
    public void destroy() {
        log.info("关闭所有 WebSocket 连接...");
        for (Long accountId : clients.keySet()) {
            try {
                disconnect(accountId);
            } catch (Exception ignored) {
            }
        }
        reconnectScheduler.shutdownNow();
        log.info("WebSocket 管理器关闭完成");
    }
}
