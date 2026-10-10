package com.xianyu.auto.system.controller;

import com.xianyu.auto.common.api.CommonResult;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.HashMap;
import java.util.Map;

/**
 * 公开接口（无需登录）
 * - /api/public/health: 容器健康检查
 */
@RestController
@RequestMapping("/api/public")
public class PublicController {

    /**
     * 健康检查端点（Docker HEALTHCHECK 用）
     */
    @GetMapping("/health")
    public CommonResult<Map<String, Object>> health() {
        Map<String, Object> info = new HashMap<>();
        info.put("status", "UP");
        info.put("timestamp", System.currentTimeMillis());
        info.put("service", "xianyu-auto");
        return CommonResult.success(info);
    }
}
