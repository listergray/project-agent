package com.xianyu.auto.delivery.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.xianyu.auto.common.api.CommonResult;
import com.xianyu.auto.common.api.PageResult;
import com.xianyu.auto.common.exception.BusinessException;
import com.xianyu.auto.delivery.engine.AutoDeliveryEngine;
import com.xianyu.auto.delivery.entity.DeliveryLog;
import com.xianyu.auto.delivery.service.DeliveryLogService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/delivery/log")
@RequiredArgsConstructor
public class DeliveryLogController {

    private final DeliveryLogService deliveryLogService;
    private final AutoDeliveryEngine autoDeliveryEngine;

    @GetMapping("/page")
    public CommonResult<PageResult<DeliveryLog>> page(@RequestParam(defaultValue = "1") Integer pageNo,
                                                       @RequestParam(defaultValue = "20") Integer pageSize,
                                                       @RequestParam(required = false) String keyword,
                                                       @RequestParam(required = false) Long accountId,
                                                       @RequestParam(required = false) String status) {
        LambdaQueryWrapper<DeliveryLog> wrapper = new LambdaQueryWrapper<>();
        if (keyword != null && !keyword.isEmpty()) {
            wrapper.and(w -> w.like(DeliveryLog::getBuyerNick, keyword)
                    .or().like(DeliveryLog::getItemName, keyword)
                    .or().like(DeliveryLog::getOrderId, keyword));
        }
        if (accountId != null) {
            wrapper.eq(DeliveryLog::getAccountId, accountId);
        }
        if (status != null && !status.isEmpty()) {
            wrapper.eq(DeliveryLog::getStatus, status);
        }
        wrapper.orderByDesc(DeliveryLog::getCreatedAt);

        Page<DeliveryLog> page = deliveryLogService.page(new Page<>(pageNo, pageSize), wrapper);
        return CommonResult.success(new PageResult<>(page.getRecords(), page.getTotal()));
    }

    @GetMapping("/{id}")
    public CommonResult<DeliveryLog> get(@PathVariable Long id) {
        return CommonResult.success(deliveryLogService.getById(id));
    }

    /**
     * 手动重发（复用原发货内容，不重复扣库存）
     */
    @PostMapping("/{id}/resend")
    public CommonResult<Void> resend(@PathVariable Long id) {
        try {
            boolean ok = autoDeliveryEngine.resend(id);
            if (!ok) {
                throw new BusinessException("重发失败，请确认账号已连接");
            }
            return CommonResult.success("重发成功", null);
        } catch (IllegalArgumentException e) {
            throw new BusinessException(e.getMessage());
        }
    }
}
