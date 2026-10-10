package com.xianyu.auto.order.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.xianyu.auto.common.exception.BusinessException;
import com.xianyu.auto.order.entity.TradeOrder;
import com.xianyu.auto.xianyu.auth.CookieManager;
import com.xianyu.auto.xianyu.client.XianyuApiClient;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 从闲鱼卖家已售订单接口补全/对账 t_order
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class TradeOrderSyncService {

    private final TradeOrderService tradeOrderService;
    private final CookieManager cookieManager;
    private final XianyuApiClient apiClient;

    public Map<String, Object> syncFromXianyu(Long accountId) {
        if (accountId == null) {
            throw new BusinessException("accountId 不能为空");
        }
        String cookie = cookieManager.getCookie(accountId);
        if (!StringUtils.hasText(cookie)) {
            throw new BusinessException("账号 Cookie 不可用，请重新录入");
        }

        int page = 1;
        int upserted = 0;
        int errors = 0;
        while (page <= 20) {
            JsonNode resp;
            try {
                resp = apiClient.querySoldOrders(cookie, page, 20);
            } catch (Exception e) {
                log.warn("同步订单列表失败 page={}: {}", page, e.getMessage());
                errors++;
                break;
            }
            if (!apiClient.isApiSuccess(resp)) {
                throw new BusinessException("同步订单失败: " + resp.path("ret"));
            }
            List<JsonNode> orders = extractOrderNodes(resp);
            if (orders.isEmpty()) {
                break;
            }
            for (JsonNode node : orders) {
                try {
                    upsertFromSoldNode(accountId, node);
                    upserted++;
                    Thread.sleep(150 + (long) (Math.random() * 350));
                } catch (Exception e) {
                    errors++;
                    log.warn("同步单笔订单失败: {}", e.getMessage());
                }
            }
            if (orders.size() < 20) {
                break;
            }
            page++;
            try {
                Thread.sleep(400 + (long) (Math.random() * 600));
            } catch (InterruptedException ie) {
                Thread.currentThread().interrupt();
                break;
            }
        }
        Map<String, Object> result = new HashMap<>();
        result.put("upserted", upserted);
        result.put("errors", errors);
        result.put("pages", page);
        return result;
    }

    private void upsertFromSoldNode(Long accountId, JsonNode node) {
        String orderId = text(node, "orderId", "bizOrderId", "id");
        if (!StringUtils.hasText(orderId)) {
            return;
        }
        String itemId = text(node, "itemId", "auctionId");
        String itemTitle = text(node, "itemTitle", "title", "auctionTitle");
        String buyerId = text(node, "buyerId", "buyerUserId");
        String buyerNick = text(node, "buyerNick", "buyerNickName");
        String status = mapSoldStatus(node);
        String raw = node.toString();
        TradeOrder o = tradeOrderService.upsertFromEvent(
                accountId, orderId, itemId, itemTitle, buyerId, buyerNick, null, status, raw);
        if (o != null) {
            BigDecimal amount = decimal(node, "payAmount", "actualFee", "totalFee", "price");
            if (amount != null) {
                o.setPayAmount(amount);
                tradeOrderService.updateById(o);
            }
        }
    }

    private String mapSoldStatus(JsonNode node) {
        String s = text(node, "status", "orderStatus", "tradeStatus");
        if (!StringUtils.hasText(s)) {
            return TradeOrder.STATUS_WAIT_SHIP;
        }
        String u = s.toUpperCase();
        if (u.contains("WAIT_BUYER_PAY") || u.contains("未付款") || "1".equals(s)) {
            return TradeOrder.STATUS_WAIT_PAY;
        }
        if (u.contains("WAIT_SELLER_SEND") || u.contains("WAIT_SHIP") || u.contains("待发货") || "2".equals(s)) {
            return TradeOrder.STATUS_WAIT_SHIP;
        }
        if (u.contains("WAIT_BUYER_CONFIRM") || u.contains("SHIPPED") || u.contains("已发货") || "3".equals(s)) {
            return TradeOrder.STATUS_SHIPPED;
        }
        if (u.contains("SUCCESS") || u.contains("TRADE_FINISHED") || u.contains("完成") || "4".equals(s)) {
            return TradeOrder.STATUS_SUCCESS;
        }
        if (u.contains("CLOSED") || u.contains("关闭") || u.contains("CANCEL")) {
            return TradeOrder.STATUS_CLOSED;
        }
        return TradeOrder.STATUS_WAIT_SHIP;
    }

    private List<JsonNode> extractOrderNodes(JsonNode resp) {
        List<JsonNode> list = new ArrayList<>();
        JsonNode data = resp.path("data");
        collectArray(data.path("cardList"), list);
        collectArray(data.path("items"), list);
        collectArray(data.path("list"), list);
        collectArray(data.path("orders"), list);
        collectArray(data.path("result"), list);
        if (list.isEmpty() && data.isArray()) {
            data.forEach(list::add);
        }
        // 嵌套 items
        if (list.isEmpty()) {
            data.fields().forEachRemaining(e -> {
                if (e.getValue().isArray() && e.getValue().size() > 0
                        && (e.getValue().get(0).has("orderId") || e.getValue().get(0).has("bizOrderId"))) {
                    e.getValue().forEach(list::add);
                }
            });
        }
        return list;
    }

    private void collectArray(JsonNode arr, List<JsonNode> out) {
        if (arr != null && arr.isArray()) {
            arr.forEach(out::add);
        }
    }

    private String text(JsonNode node, String... keys) {
        for (String k : keys) {
            JsonNode n = node.get(k);
            if (n != null && !n.isNull() && StringUtils.hasText(n.asText())) {
                return n.asText();
            }
        }
        return null;
    }

    private BigDecimal decimal(JsonNode node, String... keys) {
        for (String k : keys) {
            JsonNode n = node.get(k);
            if (n == null || n.isNull()) continue;
            try {
                if (n.isNumber()) return n.decimalValue();
                String t = n.asText();
                if (StringUtils.hasText(t)) return new BigDecimal(t.trim());
            } catch (Exception ignored) {
            }
        }
        return null;
    }
}
