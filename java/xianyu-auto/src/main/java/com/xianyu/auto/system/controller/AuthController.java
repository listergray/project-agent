package com.xianyu.auto.system.controller;

import cn.dev33.satoken.stp.StpUtil;
import com.xianyu.auto.common.api.CommonResult;
import com.xianyu.auto.common.exception.BusinessException;
import com.xianyu.auto.common.util.DateUtils;
import com.xianyu.auto.common.util.PasswordUtils;
import com.xianyu.auto.system.entity.SysUser;
import com.xianyu.auto.system.service.SysLogService;
import com.xianyu.auto.system.service.SysUserService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

/**
 * 认证控制器：登录、登出、获取当前用户信息
 */
@Slf4j
@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final SysUserService userService;
    private final SysLogService logService;

    @PostMapping("/login")
    public CommonResult<Map<String, Object>> login(@RequestBody LoginRequest req, HttpServletRequest request) {
        long start = System.currentTimeMillis();
        if (req.getUsername() == null || req.getPassword() == null) {
            throw new BusinessException("用户名和密码不能为空");
        }
        SysUser user = userService.findByUsername(req.getUsername());
        if (user == null || !PasswordUtils.verify(req.getPassword(), user.getPasswordHash())) {
            throw new BusinessException("用户名或密码错误");
        }
        if (user.getStatus() != null && user.getStatus() == 0) {
            throw new BusinessException("账号已被禁用");
        }
        // Sa-Token 登录
        StpUtil.login(user.getId());
        String token = StpUtil.getTokenValue();

        // 更新登录信息
        user.setLastLoginAt(DateUtils.nowMillis());
        user.setLastLoginIp(getClientIp(request));
        user.setUpdatedAt(DateUtils.nowMillis());
        userService.updateById(user);

        // 记录日志
        logService.record(user.getUsername(), "LOGIN", "/api/auth/login",
                req.getUsername(), "success", getClientIp(request),
                System.currentTimeMillis() - start, null);

        Map<String, Object> result = new HashMap<>();
        result.put("token", token);
        result.put("userInfo", user);
        return CommonResult.success("登录成功", result);
    }

    @PostMapping("/logout")
    public CommonResult<Void> logout() {
        Object userId = StpUtil.getLoginIdDefaultNull();
        if (userId != null) {
            SysUser user = userService.getById(Long.valueOf(userId.toString()));
            String username = user != null ? user.getUsername() : "unknown";
            logService.record(username, "LOGOUT", "/api/auth/logout", null, "success", null, 0L, null);
        }
        StpUtil.logout();
        return CommonResult.success("退出成功", null);
    }

    @GetMapping("/info")
    public CommonResult<SysUser> info() {
        Long userId = StpUtil.getLoginIdAsLong();
        SysUser user = userService.getById(userId);
        if (user == null) {
            throw new BusinessException("用户不存在");
        }
        return CommonResult.success(user);
    }

    @PostMapping("/refresh-token")
    public CommonResult<Map<String, Object>> refreshToken() {
        Long userId = StpUtil.getLoginIdAsLong();
        SysUser user = userService.getById(userId);
        if (user == null) {
            throw new BusinessException("用户不存在");
        }
        // 重新登录生成新 Token
        StpUtil.login(userId);
        String newToken = StpUtil.getTokenValue();
        Map<String, Object> result = new HashMap<>();
        result.put("token", newToken);
        return CommonResult.success("Token 已刷新", result);
    }

    @PostMapping("/change-password")
    public CommonResult<Void> changePassword(@RequestBody ChangePasswordRequest req) {
        Long userId = StpUtil.getLoginIdAsLong();
        userService.changePassword(userId, req.getOldPassword(), req.getNewPassword());
        return CommonResult.success("密码修改成功", null);
    }

    private String getClientIp(HttpServletRequest request) {
        String ip = request.getHeader("X-Forwarded-For");
        if (ip == null || ip.isEmpty()) ip = request.getHeader("X-Real-IP");
        if (ip == null || ip.isEmpty()) ip = request.getRemoteAddr();
        return ip;
    }

    @Data
    public static class LoginRequest {
        @NotBlank private String username;
        @NotBlank private String password;
    }

    @Data
    public static class ChangePasswordRequest {
        @NotBlank private String oldPassword;
        @NotBlank private String newPassword;
    }
}
