package com.xianyu.auto.account.controller;

import com.xianyu.auto.account.entity.Account;
import com.xianyu.auto.account.service.AccountService;
import com.xianyu.auto.common.api.CommonResult;
import com.xianyu.auto.common.api.PageParam;
import com.xianyu.auto.common.api.PageResult;
import com.xianyu.auto.xianyu.auth.TokenRefresher;
import com.xianyu.auto.xianyu.client.XianyuApiClient;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

/**
 * 闲鱼账号管理
 * 注意：Cookie 单独接口录入，不与基础 CRUD 混在一起
 */
@RestController
@RequestMapping("/api/account")
@RequiredArgsConstructor
public class AccountController {

    private final AccountService accountService;
    private final XianyuApiClient xianyuApiClient;
    private final TokenRefresher tokenRefresher;

    /**
     * 分页查询账号列表
     */
    @GetMapping("/page")
    public CommonResult<PageResult<Account>> page(PageParam page,
                                                  @RequestParam(required = false) String keyword) {
        return CommonResult.success(accountService.page(page.getPageNo(), page.getPageSize(), keyword));
    }

    /**
     * 查询全部账号（简化列表，用于下拉选择）
     */
    @GetMapping("/all")
    public CommonResult<?> all() {
        return CommonResult.success(accountService.list());
    }

    /**
     * 查询账号详情（不含 Cookie）
     */
    @GetMapping("/{id}")
    public CommonResult<Account> get(@PathVariable Long id) {
        return CommonResult.success(accountService.getById(id));
    }

    /**
     * 创建账号（仅基本字段：nickname / auto_start）
     */
    @PostMapping
    public CommonResult<Account> create(@RequestBody Account account) {
        return CommonResult.success(accountService.create(account));
    }

    /**
     * 更新账号基础信息
     */
    @PutMapping("/{id}")
    public CommonResult<Void> update(@PathVariable Long id, @RequestBody Account account) {
        account.setId(id);
        accountService.update(account);
        return CommonResult.success("更新成功", null);
    }

    /**
     * 单独更新 Cookie（AES 加密落库）
     * Body: { "cookie": "完整的 Cookie 字符串" }
     */
    @PutMapping("/{id}/cookie")
    public CommonResult<Void> updateCookie(@PathVariable Long id, @RequestBody Map<String, String> body) {
        String cookie = body.get("cookie");
        accountService.updateCookie(id, cookie);
        return CommonResult.success("Cookie 已保存", null);
    }

    /**
     * 查询账号状态（用于前端轮询）
     */
    @GetMapping("/{id}/status")
    public CommonResult<Map<String, Object>> getStatus(@PathVariable Long id) {
        Account account = accountService.getById(id);
        if (account == null) {
            return CommonResult.error(404, "账号不存在");
        }
        Map<String, Object> info = new HashMap<>();
        info.put("id", account.getId());
        info.put("status", account.getStatus());
        info.put("lastError", account.getLastError());
        info.put("lastKeepaliveAt", account.getLastKeepaliveAt());
        info.put("lastLoginAt", account.getLastLoginAt());
        info.put("hasCookie", account.getCookieText() != null && !account.getCookieText().isEmpty());
        info.put("hasWsToken", account.getWsToken() != null && !account.getWsToken().isEmpty());
        info.put("userId", account.getUserId());
        return CommonResult.success(info);
    }

    /**
     * 删除账号
     */
    @DeleteMapping("/{id}")
    public CommonResult<Void> delete(@PathVariable Long id) {
        accountService.delete(id);
        return CommonResult.success("删除成功", null);
    }

    /**
     * 测试 hasLogin（手动触发登录态校验）
     */
    @PostMapping("/{id}/test-has-login")
    public CommonResult<Map<String, Object>> testHasLogin(@PathVariable Long id) {
        String cookie = accountService.getDecryptedCookie(id);
        if (cookie == null) {
            return CommonResult.error(400, "Cookie 未录入");
        }
        boolean alive = xianyuApiClient.hasLogin(cookie);
        Map<String, Object> result = new HashMap<>();
        result.put("alive", alive);
        result.put("accountId", id);
        return CommonResult.success(result);
    }

    /**
     * 手动刷新 _m_h5_tk
     */
    @PostMapping("/{id}/refresh-mh5-tk")
    public CommonResult<Map<String, Object>> refreshMh5Tk(@PathVariable Long id) {
        String cookie = accountService.getDecryptedCookie(id);
        if (cookie == null) {
            return CommonResult.error(400, "Cookie 未录入");
        }
        String refreshedCookie = xianyuApiClient.refreshMh5Tk(cookie);
        boolean updated = !refreshedCookie.equals(cookie);
        if (updated) {
            accountService.updateCookie(id, refreshedCookie);
        }
        Map<String, Object> result = new HashMap<>();
        result.put("updated", updated);
        result.put("accountId", id);
        return CommonResult.success(result);
    }

    /**
     * 手动刷新 WS Token
     */
    @PostMapping("/{id}/refresh-ws-token")
    public CommonResult<Map<String, Object>> refreshWsToken(@PathVariable Long id) {
        String wsToken = tokenRefresher.refreshWsToken(id);
        Map<String, Object> result = new HashMap<>();
        result.put("success", wsToken != null && !wsToken.isEmpty());
        result.put("accountId", id);
        return CommonResult.success(result);
    }
}
