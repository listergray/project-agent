package com.xianyu.auto.account.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.xianyu.auto.account.entity.Account;
import com.xianyu.auto.account.mapper.AccountMapper;
import com.xianyu.auto.common.api.PageResult;
import com.xianyu.auto.common.exception.BusinessException;
import com.xianyu.auto.common.security.CookieUtils;
import com.xianyu.auto.common.security.DeviceIdGenerator;
import com.xianyu.auto.common.util.AesUtils;
import com.xianyu.auto.common.util.DateUtils;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.List;

/**
 * 闲鱼账号服务
 * 负责：
 *  - 账号 CRUD（不含 Cookie）
 *  - Cookie AES 加密存储 / 解密读取
 *  - 状态更新
 *  - WS Token 持久化
 */
@Slf4j
@Service
public class AccountService extends ServiceImpl<AccountMapper, Account> {

    private final AesUtils aesUtils;

    public AccountService(AesUtils aesUtils) {
        this.aesUtils = aesUtils;
    }

    /**
     * 分页查询账号列表（不含 Cookie）
     */
    public PageResult<Account> page(Integer pageNo, Integer pageSize, String keyword) {
        Page<Account> page = new Page<>(pageNo, pageSize);
        LambdaQueryWrapper<Account> wrapper = new LambdaQueryWrapper<>();
        if (StringUtils.hasText(keyword)) {
            wrapper.like(Account::getNickname, keyword)
                    .or().like(Account::getUserId, keyword)
                    .or().like(Account::getUserNick, keyword);
        }
        wrapper.orderByDesc(Account::getCreatedAt);
        IPage<Account> result = baseMapper.selectPage(page, wrapper);
        // cookieText 已 @JsonIgnore，返回时不会序列化
        return new PageResult<>(result.getRecords(), result.getTotal());
    }

    /**
     * 创建账号（仅基本字段，Cookie 通过 updateCookie 单独录入）
     */
    public Account create(Account account) {
        if (!StringUtils.hasText(account.getNickname())) {
            throw new BusinessException("账号昵称不能为空");
        }
        account.setId(null);
        account.setStatus(Account.STATUS_OFFLINE);
        account.setDeviceId(DeviceIdGenerator.generate());
        if (account.getAutoStart() == null) {
            account.setAutoStart(0);
        }
        account.setCreatedAt(DateUtils.nowMillis());
        account.setUpdatedAt(DateUtils.nowMillis());
        baseMapper.insert(account);
        log.info("创建闲鱼账号: id={}, nickname={}", account.getId(), account.getNickname());
        return account;
    }

    /**
     * 更新账号基础信息（不含 Cookie）
     */
    public void update(Account account) {
        Account existing = baseMapper.selectById(account.getId());
        if (existing == null) {
            throw new BusinessException("账号不存在");
        }
        existing.setNickname(account.getNickname());
        existing.setAutoStart(account.getAutoStart());
        existing.setUpdatedAt(DateUtils.nowMillis());
        baseMapper.updateById(existing);
    }

    /**
     * 更新 Cookie（AES 加密存储）
     * 校验 Cookie 必要字段
     */
    public void updateCookie(Long accountId, String cookieText) {
        Account existing = baseMapper.selectById(accountId);
        if (existing == null) {
            throw new BusinessException("账号不存在");
        }
        if (!StringUtils.hasText(cookieText)) {
            throw new BusinessException("Cookie 不能为空");
        }
        if (!CookieUtils.isCookieValid(cookieText)) {
            throw new BusinessException("Cookie 缺少必要字段（_m_h5_tk / _m_h5_tk_enc / unb）");
        }
        // 提取用户信息（unb 作为 userId，更新已有用户信息字段）
        String unb = CookieUtils.extractUnb(cookieText);
        existing.setCookieText(aesUtils.encrypt(cookieText));
        if (StringUtils.hasText(unb)) {
            existing.setUserId(unb);
            // 对齐网页端 did：UUID-userId
            existing.setDeviceId(DeviceIdGenerator.ensureWithUserId(existing.getDeviceId(), unb));
        }
        // Cookie 变更后旧 WS Token 失效
        existing.setWsToken(null);
        existing.setStatus(Account.STATUS_OFFLINE);
        existing.setLastLoginAt(DateUtils.nowMillis());
        existing.setUpdatedAt(DateUtils.nowMillis());
        baseMapper.updateById(existing);
        // 单独强制清空 last_error（避免 NOT_NULL 策略吞掉 null）
        clearLastError(accountId);
        log.info("更新 Cookie: accountId={}, userId={}, deviceId={}", accountId, unb, existing.getDeviceId());
    }

    /**
     * 解密读取 Cookie 原文
     */
    public String getDecryptedCookie(Long accountId) {
        Account account = baseMapper.selectById(accountId);
        if (account == null || !StringUtils.hasText(account.getCookieText())) {
            return null;
        }
        return aesUtils.decrypt(account.getCookieText());
    }

    /**
     * 加载账号（含 Cookie 与 WS Token，内部使用）
     * 注意：返回的 Account 含敏感字段，禁止直接序列化返回前端
     */
    public Account loadFullAccount(Long accountId) {
        return baseMapper.selectById(accountId);
    }

    /** 更新或清空 WS Token */
    public void updateWsToken(Long accountId, String wsToken) {
        updateWsToken(accountId, wsToken, null);
    }

    public void updateWsToken(Long accountId, String wsToken, Long expireAtMs) {
        if (wsToken == null) {
            lambdaUpdate()
                    .eq(Account::getId, accountId)
                    .set(Account::getWsToken, null)
                    .set(Account::getWsTokenExpireAt, null)
                    .set(Account::getUpdatedAt, DateUtils.nowMillis())
                    .update();
            return;
        }
        Account existing = baseMapper.selectById(accountId);
        if (existing == null) {
            return;
        }
        existing.setWsToken(wsToken);
        existing.setWsTokenExpireAt(expireAtMs);
        existing.setUpdatedAt(DateUtils.nowMillis());
        baseMapper.updateById(existing);
    }

    /**
     * 仅更新 Cookie 密文，不改状态 / 不清空 WS Token（保活用）
     */
    public void updateCookieQuiet(Long accountId, String cookieText) {
        Account existing = baseMapper.selectById(accountId);
        if (existing == null || !StringUtils.hasText(cookieText)) {
            return;
        }
        if (!CookieUtils.isCookieValid(cookieText)) {
            throw new BusinessException("Cookie 缺少必要字段（_m_h5_tk / _m_h5_tk_enc / unb）");
        }
        String unb = CookieUtils.extractUnb(cookieText);
        existing.setCookieText(aesUtils.encrypt(cookieText));
        if (StringUtils.hasText(unb)) {
            existing.setUserId(unb);
            existing.setDeviceId(DeviceIdGenerator.ensureWithUserId(existing.getDeviceId(), unb));
        }
        existing.setUpdatedAt(DateUtils.nowMillis());
        baseMapper.updateById(existing);
        log.debug("静默更新 Cookie: accountId={}, userId={}", accountId, unb);
    }

    /**
     * 更新状态
     */
    public void updateStatus(Long accountId, String status, String errorMsg) {
        var chain = lambdaUpdate()
                .eq(Account::getId, accountId)
                .set(Account::getStatus, status)
                .set(Account::getLastError, errorMsg)
                .set(Account::getUpdatedAt, DateUtils.nowMillis());
        if (Account.STATUS_ONLINE.equals(status)) {
            chain.set(Account::getLastKeepaliveAt, DateUtils.nowMillis());
        }
        chain.update();
    }

    /**
     * 更新保活时间，并强制清除 lastError（MyBatis-Plus 默认忽略 null，需用 setSql/ALWAYS）
     */
    public void touchKeepalive(Long accountId) {
        lambdaUpdate()
                .eq(Account::getId, accountId)
                .set(Account::getLastKeepaliveAt, DateUtils.nowMillis())
                .set(Account::getLastError, null)
                .set(Account::getUpdatedAt, DateUtils.nowMillis())
                .setSql("status = CASE WHEN status = 'EXPIRED' THEN 'OFFLINE' ELSE status END")
                .update();
    }

    /** 仅清除错误信息 */
    public void clearLastError(Long accountId) {
        lambdaUpdate()
                .eq(Account::getId, accountId)
                .set(Account::getLastError, null)
                .set(Account::getUpdatedAt, DateUtils.nowMillis())
                .update();
    }

    /**
     * 标记 Cookie 失效
     */
    public void markExpired(Long accountId, String reason) {
        updateStatus(accountId, Account.STATUS_EXPIRED, reason);
        log.warn("Cookie 失效: accountId={}, reason={}", accountId, reason);
    }

    /**
     * 查询所有 auto_start=1 且 Cookie 已录入 的账号（启动时自动连接）
     */
    public List<Account> listAutoStartAccounts() {
        return baseMapper.selectList(new LambdaQueryWrapper<Account>()
                .eq(Account::getAutoStart, 1)
                .isNotNull(Account::getCookieText));
    }

    /**
     * 查询所有 Cookie 已录入 的账号（用于 Token 刷新调度）
     */
    public List<Account> listAccountsHasCookie() {
        return baseMapper.selectList(new LambdaQueryWrapper<Account>()
                .isNotNull(Account::getCookieText));
    }

    /**
     * 删除账号（逻辑删除）
     */
    public void delete(Long accountId) {
        Account existing = baseMapper.selectById(accountId);
        if (existing == null) {
            throw new BusinessException("账号不存在");
        }
        baseMapper.deleteById(accountId);
        log.info("删除闲鱼账号: id={}", accountId);
    }

    /**
     * 更新 OAuth2.0 Token 信息
     */
    public void updateOAuth2Token(Long accountId, String accessToken, String refreshToken,
                                  Long accessTokenExpireAt, Long refreshTokenExpireAt) {
        Account existing = baseMapper.selectById(accountId);
        if (existing == null) {
            throw new BusinessException("账号不存在");
        }
        existing.setAccessToken(accessToken);
        existing.setRefreshToken(refreshToken);
        existing.setAccessTokenExpireAt(accessTokenExpireAt);
        existing.setRefreshTokenExpireAt(refreshTokenExpireAt);
        existing.setUpdatedAt(DateUtils.nowMillis());
        baseMapper.updateById(existing);
        log.info("更新 OAuth2 Token: accountId={}", accountId);
    }

    /**
     * 查询所有已授权的账号（Cookie 或 OAuth2）
     */
    public List<Account> listAuthorizedAccounts() {
        return baseMapper.selectList(new LambdaQueryWrapper<Account>()
                .and(w -> w.isNotNull(Account::getCookieText).or().isNotNull(Account::getAccessToken)));
    }
}
