package com.xianyu.auto.xianyu.oauth2;

import com.xianyu.auto.account.entity.Account;
import com.xianyu.auto.account.service.AccountService;
import com.xianyu.auto.common.api.CommonResult;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

/**
 * 闲鱼开放平台 OAuth2.0 控制器
 */
@Slf4j
@RestController
@RequestMapping("/api/oauth2")
@RequiredArgsConstructor
public class OAuth2Controller {

    private final XianyuOAuth2Service oAuth2Service;
    private final AccountService accountService;

    /**
     * 获取授权 URL
     * 
     * @param accountId 账号 ID
     * @return 授权 URL
     */
    @GetMapping("/auth-url")
    public CommonResult<Map<String, String>> getAuthUrl(@RequestParam Long accountId) {
        try {
            Account account = accountService.getById(accountId);
            if (account == null) {
                return CommonResult.error("账号不存在");
            }
            
            String authUrl = oAuth2Service.generateAuthUrl(accountId);
            
            Map<String, String> result = new HashMap<>();
            result.put("authUrl", authUrl);
            result.put("accountId", String.valueOf(accountId));
            result.put("nickname", account.getNickname());
            
            return CommonResult.success("授权 URL 生成成功", result);
        } catch (Exception e) {
            log.error("生成授权 URL 失败: {}", e.getMessage());
            return CommonResult.error("生成授权 URL 失败: " + e.getMessage());
        }
    }

    /**
     * 授权回调（闲鱼开放平台会调用此接口）
     * 
     * @param code 授权码
     * @param state 随机字符串
     * @return 授权结果页面
     */
    @GetMapping("/callback")
    public String callback(@RequestParam String code, @RequestParam String state) {
        try {
            Long accountId = oAuth2Service.handleCallback(code, state);
            Account account = accountService.getById(accountId);
            
            // 返回成功页面
            return "<html><body>" +
                    "<h1>授权成功！</h1>" +
                    "<p>账号: " + (account != null ? account.getNickname() : accountId) + "</p>" +
                    "<p>授权类型: OAuth2.0</p>" +
                    "<p><a href=\"/\">返回系统</a></p>" +
                    "</body></html>";
        } catch (Exception e) {
            log.error("授权回调失败: {}", e.getMessage());
            return "<html><body>" +
                    "<h1>授权失败</h1>" +
                    "<p>错误: " + e.getMessage() + "</p>" +
                    "<p><a href=\"/\">返回系统</a></p>" +
                    "</body></html>";
        }
    }

    /**
     * 刷新 Access Token
     * 
     * @param accountId 账号 ID
     * @return 刷新结果
     */
    @PostMapping("/refresh-token")
    public CommonResult<Map<String, Object>> refreshToken(@RequestParam Long accountId) {
        try {
            Account account = accountService.getById(accountId);
            if (account == null) {
                return CommonResult.error("账号不存在");
            }
            if (account.getRefreshToken() == null) {
                return CommonResult.error("该账号未配置 Refresh Token");
            }

            OAuth2Token token = oAuth2Service.refreshAccessToken(accountId, account.getRefreshToken());
            
            Map<String, Object> result = new HashMap<>();
            result.put("accountId", accountId);
            result.put("accessTokenExpireAt", token.getAccessTokenExpireAt());
            result.put("refreshTokenExpireAt", token.getRefreshTokenExpireAt());
            
            return CommonResult.success("Token 刷新成功", result);
        } catch (Exception e) {
            log.error("刷新 token 失败: {}", e.getMessage());
            return CommonResult.error("刷新 token 失败: " + e.getMessage());
        }
    }

    /**
     * 获取 Access Token 状态
     * 
     * @param accountId 账号 ID
     * @return token 状态
     */
    @GetMapping("/token-status")
    public CommonResult<Map<String, Object>> getTokenStatus(@RequestParam Long accountId) {
        try {
            Account account = accountService.getById(accountId);
            if (account == null) {
                return CommonResult.error("账号不存在");
            }

            long now = System.currentTimeMillis();
            
            Map<String, Object> result = new HashMap<>();
            result.put("accountId", accountId);
            result.put("authType", account.getAuthType());
            result.put("hasAccessToken", account.getAccessToken() != null);
            result.put("hasRefreshToken", account.getRefreshToken() != null);
            
            if (account.getAccessTokenExpireAt() != null) {
                result.put("accessTokenExpireAt", account.getAccessTokenExpireAt());
                result.put("accessTokenRemainingSeconds", 
                        Math.max(0, (account.getAccessTokenExpireAt() - now) / 1000));
                result.put("accessTokenValid", now < account.getAccessTokenExpireAt());
            }
            
            if (account.getRefreshTokenExpireAt() != null) {
                result.put("refreshTokenExpireAt", account.getRefreshTokenExpireAt());
                result.put("refreshTokenRemainingSeconds", 
                        Math.max(0, (account.getRefreshTokenExpireAt() - now) / 1000));
                result.put("refreshTokenValid", now < account.getRefreshTokenExpireAt());
            }
            
            return CommonResult.success("获取成功", result);
        } catch (Exception e) {
            log.error("获取 token 状态失败: {}", e.getMessage());
            return CommonResult.error("获取 token 状态失败: " + e.getMessage());
        }
    }
}
