package com.xianyu.auto.xianyu.auth;

import com.xianyu.auto.account.entity.Account;
import com.xianyu.auto.account.service.AccountService;
import com.xianyu.auto.common.security.CookieUtils;
import com.xianyu.auto.common.util.DateUtils;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

/**
 * Cookie 管理器
 * 职责：
 *  - 解密读取 Cookie 原文（供 XianyuApiClient / XianyuWsClient 使用）
 *  - 标记 Cookie 失效并触发通知事件（Phase 5 接入）
 *  - 基础校验
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class CookieManager {

    private final AccountService accountService;

    /**
     * 解密读取账号 Cookie 原文
     */
    public String getCookie(Long accountId) {
        return accountService.getDecryptedCookie(accountId);
    }

    /**
     * 从 Cookie 提取 _m_h5_tk
     */
    public String getMh5Tk(Long accountId) {
        String cookie = getCookie(accountId);
        return cookie == null ? null : CookieUtils.extractMh5Tk(cookie);
    }

    /**
     * 从 Cookie 提取 sign token（_m_h5_tk 第一段）
     */
    public String getSignToken(Long accountId) {
        String cookie = getCookie(accountId);
        return cookie == null ? null : CookieUtils.extractSignToken(cookie);
    }

    /**
     * 提取 unb（用户 ID）
     */
    public String getUnb(Long accountId) {
        String cookie = getCookie(accountId);
        return cookie == null ? null : CookieUtils.extractUnb(cookie);
    }

    /**
     * 判断 Cookie 是否有效
     */
    public boolean isCookieValid(Long accountId) {
        String cookie = getCookie(accountId);
        return CookieUtils.isCookieValid(cookie);
    }

    /**
     * 标记 Cookie 已失效
     * 触发后续通知（Phase 5 接入 NotificationService）
     */
    public void markExpired(Long accountId, String reason) {
        accountService.markExpired(accountId, reason);
        log.warn("Cookie 失效标记: accountId={}, reason={}", accountId, reason);
        // TODO Phase 5: 发布 CookieExpiredEvent 触发邮件/企业微信通知
    }

    /**
     * 更新保活时间（hasLogin 成功后调用）
     */
    public void touchKeepalive(Long accountId) {
        accountService.touchKeepalive(accountId);
    }

    /**
     * 判断 Cookie 是否到期需刷新 _m_h5_tk
     * 简化策略：始终由 TokenRefresher 调度，此处保留扩展点
     */
    public boolean needsRefresh(Account account) {
        if (account.getLastKeepaliveAt() == null) {
            return true;
        }
        return DateUtils.nowMillis() - account.getLastKeepaliveAt() > 2 * 3600_000L;
    }
}
