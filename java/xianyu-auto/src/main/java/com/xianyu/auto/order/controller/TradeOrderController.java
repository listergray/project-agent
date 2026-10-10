package com.xianyu.auto.order.controller;

import com.xianyu.auto.common.api.CommonResult;
import com.xianyu.auto.common.api.PageResult;
import com.xianyu.auto.order.entity.TradeOrder;
import com.xianyu.auto.order.service.TradeOrderService;
import com.xianyu.auto.order.service.TradeOrderSyncService;
import com.xianyu.auto.xianyu.client.XianyuApiClient;
import com.xianyu.auto.xianyu.auth.CookieManager;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/order")
@RequiredArgsConstructor
public class TradeOrderController {

    private final TradeOrderService tradeOrderService;
    private final TradeOrderSyncService tradeOrderSyncService;
    private final XianyuApiClient xianyuApiClient;
    private final CookieManager cookieManager;

    @GetMapping("/page")
    public CommonResult<PageResult<TradeOrder>> page(
            @RequestParam(defaultValue = "1") Integer pageNo,
            @RequestParam(defaultValue = "20") Integer pageSize,
            @RequestParam(required = false) Long accountId,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String keyword) {
        return CommonResult.success(tradeOrderService.page(pageNo, pageSize, accountId, status, keyword));
    }

    @GetMapping("/{id}")
    public CommonResult<TradeOrder> detail(@PathVariable Long id) {
        return CommonResult.success(tradeOrderService.getById(id));
    }

    /** 从闲鱼卖家已售列表同步订单 */
    @PostMapping("/sync/{accountId}")
    public CommonResult<Map<String, Object>> sync(@PathVariable Long accountId) {
        return CommonResult.success(tradeOrderSyncService.syncFromXianyu(accountId));
    }

    /** 手动确认发货（调用闲鱼 consign） */
    @PostMapping("/{id}/consign")
    public CommonResult<Map<String, Object>> consign(@PathVariable Long id) {
        TradeOrder order = tradeOrderService.getById(id);
        if (order == null) {
            return CommonResult.error("订单不存在");
        }
        String cookie = cookieManager.getCookie(order.getAccountId());
        boolean ok = xianyuApiClient.tradeConsignment(cookie, order.getOrderId());
        String consign = ok ? "SUCCESS" : "FAILED";
        tradeOrderService.markConsign(order.getAccountId(), order.getOrderId(), consign);
        Map<String, Object> result = new HashMap<>();
        result.put("success", ok);
        result.put("consignStatus", consign);
        return CommonResult.success(result);
    }
}
