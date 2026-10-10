package com.xianyu.auto.order.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.xianyu.auto.common.api.PageResult;
import com.xianyu.auto.common.util.DateUtils;
import com.xianyu.auto.order.entity.TradeOrder;
import com.xianyu.auto.order.mapper.TradeOrderMapper;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

@Service
public class TradeOrderService extends ServiceImpl<TradeOrderMapper, TradeOrder> {

    public PageResult<TradeOrder> page(Integer pageNo, Integer pageSize,
                                       Long accountId, String status, String keyword) {
        Page<TradeOrder> page = new Page<>(pageNo == null ? 1 : pageNo, pageSize == null ? 20 : pageSize);
        LambdaQueryWrapper<TradeOrder> q = new LambdaQueryWrapper<>();
        if (accountId != null) {
            q.eq(TradeOrder::getAccountId, accountId);
        }
        if (StringUtils.hasText(status)) {
            q.eq(TradeOrder::getStatus, status);
        }
        if (StringUtils.hasText(keyword)) {
            q.and(w -> w.like(TradeOrder::getOrderId, keyword)
                    .or().like(TradeOrder::getBuyerNick, keyword)
                    .or().like(TradeOrder::getBuyerId, keyword)
                    .or().like(TradeOrder::getItemId, keyword)
                    .or().like(TradeOrder::getItemTitle, keyword));
        }
        q.orderByDesc(TradeOrder::getUpdatedAt);
        Page<TradeOrder> result = page(page, q);
        return new PageResult<>(result.getRecords(), result.getTotal());
    }

    /**
     * 按订单事件 upsert
     */
    public TradeOrder upsertFromEvent(Long accountId, String orderId, String itemId, String itemTitle,
                                      String buyerId, String buyerNick, String conversationId,
                                      String status, String rawJson) {
        if (!StringUtils.hasText(orderId) || accountId == null) {
            return null;
        }
        TradeOrder existing = getOne(new LambdaQueryWrapper<TradeOrder>()
                .eq(TradeOrder::getAccountId, accountId)
                .eq(TradeOrder::getOrderId, orderId)
                .last("LIMIT 1"));
        long now = DateUtils.nowMillis();
        if (existing == null) {
            TradeOrder o = new TradeOrder();
            o.setAccountId(accountId);
            o.setOrderId(orderId);
            o.setItemId(itemId);
            o.setItemTitle(itemTitle);
            o.setBuyerId(buyerId);
            o.setBuyerNick(buyerNick);
            o.setConversationId(conversationId);
            o.setStatus(status != null ? status : TradeOrder.STATUS_WAIT_PAY);
            o.setRawJson(rawJson);
            o.setCreatedAt(now);
            o.setUpdatedAt(now);
            if (TradeOrder.STATUS_WAIT_SHIP.equals(o.getStatus())) {
                o.setPaidAt(now);
            }
            save(o);
            return o;
        }
        if (StringUtils.hasText(itemId)) existing.setItemId(itemId);
        if (StringUtils.hasText(itemTitle)) existing.setItemTitle(itemTitle);
        if (StringUtils.hasText(buyerId)) existing.setBuyerId(buyerId);
        if (StringUtils.hasText(buyerNick)) existing.setBuyerNick(buyerNick);
        if (StringUtils.hasText(conversationId)) existing.setConversationId(conversationId);
        if (StringUtils.hasText(status)) {
            String prev = existing.getStatus();
            existing.setStatus(status);
            if (TradeOrder.STATUS_WAIT_SHIP.equals(status) && existing.getPaidAt() == null) {
                existing.setPaidAt(now);
            }
            if (TradeOrder.STATUS_SHIPPED.equals(status) && existing.getShippedAt() == null) {
                existing.setShippedAt(now);
            }
            // 已关闭/成功不回退到待付款
            if (TradeOrder.STATUS_CLOSED.equals(prev) || TradeOrder.STATUS_SUCCESS.equals(prev)) {
                if (TradeOrder.STATUS_WAIT_PAY.equals(status)) {
                    existing.setStatus(prev);
                }
            }
        }
        if (StringUtils.hasText(rawJson)) existing.setRawJson(rawJson);
        existing.setUpdatedAt(now);
        updateById(existing);
        return existing;
    }

    public void markConsign(Long accountId, String orderId, String consignStatus) {
        if (!StringUtils.hasText(orderId)) return;
        TradeOrder o = getOne(new LambdaQueryWrapper<TradeOrder>()
                .eq(TradeOrder::getAccountId, accountId)
                .eq(TradeOrder::getOrderId, orderId)
                .last("LIMIT 1"));
        if (o == null) return;
        o.setConsignStatus(consignStatus);
        if ("SUCCESS".equals(consignStatus)) {
            o.setStatus(TradeOrder.STATUS_SHIPPED);
            o.setShippedAt(DateUtils.nowMillis());
        }
        o.setUpdatedAt(DateUtils.nowMillis());
        updateById(o);
    }
}
