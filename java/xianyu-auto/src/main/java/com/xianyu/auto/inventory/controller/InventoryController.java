package com.xianyu.auto.inventory.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.xianyu.auto.common.api.CommonResult;
import com.xianyu.auto.common.api.PageResult;
import com.xianyu.auto.inventory.entity.Inventory;
import com.xianyu.auto.inventory.service.InventoryService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/inventory")
@RequiredArgsConstructor
public class InventoryController {

    private final InventoryService inventoryService;

    @GetMapping("/page")
    public CommonResult<PageResult<Inventory>> page(@RequestParam(defaultValue = "1") Integer pageNo,
                                                     @RequestParam(defaultValue = "20") Integer pageSize,
                                                     @RequestParam(required = false) String keyword,
                                                     @RequestParam(required = false) String type,
                                                     @RequestParam(required = false) Long productId) {
        LambdaQueryWrapper<Inventory> wrapper = new LambdaQueryWrapper<>();
        if (keyword != null && !keyword.isEmpty()) {
            wrapper.like(Inventory::getCode, keyword).or().like(Inventory::getContent, keyword);
        }
        if (type != null && !type.isEmpty()) {
            wrapper.eq(Inventory::getType, type);
        }
        if (productId != null) {
            wrapper.eq(Inventory::getProductId, productId);
        }
        wrapper.orderByDesc(Inventory::getCreatedAt);

        Page<Inventory> page = inventoryService.page(new Page<>(pageNo, pageSize), wrapper);
        return CommonResult.success(new PageResult<>(page.getRecords(), page.getTotal()));
    }

    @GetMapping("/list")
    public CommonResult<List<Inventory>> list(@RequestParam(required = false) Long productId) {
        LambdaQueryWrapper<Inventory> wrapper = new LambdaQueryWrapper<>();
        if (productId != null) {
            wrapper.eq(Inventory::getProductId, productId);
        }
        wrapper.orderByAsc(Inventory::getId);
        return CommonResult.success(inventoryService.list(wrapper));
    }

    @GetMapping("/{id}")
    public CommonResult<Inventory> get(@PathVariable Long id) {
        return CommonResult.success(inventoryService.getById(id));
    }

    @PostMapping
    public CommonResult<Void> create(@RequestBody Inventory inventory) {
        if (inventory.getStock() == null) inventory.setStock(1);
        if (inventory.getUsedCount() == null) inventory.setUsedCount(0);
        if (inventory.getStatus() == null) inventory.setStatus(Inventory.STATUS_AVAILABLE);
        if (inventory.getCreatedAt() == null) inventory.setCreatedAt(System.currentTimeMillis());
        if (inventory.getUpdatedAt() == null) inventory.setUpdatedAt(System.currentTimeMillis());
        inventoryService.save(inventory);
        return CommonResult.success();
    }

    @PostMapping("/batch")
    public CommonResult<Void> batchCreate(@RequestBody Map<String, Object> params) {
        @SuppressWarnings("unchecked")
        List<String> codes = (List<String>) params.get("codes");
        String content = (String) params.get("content");
        String type = (String) params.get("type");
        Long productId = params.get("productId") != null ? Long.valueOf(params.get("productId").toString()) : null;
        Long now = System.currentTimeMillis();

        for (String code : codes) {
            Inventory inv = new Inventory();
            inv.setCode(code.trim());
            inv.setContent(content);
            inv.setType(type);
            inv.setProductId(productId);
            inv.setStock(1);
            inv.setUsedCount(0);
            inv.setStatus(Inventory.STATUS_AVAILABLE);
            inv.setCreatedAt(now);
            inv.setUpdatedAt(now);
            inventoryService.save(inv);
        }
        return CommonResult.success();
    }

    @PutMapping("/{id}")
    public CommonResult<Void> update(@PathVariable Long id, @RequestBody Inventory inventory) {
        inventory.setId(id);
        inventory.setUpdatedAt(System.currentTimeMillis());
        inventoryService.updateById(inventory);
        return CommonResult.success();
    }

    @DeleteMapping("/{id}")
    public CommonResult<Void> delete(@PathVariable Long id) {
        inventoryService.removeById(id);
        return CommonResult.success();
    }

    @DeleteMapping("/batch")
    public CommonResult<Void> batchDelete(@RequestBody List<Long> ids) {
        inventoryService.removeByIds(ids);
        return CommonResult.success();
    }
}
