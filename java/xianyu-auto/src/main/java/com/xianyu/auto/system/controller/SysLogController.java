package com.xianyu.auto.system.controller;

import com.xianyu.auto.common.api.CommonResult;
import com.xianyu.auto.common.api.PageResult;
import com.xianyu.auto.system.entity.SysLog;
import com.xianyu.auto.system.service.SysLogService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

/**
 * 操作日志
 */
@RestController
@RequestMapping("/api/system/logs")
@RequiredArgsConstructor
public class SysLogController {

    private final SysLogService logService;

    @GetMapping
    public CommonResult<PageResult<SysLog>> page(
            @RequestParam(defaultValue = "1") Integer pageNo,
            @RequestParam(defaultValue = "10") Integer pageSize,
            @RequestParam(required = false) String keyword,
            @RequestParam(required = false) String action) {
        return CommonResult.success(logService.page(pageNo, pageSize, keyword, action));
    }

    @DeleteMapping
    public CommonResult<Void> clearAll() {
        logService.remove(null);
        return CommonResult.success("清空成功", null);
    }
}
