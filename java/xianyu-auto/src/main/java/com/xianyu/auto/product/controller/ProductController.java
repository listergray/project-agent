package com.xianyu.auto.product.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.xianyu.auto.common.api.CommonResult;
import com.xianyu.auto.common.api.PageResult;
import com.xianyu.auto.inventory.entity.Inventory;
import com.xianyu.auto.inventory.service.InventoryService;
import com.xianyu.auto.product.entity.Product;
import com.xianyu.auto.product.service.ProductService;
import com.xianyu.auto.product.service.XianyuItemService;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/product")
@RequiredArgsConstructor
public class ProductController {

    private final ProductService productService;
    private final InventoryService inventoryService;
    private final XianyuItemService xianyuItemService;

    @GetMapping("/page")
    public CommonResult<PageResult<Product>> page(@RequestParam(defaultValue = "1") Integer pageNo,
                                                   @RequestParam(defaultValue = "20") Integer pageSize,
                                                   @RequestParam(required = false) String keyword,
                                                   @RequestParam(required = false) Long accountId,
                                                   @RequestParam(required = false) String shelfStatus) {
        LambdaQueryWrapper<Product> wrapper = new LambdaQueryWrapper<>();
        if (keyword != null && !keyword.isEmpty()) {
            wrapper.and(w -> w.like(Product::getName, keyword)
                    .or().like(Product::getTitle, keyword)
                    .or().like(Product::getXianyuItemId, keyword));
        }
        if (accountId != null) {
            wrapper.eq(Product::getAccountId, accountId);
        }
        if (shelfStatus != null && !shelfStatus.isEmpty()) {
            wrapper.eq(Product::getShelfStatus, shelfStatus);
        }
        wrapper.orderByDesc(Product::getUpdatedAt);

        Page<Product> page = productService.page(new Page<>(pageNo, pageSize), wrapper);
        page.getRecords().forEach(this::fillStockInfo);
        return CommonResult.success(new PageResult<>(page.getRecords(), page.getTotal()));
    }

    @GetMapping("/list")
    public CommonResult<List<Product>> list(@RequestParam(required = false) Long accountId) {
        LambdaQueryWrapper<Product> wrapper = new LambdaQueryWrapper<>();
        if (accountId != null) {
            wrapper.eq(Product::getAccountId, accountId);
        }
        // 下拉关联优先展示在售/启用商品，其余排后
        wrapper.orderByAsc(Product::getShelfStatus).orderByAsc(Product::getId);
        List<Product> list = productService.list(wrapper);
        list.forEach(this::fillStockInfo);
        return CommonResult.success(list);
    }

    @GetMapping("/{id}")
    public CommonResult<Product> get(@PathVariable Long id) {
        Product product = productService.getById(id);
        fillStockInfo(product);
        return CommonResult.success(product);
    }

    @PostMapping
    public CommonResult<Void> create(@RequestBody Product product) {
        if (product.getAutoDelivery() == null) product.setAutoDelivery(0);
        if (product.getStatus() == null) product.setStatus(Product.STATUS_ENABLED);
        if (product.getShelfStatus() == null) product.setShelfStatus(Product.SHELF_OFF);
        if (product.getSyncStatus() == null) product.setSyncStatus(Product.SYNC_LOCAL);
        if (product.getCreatedAt() == null) product.setCreatedAt(System.currentTimeMillis());
        if (product.getUpdatedAt() == null) product.setUpdatedAt(System.currentTimeMillis());
        if (product.getName() == null && product.getTitle() != null) {
            product.setName(product.getTitle());
        }
        productService.save(product);
        return CommonResult.success();
    }

    @PutMapping("/{id}")
    public CommonResult<Void> update(@PathVariable Long id, @RequestBody Product product) {
        product.setId(id);
        product.setUpdatedAt(System.currentTimeMillis());
        productService.updateById(product);
        return CommonResult.success();
    }

    @DeleteMapping("/{id}")
    public CommonResult<Void> delete(@PathVariable Long id) {
        productService.removeById(id);
        return CommonResult.success();
    }

    @PostMapping("/sync/{accountId}")
    public CommonResult<Map<String, Object>> sync(@PathVariable Long accountId) {
        return CommonResult.success(xianyuItemService.syncFromXianyu(accountId));
    }

    @PostMapping("/{id}/shelf")
    public CommonResult<Void> shelf(@PathVariable Long id,
                                    @RequestParam boolean onSale,
                                    @RequestParam(required = false) Long accountId) {
        xianyuItemService.setShelf(accountId, id, onSale);
        return CommonResult.success();
    }

    @PostMapping("/{id}/copy")
    public CommonResult<Product> copy(@PathVariable Long id) {
        return CommonResult.success(xianyuItemService.copyLocal(id));
    }

    @PostMapping("/{id}/refresh-detail")
    public CommonResult<Void> refreshDetail(@PathVariable Long id,
                                            @RequestParam(required = false) Long accountId) {
        xianyuItemService.refreshDetail(accountId, id);
        return CommonResult.success();
    }

    @PostMapping("/migrate")
    public CommonResult<Map<String, Object>> migrate(@RequestBody Map<String, Object> body) {
        Long fromAccountId = Long.valueOf(body.get("fromAccountId").toString());
        Long toAccountId = Long.valueOf(body.get("toAccountId").toString());
        @SuppressWarnings("unchecked")
        List<Object> rawIds = (List<Object>) body.get("productIds");
        List<Long> productIds = rawIds.stream().map(o -> Long.valueOf(o.toString())).toList();
        return CommonResult.success(xianyuItemService.migrateItems(fromAccountId, toAccountId, productIds));
    }

    private void fillStockInfo(Product product) {
        if (product == null) return;
        List<Inventory> invList = inventoryService.list(new LambdaQueryWrapper<Inventory>()
                .eq(Inventory::getProductId, product.getId()));
        int totalStock = invList.stream().mapToInt(Inventory::getStock).sum();
        int usedCount = invList.stream().mapToInt(Inventory::getUsedCount).sum();
        product.setTotalStock(totalStock);
        product.setUsedCount(usedCount);
    }
}
