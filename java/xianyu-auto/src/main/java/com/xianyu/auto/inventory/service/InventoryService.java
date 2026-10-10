package com.xianyu.auto.inventory.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.xianyu.auto.inventory.entity.Inventory;

public interface InventoryService extends IService<Inventory> {

    /**
     * 按库存行 ID 扣减 1（规则 inventoryId / 商品 defaultInventoryId）
     */
    Inventory allocateById(Long inventoryId);

    /**
     * 按商品 ID 取一条可用库存并扣减
     */
    Inventory allocateByProductId(Long productId);

    /**
     * 兼容旧接口：语义为按商品 ID 分配
     */
    Inventory allocate(Long productId);

    /**
     * 发送失败时回补库存
     */
    void rollback(Long inventoryId);

    void markUsed(Long inventoryId, String orderId);
}
