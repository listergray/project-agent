package com.xianyu.auto.xianyu.auth;

import com.xianyu.auto.account.entity.Account;
import com.xianyu.auto.account.service.AccountService;
import com.xianyu.auto.common.exception.BusinessException;
import com.xianyu.auto.common.security.DeviceIdGenerator;
import com.xianyu.auto.xianyu.client.XianyuApiClient;
import com.xianyu.auto.xianyu.config.XianyuProperties;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

/**
 * Token / Cookie 轻量维护：
 * - ONLINE：依赖 WS 心跳，不做 HTTP 保活
 * - 离线：低频访问首页刷 _m_h5_tk（带抖动、错峰）
 * - WS Token：未过期则复用；定时在过期前刷新
 */
@Slf4j
@Component
public class TokenRefresher {

    /** 过期前多少毫秒内仍视为可用（留缓冲给 reg） */
    private static final long WS_TOKEN_SAFE_MARGIN_MS = 30 * 60_000L;

    private final AccountService accountService;
    private final CookieManager cookieManager;
    private final XianyuApiClient apiClient;
    private final XianyuProperties properties;

    private final ScheduledExecutorService scheduler =
            new ScheduledThreadPoolExecutor(4, r -> {
                Thread t = new Thread(r, "xianyu-token-refresh");
                t.setDaemon(true);
                return t;
            });

    private final ConcurrentMap<Long, Long> wsTokenNextRefresh = new ConcurrentHashMap<>();
    private final ConcurrentMap<Long, Boolean> keepaliveScheduled = new ConcurrentHashMap<>();

    public TokenRefresher(AccountService accountService,
                          CookieManager cookieManager,
                          XianyuApiClient apiClient,
                          XianyuProperties properties) {
        this.accountService = accountService;
        this.cookieManager = cookieManager;
        this.apiClient = apiClient;
        this.properties = properties;
    }

    @PostConstruct
    public void init() {
        scheduler.schedule(this::initRefreshSchedules, 5_000L, TimeUnit.MILLISECONDS);
        log.info("Token 刷新调度器启动: 离线保活约 {}~{}min, mh5/ws 由过期策略驱动",
                Math.round(properties.getCookieKeepaliveMin() * 0.8),
                Math.round(properties.getCookieKeepaliveMin() * 1.2));
    }

    @PreDestroy
    public void destroy() {
        scheduler.shutdownNow();
        log.info("Token 刷新调度器关闭");
    }

    /**
     * 确保有可用 WS Token：未过期则复用，否则刷新
     */
    public String ensureWsToken(Long accountId) {
        Account account = accountService.loadFullAccount(accountId);
        if (account == null) {
            throw new BusinessException("账号不存在: " + accountId);
        }
        String wsToken = account.getWsToken();
        Long expireAt = account.getWsTokenExpireAt();
        long now = System.currentTimeMillis();
        if (wsToken != null && !wsToken.isEmpty()
                && expireAt != null && expireAt - WS_TOKEN_SAFE_MARGIN_MS > now) {
            if (!wsTokenNextRefresh.containsKey(accountId)) {
                scheduleNextWsTokenRefresh(accountId, expireAt);
            }
            ensureKeepaliveScheduled(accountId);
            log.debug("复用未过期 WS Token: accountId={}, remainMin={}",
                    accountId, (expireAt - now) / 60_000);
            return wsToken;
        }
        return refreshWsToken(accountId);
    }

    /**
     * 强制刷新 WS Token（reg 失败或手动刷新时用）
     */
    public String refreshWsToken(Long accountId) {
        try {
            Account account = accountService.loadFullAccount(accountId);
            if (account == null) {
                throw new BusinessException("账号不存在");
            }
            String cookie = accountService.getDecryptedCookie(accountId);
            if (cookie == null) {
                throw new BusinessException("Cookie 未录入");
            }

            // 签 MTOP 前轻量刷一次 mh5（首页），不做 hasLogin
            String refreshedCookie = apiClient.refreshMh5Tk(cookie);
            if (!refreshedCookie.equals(cookie)) {
                accountService.updateCookieQuiet(accountId, refreshedCookie);
                cookie = refreshedCookie;
                account = accountService.loadFullAccount(accountId);
            }

            String userId = account.getUserId();
            if (userId == null || userId.isEmpty()) {
                userId = cookieManager.getUnb(accountId);
            }
            String deviceId = DeviceIdGenerator.ensureWithUserId(account.getDeviceId(), userId);
            if (!deviceId.equals(account.getDeviceId())) {
                account.setDeviceId(deviceId);
                accountService.updateById(account);
            }

            XianyuApiClient.WsLoginToken result = apiClient.loginToken(cookie, deviceId);
            accountService.updateWsToken(accountId, result.accessToken(), result.expireAtMs());
            scheduleNextWsTokenRefresh(accountId, result.expireAtMs());
            ensureKeepaliveScheduled(accountId);
            log.info("WS Token 刷新成功: accountId={}, deviceId={}, expireAt={}",
                    accountId, deviceId, result.expireAtMs());
            return result.accessToken();
        } catch (Exception e) {
            log.error("WS Token 刷新失败: accountId={}, error={}", accountId, e.getMessage());
            accountService.updateStatus(accountId, Account.STATUS_ERROR, "WS Token 刷新失败: " + e.getMessage());
            throw new BusinessException("WS Token 刷新失败: " + e.getMessage(), e);
        }
    }

    private void scheduleNextWsTokenRefresh(Long accountId, Long expireAtMs) {
        long now = System.currentTimeMillis();
        long delayMs;
        if (expireAtMs != null && expireAtMs > now + WS_TOKEN_SAFE_MARGIN_MS) {
            // 过期前 1～2 小时随机刷新
            long windowStart = expireAtMs - 2 * 3600_000L;
            long windowEnd = expireAtMs - WS_TOKEN_SAFE_MARGIN_MS;
            long target = Math.max(now + 60_000L,
                    windowStart + (long) (Math.random() * Math.max(1, windowEnd - windowStart)));
            delayMs = target - now;
        } else {
            delayMs = properties.nextWsTokenRefreshDelayMs();
        }
        long nextAt = now + delayMs;
        wsTokenNextRefresh.put(accountId, nextAt);
        scheduler.schedule(() -> {
            try {
                Account acc = accountService.getById(accountId);
                if (acc == null || Account.STATUS_DISABLED.equals(acc.getStatus())) {
                    return;
                }
                // 仍在线且 token 未近过期则再顺延
                if (acc.getWsTokenExpireAt() != null
                        && acc.getWsTokenExpireAt() - WS_TOKEN_SAFE_MARGIN_MS > System.currentTimeMillis()) {
                    scheduleNextWsTokenRefresh(accountId, acc.getWsTokenExpireAt());
                    return;
                }
                refreshWsToken(accountId);
            } catch (Exception e) {
                log.warn("调度刷新 WS Token 失败: accountId={}, error={}", accountId, e.getMessage());
                scheduleNextWsTokenRefresh(accountId, null);
            }
        }, delayMs, TimeUnit.MILLISECONDS);
        log.debug("调度下次 WS Token 刷新: accountId={}, delayMs={}", accountId, delayMs);
    }

    private void ensureKeepaliveScheduled(Long accountId) {
        if (keepaliveScheduled.putIfAbsent(accountId, Boolean.TRUE) == null) {
            scheduleNextKeepalive(accountId, true);
        }
    }

    /**
     * 每账号独立保活调度（带抖动）；首轮可加错峰
     */
    private void scheduleNextKeepalive(Long accountId, boolean first) {
        long base = properties.cookieKeepaliveMs();
        // ±20% 抖动
        long delay = (long) (base * (0.8 + Math.random() * 0.4));
        if (first) {
            // 账号错峰 0～3 分钟，避免启动瞬间齐射
            delay = (accountId % 7) * 25_000L + (long) (Math.random() * 180_000L);
        }
        scheduler.schedule(() -> {
            try {
                doLightKeepalive(accountId);
            } catch (Exception e) {
                log.warn("轻量保活失败: accountId={}, error={}", accountId, e.getMessage());
            } finally {
                Account acc = accountService.getById(accountId);
                if (acc != null && !Account.STATUS_DISABLED.equals(acc.getStatus())
                        && acc.getCookieText() != null) {
                    scheduleNextKeepalive(accountId, false);
                } else {
                    keepaliveScheduled.remove(accountId);
                }
            }
        }, delay, TimeUnit.MILLISECONDS);
    }

    /**
     * ONLINE/CONNECTING：不打 HTTP；离线：仅访问首页刷 Cookie
     */
    private void doLightKeepalive(Long accountId) {
        Account account = accountService.loadFullAccount(accountId);
        if (account == null || Account.STATUS_DISABLED.equals(account.getStatus())) {
            return;
        }
        if (Account.STATUS_ONLINE.equals(account.getStatus())
                || Account.STATUS_CONNECTING.equals(account.getStatus())) {
            log.debug("账号在线，跳过 HTTP 保活: accountId={}", accountId);
            return;
        }
        String cookie = accountService.getDecryptedCookie(accountId);
        if (cookie == null) {
            return;
        }
        try {
            String refreshed = apiClient.refreshMh5Tk(cookie);
            if (!refreshed.equals(cookie)) {
                accountService.updateCookieQuiet(accountId, refreshed);
                log.info("离线轻量保活：已刷新 _m_h5_tk accountId={}", accountId);
            } else {
                log.debug("离线轻量保活完成（Cookie 未变）: accountId={}", accountId);
            }
            cookieManager.touchKeepalive(accountId);
        } catch (Exception e) {
            log.warn("离线轻量保活异常: accountId={}, error={}", accountId, e.getMessage());
        }
    }

    private void initRefreshSchedules() {
        try {
            List<Account> accounts = accountService.listAccountsHasCookie();
            int ws = 0;
            for (Account account : accounts) {
                if (Account.STATUS_DISABLED.equals(account.getStatus())) {
                    continue;
                }
                ensureKeepaliveScheduled(account.getId());
                if (account.getWsToken() != null && !account.getWsToken().isEmpty()) {
                    scheduleNextWsTokenRefresh(account.getId(), account.getWsTokenExpireAt());
                    ws++;
                }
            }
            log.info("Token/保活调度初始化完成: accounts={}, withWsToken={}", accounts.size(), ws);
        } catch (Exception e) {
            log.error("Token 刷新调度初始化失败", e);
        }
    }
}
