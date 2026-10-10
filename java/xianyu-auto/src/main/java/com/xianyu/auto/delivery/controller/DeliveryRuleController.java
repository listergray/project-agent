package com.xianyu.auto.delivery.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.xianyu.auto.common.api.CommonResult;
import com.xianyu.auto.common.api.PageResult;
import com.xianyu.auto.delivery.entity.DeliveryRule;
import com.xianyu.auto.delivery.service.DeliveryRuleService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/delivery/rule")
@RequiredArgsConstructor
public class DeliveryRuleController {

    private final DeliveryRuleService deliveryRuleService;

    @GetMapping("/page")
    public CommonResult<PageResult<DeliveryRule>> page(@RequestParam(defaultValue = "1") Integer pageNo,
                                                        @RequestParam(defaultValue = "20") Integer pageSize,
                                                        @RequestParam(required = false) String keyword,
                                                        @RequestParam(required = false) Long accountId) {
        LambdaQueryWrapper<DeliveryRule> wrapper = new LambdaQueryWrapper<>();
        if (keyword != null && !keyword.isEmpty()) {
            wrapper.like(DeliveryRule::getName, keyword);
        }
        if (accountId != null) {
            wrapper.eq(DeliveryRule::getAccountId, accountId);
        }
        wrapper.orderByDesc(DeliveryRule::getPriority).orderByDesc(DeliveryRule::getCreatedAt);

        Page<DeliveryRule> page = deliveryRuleService.page(new Page<>(pageNo, pageSize), wrapper);
        return CommonResult.success(new PageResult<>(page.getRecords(), page.getTotal()));
    }

    @GetMapping("/list")
    public CommonResult<List<DeliveryRule>> list(@RequestParam(required = false) Long accountId) {
        LambdaQueryWrapper<DeliveryRule> wrapper = new LambdaQueryWrapper<>();
        if (accountId != null) {
            wrapper.eq(DeliveryRule::getAccountId, accountId);
        }
        wrapper.orderByDesc(DeliveryRule::getPriority);
        return CommonResult.success(deliveryRuleService.list(wrapper));
    }

    @GetMapping("/{id}")
    public CommonResult<DeliveryRule> get(@PathVariable Long id) {
        return CommonResult.success(deliveryRuleService.getById(id));
    }

    @PostMapping
    public CommonResult<Void> create(@RequestBody DeliveryRule rule) {
        if (rule.getPriority() == null) rule.setPriority(100);
        if (rule.getEnabled() == null) rule.setEnabled(1);
        if (rule.getAutoConfirm() == null) rule.setAutoConfirm(1);
        if (rule.getDelaySeconds() == null) rule.setDelaySeconds(0);
        if (rule.getCreatedAt() == null) rule.setCreatedAt(System.currentTimeMillis());
        if (rule.getUpdatedAt() == null) rule.setUpdatedAt(System.currentTimeMillis());
        deliveryRuleService.save(rule);
        return CommonResult.success();
    }

    @PutMapping("/{id}")
    public CommonResult<Void> update(@PathVariable Long id, @RequestBody DeliveryRule rule) {
        rule.setId(id);
        rule.setUpdatedAt(System.currentTimeMillis());
        deliveryRuleService.updateById(rule);
        return CommonResult.success();
    }

    @DeleteMapping("/{id}")
    public CommonResult<Void> delete(@PathVariable Long id) {
        deliveryRuleService.removeById(id);
        return CommonResult.success();
    }
}
