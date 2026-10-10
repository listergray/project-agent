package com.xianyu.auto.system.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.xianyu.auto.common.api.CommonResult;
import com.xianyu.auto.system.entity.SysConfig;
import com.xianyu.auto.system.service.SysConfigService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 系统配置管理
 */
@RestController
@RequestMapping("/api/system/configs")
@RequiredArgsConstructor
public class SysConfigController {

    private final SysConfigService configService;

    @GetMapping
    public CommonResult<List<SysConfig>> list(@RequestParam(required = false) String group) {
        LambdaQueryWrapper<SysConfig> wrapper = new LambdaQueryWrapper<>();
        if (group != null && !group.isEmpty()) {
            wrapper.eq(SysConfig::getConfigGroup, group);
        }
        wrapper.orderByAsc(SysConfig::getConfigGroup).orderByAsc(SysConfig::getConfigKey);
        return CommonResult.success(configService.list(wrapper));
    }

    @GetMapping("/group/{group}")
    public CommonResult<Map<String, String>> getByGroup(@PathVariable String group) {
        return CommonResult.success(configService.getConfigsByGroup(group));
    }

    @GetMapping("/key/{key}")
    public CommonResult<String> getByKey(@PathVariable String key) {
        return CommonResult.success(configService.getConfigValue(key));
    }

    @PostMapping("/batch")
    public CommonResult<Void> saveOrUpdate(@RequestBody List<SysConfig> configs) {
        configService.saveOrUpdate(configs);
        return CommonResult.success("保存成功", null);
    }

    @PostMapping
    public CommonResult<Void> save(@RequestBody SysConfig config) {
        configService.saveOrUpdate(List.of(config));
        return CommonResult.success("保存成功", null);
    }

    @DeleteMapping("/{key}")
    public CommonResult<Void> delete(@PathVariable String key) {
        configService.deleteByKey(key);
        return CommonResult.success("删除成功", null);
    }
}
