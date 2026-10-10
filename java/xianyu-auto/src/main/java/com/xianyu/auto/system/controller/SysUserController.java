package com.xianyu.auto.system.controller;

import com.baomidou.mybatisplus.core.metadata.IPage;
import com.xianyu.auto.common.api.CommonResult;
import com.xianyu.auto.common.api.PageResult;
import com.xianyu.auto.common.util.DateUtils;
import com.xianyu.auto.system.entity.SysUser;
import com.xianyu.auto.system.service.SysLogService;
import com.xianyu.auto.system.service.SysUserService;
import jakarta.servlet.http.HttpServletRequest;
import lombok.Data;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

/**
 * 系统用户管理
 */
@RestController
@RequestMapping("/api/system/users")
@RequiredArgsConstructor
public class SysUserController {

    private final SysUserService userService;
    private final SysLogService logService;

    @GetMapping
    public CommonResult<PageResult<SysUser>> page(
            @RequestParam(defaultValue = "1") Integer pageNo,
            @RequestParam(defaultValue = "10") Integer pageSize,
            @RequestParam(required = false) String keyword) {
        return CommonResult.success(userService.page(pageNo, pageSize, keyword));
    }

    @PostMapping
    public CommonResult<Void> create(@RequestBody SysUser user, HttpServletRequest request) {
        userService.createUser(user);
        logService.record(getCurrentUsername(), "CREATE_USER", "/api/system/users",
                user.getUsername(), "success", null, 0L, null);
        return CommonResult.success("创建成功", null);
    }

    @PutMapping("/{id}")
    public CommonResult<Void> update(@PathVariable Long id, @RequestBody SysUser user) {
        user.setId(id);
        userService.updateUser(user);
        return CommonResult.success("更新成功", null);
    }

    @DeleteMapping
    public CommonResult<Void> delete(@RequestBody List<Long> ids) {
        userService.deleteUsers(ids);
        return CommonResult.success("删除成功", null);
    }

    @PutMapping("/{id}/reset-password")
    public CommonResult<Void> resetPassword(@PathVariable Long id, @RequestBody ResetPasswordRequest req) {
        userService.resetPassword(id, req.getNewPassword());
        return CommonResult.success("重置成功", null);
    }

    @PutMapping("/{id}/status")
    public CommonResult<Void> changeStatus(@PathVariable Long id, @RequestBody ChangeStatusRequest req) {
        SysUser user = new SysUser();
        user.setId(id);
        user.setStatus(req.getStatus());
        user.setUpdatedAt(DateUtils.nowMillis());
        userService.updateById(user);
        return CommonResult.success("状态更新成功", null);
    }

    private String getCurrentUsername() {
        return "system";  // 简化实现，Phase 6 可补充 Sa-Token 获取当前用户
    }

    @Data
    public static class ResetPasswordRequest {
        private String newPassword;
    }

    @Data
    public static class ChangeStatusRequest {
        private Integer status;
    }
}
