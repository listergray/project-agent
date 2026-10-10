package com.xianyu.auto.inventory.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.xianyu.auto.inventory.entity.Inventory;
import com.xianyu.auto.inventory.mapper.InventoryMapper;
import com.xianyu.auto.inventory.service.InventoryService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Slf4j
@Service
@RequiredArgsConstructor
public class InventoryServiceImpl extends ServiceImpl<InventoryMapper, Inventory> implements InventoryService {

    @Override
    @Transactional
    public Inventory allocateById(Long inventoryId) {
        if (inventoryId == null) {
            return null;
        }
        synchronized (InventoryServiceImpl.class) {
            Inventory inv = this.getById(inventoryId);
            if (inv == null) {
                log.warn("库存不存在: id={}", inventoryId);
                return null;
            }
            if (!Inventory.STATUS_AVAILABLE.equals(inv.getStatus()) || inv.getStock() == null || inv.getStock() <= 0) {
                log.warn("库存不可用: id={}, status={}, stock={}", inventoryId, inv.getStatus(), inv.getStock());
                return null;
            }
            return decrement(inv);
        }
    }

    @Override
    @Transactional
    public Inventory allocateByProductId(Long productId) {
        if (productId == null) {
            return null;
        }
        synchronized (InventoryServiceImpl.class) {
            Inventory inv = this.baseMapper.selectOne(new LambdaQueryWrapper<Inventory>()
                    .eq(Inventory::getProductId, productId)
                    .eq(Inventory::getStatus, Inventory.STATUS_AVAILABLE)
                    .gt(Inventory::getStock, 0)
                    .orderByAsc(Inventory::getId)
                    .last("LIMIT 1"));
            if (inv == null) {
                log.warn("商品无可用库存: productId={}", productId);
                return null;
            }
            return decrement(inv);
        }
    }

    @Override
    @Transactional
    public Inventory allocate(Long productId) {
        return allocateByProductId(productId);
    }

    @Override
    @Transactional
    public void rollback(Long inventoryId) {
        if (inventoryId == null) return;
        synchronized (InventoryServiceImpl.class) {
            Inventory inv = this.getById(inventoryId);
            if (inv == null) return;
            inv.setStock(inv.getStock() == null ? 1 : inv.getStock() + 1);
            if (inv.getUsedCount() != null && inv.getUsedCount() > 0) {
                inv.setUsedCount(inv.getUsedCount() - 1);
            }
            if (Inventory.STATUS_USED.equals(inv.getStatus())) {
                inv.setStatus(Inventory.STATUS_AVAILABLE);
            }
            this.updateById(inv);
            log.info("回补库存: id={}, stock={}", inventoryId, inv.getStock());
        }
    }

    @Override
    @Transactional
    public void markUsed(Long inventoryId, String orderId) {
        Inventory inv = this.getById(inventoryId);
        if (inv != null && !Inventory.STATUS_USED.equals(inv.getStatus())) {
            inv.setStatus(Inventory.STATUS_USED);
            inv.setUsedCount(inv.getUsedCount() == null ? 1 : inv.getUsedCount() + 1);
            inv.setStock(Math.max(0, inv.getStock() == null ? 0 : inv.getStock() - 1));
            this.updateById(inv);
        }
    }

    private Inventory decrement(Inventory inv) {
        inv.setStock(inv.getStock() - 1);
        inv.setUsedCount(inv.getUsedCount() == null ? 1 : inv.getUsedCount() + 1);
        if (inv.getStock() == 0) {
            inv.setStatus(Inventory.STATUS_USED);
        }
        this.updateById(inv);
        log.info("扣减库存: id={}, productId={}, stock={}", inv.getId(), inv.getProductId(), inv.getStock());
        return inv;
    }
}
