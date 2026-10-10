package com.xianyu.auto.xianyu.oauth2;

import com.fasterxml.jackson.databind.JsonNode;
import com.xianyu.auto.account.entity.Account;
import com.xianyu.auto.account.service.AccountService;
import com.xianyu.auto.common.util.JsonUtils;
import com.xianyu.auto.xianyu.config.XianyuProperties;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

/**
 * 闲鱼开放平台 OAuth2.0 服务
 * 
 * 授权流程：
 * 1. 生成授权 URL → 用户访问 → 授权后回调
 * 2. 用 code 换取 access_token 和 refresh_token
 * 3. 定时自动刷新 access_token（过期前 5 分钟）
 * 4. refresh_token 过期后重新授权
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class XianyuOAuth2Service {

    private final AccountService accountService;
    private final XianyuProperties properties;

    private final OkHttpClient httpClient = new OkHttpClient.Builder()
            .connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .build();

    /** 存储授权请求的 state → accountId 映射（用于回调验证） */
    private final ConcurrentHashMap<String, Long> stateMap = new ConcurrentHashMap<>();

    /** 定时刷新调度器 */
    private final ScheduledExecutorService scheduler = new ScheduledThreadPoolExecutor(2, r -> {
        Thread t = new Thread(r, "xianyu-oauth2-refresh");
        t.setDaemon(true);
        return t;
    });

    /**
     * 获取开放平台 AppKey（从配置或系统配置）
     */
    public String getAppKey() {
        return StringUtils.hasText(properties.getOpenAppKey()) ? properties.getOpenAppKey() : properties.getAppKey();
    }

    /**
     * 获取开放平台 AppSecret（从配置或系统配置）
     */
    public String getAppSecret() {
        return properties.getOpenAppSecret();
    }

    /**
     * 获取授权回调地址
     */
    public String getCallbackUrl() {
        return properties.getOauthCallbackUrl();
    }

    /**
     * 生成授权 URL
     * 
     * @param accountId 账号 ID
     * @return 授权 URL
     */
    public String generateAuthUrl(Long accountId) {
        String state = UUID.randomUUID().toString().replace("-", "");
        stateMap.put(state, accountId);
        
        // 设置过期时间（10分钟后自动清理）
        scheduler.schedule(() -> stateMap.remove(state), 10, TimeUnit.MINUTES);

        // 闲鱼开放平台授权地址
        return String.format(
                "https://openauth.alibaba.com/oauth2/auth.htm?appkey=%s&response_type=code&redirect_uri=%s&scope=all&state=%s",
                getAppKey(),
                getCallbackUrl(),
                state
        );
    }

    /**
     * 处理授权回调，用 code 换取 token
     * 
     * @param code 授权码
     * @param state 随机字符串
     * @return 账号 ID
     */
    public Long handleCallback(String code, String state) {
        // 验证 state
        Long accountId = stateMap.remove(state);
        if (accountId == null) {
            throw new RuntimeException("无效的授权请求或已过期");
        }

        // 用 code 换取 token
        OAuth2Token token = exchangeCodeForToken(code);
        
        // 更新账号信息
        Account account = accountService.getById(accountId);
        if (account != null) {
            accountService.updateOAuth2Token(accountId, token.getAccessToken(), 
                    token.getRefreshToken(), token.getAccessTokenExpireAt(), 
                    token.getRefreshTokenExpireAt());
            account.setAuthType("OAUTH2");
            accountService.updateById(account);
            log.info("OAuth2 授权成功: accountId={}", accountId);
        }

        // 调度下次刷新
        scheduleTokenRefresh(accountId, token.getAccessTokenExpireAt());

        return accountId;
    }

    /**
     * 用授权码换取 Access Token 和 Refresh Token
     */
    private OAuth2Token exchangeCodeForToken(String code) {
        try {
            String url = "https://openauth.alibaba.com/oauth2/token.htm";
            
            Map<String, String> params = new HashMap<>();
            params.put("appkey", getAppKey());
            params.put("appsecret", getAppSecret());
            params.put("code", code);
            params.put("grant_type", "authorization_code");
            params.put("redirect_uri", getCallbackUrl());

            StringBuilder formBody = new StringBuilder();
            for (Map.Entry<String, String> entry : params.entrySet()) {
                if (formBody.length() > 0) {
                    formBody.append("&");
                }
                formBody.append(entry.getKey()).append("=").append(java.net.URLEncoder.encode(entry.getValue(), "UTF-8"));
            }

            Request request = new Request.Builder()
                    .url(url)
                    .header("Content-Type", "application/x-www-form-urlencoded")
                    .post(okhttp3.RequestBody.create(formBody.toString(), 
                            okhttp3.MediaType.parse("application/x-www-form-urlencoded")))
                    .build();

            try (Response response = httpClient.newCall(request).execute()) {
                if (!response.isSuccessful()) {
                    throw new RuntimeException("获取 token 失败: HTTP " + response.code());
                }
                String body = response.body() != null ? response.body().string() : "{}";
                JsonNode result = JsonUtils.fromJson(body, JsonNode.class);
                
                // 解析响应
                String accessToken = result.path("access_token").asText(null);
                String refreshToken = result.path("refresh_token").asText(null);
                long expiresIn = result.path("expires_in").asLong(7200); // 默认 2 小时
                long refreshExpiresIn = result.path("refresh_token_expires_in").asLong(2592000); // 默认 30 天

                if (accessToken == null || refreshToken == null) {
                    throw new RuntimeException("获取 token 失败: " + body);
                }

                long now = System.currentTimeMillis();
                return OAuth2Token.builder()
                        .accessToken(accessToken)
                        .refreshToken(refreshToken)
                        .accessTokenExpireAt(now + expiresIn * 1000)
                        .refreshTokenExpireAt(now + refreshExpiresIn * 1000)
                        .build();
            }
        } catch (Exception e) {
            log.error("换取 token 失败: {}", e.getMessage(), e);
            throw new RuntimeException("换取 token 失败: " + e.getMessage());
        }
    }

    /**
     * 刷新 Access Token
     */
    public OAuth2Token refreshAccessToken(Long accountId, String refreshToken) {
        try {
            String url = "https://openauth.alibaba.com/oauth2/token.htm";
            
            Map<String, String> params = new HashMap<>();
            params.put("appkey", getAppKey());
            params.put("appsecret", getAppSecret());
            params.put("refresh_token", refreshToken);
            params.put("grant_type", "refresh_token");

            StringBuilder formBody = new StringBuilder();
            for (Map.Entry<String, String> entry : params.entrySet()) {
                if (formBody.length() > 0) {
                    formBody.append("&");
                }
                formBody.append(entry.getKey()).append("=").append(java.net.URLEncoder.encode(entry.getValue(), "UTF-8"));
            }

            Request request = new Request.Builder()
                    .url(url)
                    .header("Content-Type", "application/x-www-form-urlencoded")
                    .post(okhttp3.RequestBody.create(formBody.toString(), 
                            okhttp3.MediaType.parse("application/x-www-form-urlencoded")))
                    .build();

            try (Response response = httpClient.newCall(request).execute()) {
                if (!response.isSuccessful()) {
                    throw new RuntimeException("刷新 token 失败: HTTP " + response.code());
                }
                String body = response.body() != null ? response.body().string() : "{}";
                JsonNode result = JsonUtils.fromJson(body, JsonNode.class);
                
                String accessToken = result.path("access_token").asText(null);
                String newRefreshToken = result.path("refresh_token").asText(refreshToken); // 可能不变
                long expiresIn = result.path("expires_in").asLong(7200);

                if (accessToken == null) {
                    throw new RuntimeException("刷新 token 失败: " + body);
                }

                long now = System.currentTimeMillis();
                OAuth2Token token = OAuth2Token.builder()
                        .accessToken(accessToken)
                        .refreshToken(newRefreshToken)
                        .accessTokenExpireAt(now + expiresIn * 1000)
                        .refreshTokenExpireAt(now + 2592000 * 1000) // 30 天
                        .build();

                // 更新数据库
                accountService.updateOAuth2Token(accountId, token.getAccessToken(), 
                        token.getRefreshToken(), token.getAccessTokenExpireAt(), 
                        token.getRefreshTokenExpireAt());

                log.info("刷新 Access Token 成功: accountId={}", accountId);
                
                // 调度下次刷新
                scheduleTokenRefresh(accountId, token.getAccessTokenExpireAt());

                return token;
            }
        } catch (Exception e) {
            log.error("刷新 token 失败: accountId={}, error={}", accountId, e.getMessage());
            throw new RuntimeException("刷新 token 失败: " + e.getMessage());
        }
    }

    /**
     * 调度下次 token 刷新（过期前 5 分钟）
     */
    private void scheduleTokenRefresh(Long accountId, long expireAt) {
        long now = System.currentTimeMillis();
        long delayMs = expireAt - now - 5 * 60 * 1000; // 提前 5 分钟刷新

        if (delayMs > 0) {
            scheduler.schedule(() -> {
                try {
                    Account account = accountService.getById(accountId);
                    if (account != null && account.getRefreshToken() != null) {
                        refreshAccessToken(accountId, account.getRefreshToken());
                    }
                } catch (Exception e) {
                    log.warn("自动刷新 token 失败: accountId={}, error={}", accountId, e.getMessage());
                }
            }, delayMs, TimeUnit.MILLISECONDS);
            
            log.debug("调度下次 token 刷新: accountId={}, delayMs={}", accountId, delayMs);
        }
    }

    /**
     * 获取有效的 Access Token（自动刷新）
     */
    public String getValidAccessToken(Long accountId) {
        Account account = accountService.getById(accountId);
        if (account == null || account.getAccessToken() == null) {
            return null;
        }

        long now = System.currentTimeMillis();
        
        // 如果 token 即将过期（剩余不到 5 分钟），立即刷新
        if (account.getAccessTokenExpireAt() != null && 
            now > account.getAccessTokenExpireAt() - 5 * 60 * 1000) {
            
            if (account.getRefreshToken() != null) {
                OAuth2Token token = refreshAccessToken(accountId, account.getRefreshToken());
                return token.getAccessToken();
            }
            return null;
        }

        return account.getAccessToken();
    }

    /**
     * 判断 Access Token 是否有效
     */
    public boolean isAccessTokenValid(Long accountId) {
        Account account = accountService.getById(accountId);
        if (account == null || account.getAccessToken() == null) {
            return false;
        }
        long now = System.currentTimeMillis();
        return account.getAccessTokenExpireAt() != null && now < account.getAccessTokenExpireAt();
    }
}
