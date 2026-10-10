package com.xianyu.auto.account.controller;

import com.xianyu.auto.account.service.AccountService;
import com.xianyu.auto.common.api.CommonResult;
import com.xianyu.auto.common.exception.BusinessException;
import com.xianyu.auto.xianyu.client.XianyuWsManager;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * 闲鱼账号连接管理
 * 提供启动/断开/重连 WS 连接的 API
 */
@RestController
@RequestMapping("/api/account")
@RequiredArgsConstructor
public class AccountConnectionController {

    private final XianyuWsManager wsManager;
    private final AccountService accountService;

    /**
     * 启动 WebSocket 连接
     */
    @PostMapping("/{id}/connect")
    public CommonResult<Void> connect(@PathVariable Long id) {
        try {
            wsManager.connect(id);
            return CommonResult.success("连接启动中", null);
        } catch (BusinessException e) {
            return CommonResult.error(e.getCode(), e.getMessage());
        } catch (Exception e) {
            return CommonResult.error("连接启动失败: " + e.getMessage());
        }
    }

    /**
     * 断开 WebSocket 连接
     */
    @PostMapping("/{id}/disconnect")
    public CommonResult<Void> disconnect(@PathVariable Long id) {
        wsManager.disconnect(id);
        return CommonResult.success("已断开", null);
    }

    /**
     * 手动重连
     */
    @PostMapping("/{id}/reconnect")
    public CommonResult<Void> reconnect(@PathVariable Long id) {
        wsManager.disconnect(id);
        try {
            Thread.sleep(500);
        } catch (InterruptedException ignored) {
            Thread.currentThread().interrupt();
        }
        wsManager.connect(id);
        return CommonResult.success("重连中", null);
    }

    /**
     * 查询连接状态（详细）
     */
    @GetMapping("/{id}/ws-status")
    public CommonResult<Map<String, Object>> wsStatus(@PathVariable Long id) {
        return CommonResult.success(wsManager.getStatus(id));
    }

    /**
     * 查询所有账号连接状态
     */
    @GetMapping("/ws-status")
    public CommonResult<Map<Long, Map<String, Object>>> allWsStatus() {
        return CommonResult.success(wsManager.getAllStatus());
    }
}
