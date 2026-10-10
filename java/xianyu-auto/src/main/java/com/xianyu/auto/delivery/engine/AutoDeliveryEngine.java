package com.xianyu.auto.delivery.engine;

import com.xianyu.auto.account.entity.Account;
import com.xianyu.auto.account.service.AccountService;
import com.xianyu.auto.common.util.DateUtils;
import com.xianyu.auto.delivery.entity.DeliveryLog;
import com.xianyu.auto.delivery.entity.DeliveryRule;
import com.xianyu.auto.delivery.service.DeliveryLogService;
import com.xianyu.auto.delivery.service.DeliveryRuleService;
import com.xianyu.auto.inventory.entity.Inventory;
import com.xianyu.auto.inventory.service.InventoryService;
import com.xianyu.auto.message.service.ChatMessageService;
import com.xianyu.auto.order.service.TradeOrderService;
import com.xianyu.auto.product.entity.Product;
import com.xianyu.auto.product.service.ProductService;
import com.xianyu.auto.xianyu.auth.CookieManager;
import com.xianyu.auto.xianyu.client.XianyuApiClient;
import com.xianyu.auto.xianyu.client.XianyuWsManager;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.ApplicationContext;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@Slf4j
@Component
@RequiredArgsConstructor
public class AutoDeliveryEngine {

    private final DeliveryRuleService deliveryRuleService;
    private final InventoryService inventoryService;
    private final DeliveryLogService deliveryLogService;
    private final AccountService accountService;
    private final ChatMessageService chatMessageService;
    private final ProductService productService;
    private final CookieManager cookieManager;
    private final XianyuApiClient xianyuApiClient;
    private final TradeOrderService tradeOrderService;
    private final ApplicationContext applicationContext;

    private final ExecutorService deliveryExecutor = Executors.newCachedThreadPool(r -> {
        Thread t = new Thread(r, "auto-delivery");
        t.setDaemon(true);
        return t;
    });

    private XianyuWsManager getWsManager() {
        return applicationContext.getBean(XianyuWsManager.class);
    }

    /**
     * 买家付款事件（主路径）
     */
    public void onOrderPaid(Long accountId, String conversationId, String buyerId,
                            String buyerNick, String itemId, String orderId) {
        log.info("订单付款事件: account={}, conv={}, buyer={}, item={}, order={}",
                accountId, conversationId, buyerId, itemId, orderId);

        if (StringUtils.hasText(orderId)
                && deliveryLogService.existsSuccessByOrderId(accountId, orderId)) {
            log.info("订单已发货，跳过: accountId={}, orderId={}", accountId, orderId);
            return;
        }

        List<DeliveryRule> matchedRules = deliveryRuleService.matchRules(
                accountId, "[我已付款，等待你发货]", itemId, true);

        if (!matchedRules.isEmpty()) {
            Account account = accountService.getById(accountId);
            // 只执行优先级最高的一条
            DeliveryRule rule = matchedRules.get(0);
            deliveryExecutor.execute(() -> {
                try {
                    processRule(account, rule, conversationId, buyerId, buyerNick, itemId, orderId, true);
                } catch (Exception e) {
                    log.error("付款发货失败 rule={}: {}", rule.getName(), e.getMessage(), e);
                }
            });
            return;
        }

        // 商品级自动发货（仅付款事件）
        if (StringUtils.hasText(itemId)) {
            deliveryExecutor.execute(() ->
                    processProductAutoDelivery(accountId, conversationId, buyerId, buyerNick, itemId, orderId, true));
        } else {
            log.debug("付款事件无匹配规则且无 itemId: accountId={}", accountId);
        }
    }

    /**
     * 普通买家消息（KEYWORD / ALL）
     *
     * @return true=已命中发货规则并提交执行（调用方应跳过自动回复，避免双发）
     */
    public boolean onMessageReceived(Long accountId, String conversationId, String senderId,
                                     String senderNick, String content, String itemId) {
        log.debug("Received message: account={}, conversation={}, content={}, itemId={}",
                accountId, conversationId, content, itemId);

        List<DeliveryRule> matchedRules = deliveryRuleService.matchRules(
                accountId, content, itemId, false);
        if (matchedRules.isEmpty()) {
            return false;
        }

        Account account = accountService.getById(accountId);
        DeliveryRule rule = matchedRules.get(0);
        deliveryExecutor.execute(() -> {
            try {
                processRule(account, rule, conversationId, senderId, senderNick, itemId, null, false);
            } catch (Exception e) {
                log.error("消息触发发货失败 rule={}: {}", rule.getName(), e.getMessage(), e);
            }
        });
        return true;
    }

    /**
     * 手动重发：不重复扣库存，复用原内容
     */
    public boolean resend(Long logId) {
        DeliveryLog old = deliveryLogService.getById(logId);
        if (old == null) {
            throw new IllegalArgumentException("发货记录不存在");
        }
        Account account = accountService.getById(old.getAccountId());
        if (account == null) {
            throw new IllegalArgumentException("账号不存在");
        }
        String buyerId = old.getBuyerId();
        if (!StringUtils.hasText(buyerId)) {
            buyerId = old.getConversationId();
        }
        boolean sent = getWsManager().sendChatMessage(
                account.getId(), old.getConversationId(), buyerId, old.getDeliveryContent());
        if (sent) {
            chatMessageService.saveSentMessage(account.getId(), old.getConversationId(),
                    old.getDeliveryContent(), account.getNickname(), old.getItemId());
        }

        DeliveryLog logEntity = new DeliveryLog();
        logEntity.setAccountId(account.getId());
        logEntity.setAccountNickname(account.getNickname());
        logEntity.setRuleId(old.getRuleId());
        logEntity.setRuleName((old.getRuleName() == null ? "手动重发" : old.getRuleName()) + "(重发)");
        logEntity.setConversationId(old.getConversationId());
        logEntity.setBuyerId(old.getBuyerId());
        logEntity.setBuyerNick(old.getBuyerNick());
        logEntity.setItemId(old.getItemId());
        logEntity.setItemName(old.getItemName());
        logEntity.setOrderId(old.getOrderId());
        logEntity.setDeliveryContent(old.getDeliveryContent());
        logEntity.setInventoryCode(old.getInventoryCode());
        logEntity.setInventoryId(old.getInventoryId());
        logEntity.setConsignStatus(DeliveryLog.CONSIGN_SKIPPED);
        logEntity.setStatus(sent ? DeliveryLog.STATUS_SUCCESS : DeliveryLog.STATUS_FAILED);
        logEntity.setErrorMsg(sent ? null : "重发失败：账号未连接或发送失败");
        long now = DateUtils.nowMillis();
        logEntity.setCreatedAt(now);
        logEntity.setUpdatedAt(now);
        deliveryLogService.save(logEntity);
        return sent;
    }

    private void processRule(Account account, DeliveryRule rule, String conversationId,
                             String buyerId, String buyerNick, String itemId, String orderId,
                             boolean paidEvent) {
        if (account == null) return;

        if (StringUtils.hasText(orderId)
                && deliveryLogService.existsSuccessByOrderId(account.getId(), orderId)) {
            log.info("订单已发货(规则内再检查): orderId={}", orderId);
            return;
        }

        sleepDelay(rule.delaySecondsOrZero());

        Inventory allocatedInventory = null;
        String deliveryContent = rule.getDeliveryContent() == null ? "" : rule.getDeliveryContent();

        if (rule.getInventoryId() != null) {
            allocatedInventory = inventoryService.allocateById(rule.getInventoryId());
            if (allocatedInventory == null) {
                log.warn("库存不足 rule={}", rule.getName());
                saveLog(account, rule, conversationId, buyerId, buyerNick, itemId, orderId,
                        deliveryContent, null, null,
                        DeliveryLog.STATUS_FAILED, DeliveryLog.CONSIGN_SKIPPED, "库存不足");
                return;
            }
            deliveryContent = replaceInventoryPlaceholder(deliveryContent, allocatedInventory);
        }

        boolean sent = false;
        String errorMsg = null;
        String consignStatus = DeliveryLog.CONSIGN_SKIPPED;
        try {
            String toBuyer = StringUtils.hasText(buyerId) ? buyerId : conversationId;
            sent = getWsManager().sendChatMessage(account.getId(), conversationId, toBuyer, deliveryContent);
            if (!sent) {
                errorMsg = "发送失败：账号未连接或协议错误";
            } else {
                chatMessageService.saveSentMessage(account.getId(), conversationId, deliveryContent,
                        account.getNickname(), itemId);
                log.info("自动发货成功: rule={}, account={}, conv={}, order={}",
                        rule.getName(), account.getNickname(), conversationId, orderId);

                if (paidEvent && rule.isAutoConfirmEnabled() && StringUtils.hasText(orderId)) {
                    ConsignOutcome consign = doConsign(account.getId(), orderId);
                    consignStatus = consign.status();
                    if (!DeliveryLog.CONSIGN_SUCCESS.equals(consignStatus)
                            && StringUtils.hasText(consign.message())) {
                        errorMsg = "确认发货失败: " + consign.message();
                    }
                }
            }
        } catch (Exception e) {
            errorMsg = e.getMessage();
            log.error("发送自动发货消息失败: {}", errorMsg, e);
        }

        if (!sent && allocatedInventory != null) {
            inventoryService.rollback(allocatedInventory.getId());
        }

        saveLog(account, rule, conversationId, buyerId, buyerNick, itemId, orderId,
                deliveryContent,
                allocatedInventory != null ? allocatedInventory.getCode() : null,
                allocatedInventory != null ? allocatedInventory.getId() : null,
                sent ? DeliveryLog.STATUS_SUCCESS : DeliveryLog.STATUS_FAILED,
                consignStatus, errorMsg);
    }

    private void processProductAutoDelivery(Long accountId, String conversationId, String buyerId,
                                            String buyerNick, String itemId, String orderId,
                                            boolean paidEvent) {
        try {
            if (!paidEvent) {
                return;
            }
            Product product = productService.getByXianyuItemId(itemId);
            if (product == null || product.getAutoDelivery() == null || product.getAutoDelivery() != 1) {
                return;
            }
            if (!hasText(product.getDeliveryContent())) {
                return;
            }
            if (StringUtils.hasText(orderId)
                    && deliveryLogService.existsSuccessByOrderId(accountId, orderId)) {
                return;
            }

            Account account = accountService.getById(accountId);
            String deliveryContent = product.getDeliveryContent();
            Inventory allocatedInventory = null;

            if (product.getDefaultInventoryId() != null) {
                allocatedInventory = inventoryService.allocateById(product.getDefaultInventoryId());
                if (allocatedInventory == null) {
                    saveLog(account, null, conversationId, buyerId, buyerNick, itemId, orderId,
                            deliveryContent, null, null,
                            DeliveryLog.STATUS_FAILED, DeliveryLog.CONSIGN_SKIPPED, "库存不足");
                    return;
                }
                deliveryContent = replaceInventoryPlaceholder(deliveryContent, allocatedInventory);
            }

            boolean sent = false;
            String errorMsg = null;
            String consignStatus = DeliveryLog.CONSIGN_SKIPPED;
            try {
                String toBuyer = StringUtils.hasText(buyerId) ? buyerId : conversationId;
                sent = getWsManager().sendChatMessage(account.getId(), conversationId, toBuyer, deliveryContent);
                if (sent) {
                    chatMessageService.saveSentMessage(account.getId(), conversationId, deliveryContent,
                            account.getNickname(), itemId);
                    if (StringUtils.hasText(orderId)) {
                        ConsignOutcome consign = doConsign(accountId, orderId);
                        consignStatus = consign.status();
                        if (!DeliveryLog.CONSIGN_SUCCESS.equals(consignStatus)
                                && StringUtils.hasText(consign.message())) {
                            errorMsg = "确认发货失败: " + consign.message();
                        }
                    }
                } else {
                    errorMsg = "发送失败：账号未连接或协议错误";
                }
            } catch (Exception e) {
                errorMsg = e.getMessage();
            }

            if (!sent && allocatedInventory != null) {
                inventoryService.rollback(allocatedInventory.getId());
            }

            saveLog(account, null, conversationId, buyerId, buyerNick, itemId, orderId,
                    deliveryContent,
                    allocatedInventory != null ? allocatedInventory.getCode() : null,
                    allocatedInventory != null ? allocatedInventory.getId() : null,
                    sent ? DeliveryLog.STATUS_SUCCESS : DeliveryLog.STATUS_FAILED,
                    consignStatus, errorMsg);
        } catch (Exception e) {
            log.error("商品自动发货失败: {}", e.getMessage(), e);
        }
    }

    private record ConsignOutcome(String status, String message) {}

    private ConsignOutcome doConsign(Long accountId, String orderId) {
        try {
            String cookie = cookieManager.getCookie(accountId);
            XianyuApiClient.ConsignResult result = xianyuApiClient.tradeConsignmentDetail(cookie, orderId);
            String status = result.success() ? DeliveryLog.CONSIGN_SUCCESS : DeliveryLog.CONSIGN_FAILED;
            try {
                tradeOrderService.markConsign(accountId, orderId, status);
            } catch (Exception ignored) {
            }
            return new ConsignOutcome(status, result.message());
        } catch (Exception e) {
            log.warn("确认发货异常 orderId={}: {}", orderId, e.getMessage());
            return new ConsignOutcome(DeliveryLog.CONSIGN_FAILED, e.getMessage());
        }
    }

    private void sleepDelay(int seconds) {
        if (seconds <= 0) return;
        try {
            Thread.sleep(seconds * 1000L);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    private String replaceInventoryPlaceholder(String template, Inventory inv) {
        String inventoryText = inv.getContent();
        if (!hasText(inventoryText)) {
            inventoryText = inv.getCode();
        }
        if (inventoryText == null) inventoryText = "";
        return template
                .replace("${inventory}", inventoryText)
                .replace("{{inventory}}", inventoryText);
    }

    private void saveLog(Account account, DeliveryRule rule, String conversationId,
                         String buyerId, String buyerNick, String itemId, String orderId,
                         String deliveryContent, String inventoryCode, Long inventoryId,
                         String status, String consignStatus, String errorMsg) {
        DeliveryLog logEntity = new DeliveryLog();
        logEntity.setAccountId(account.getId());
        logEntity.setAccountNickname(account.getNickname());
        logEntity.setRuleId(rule != null ? rule.getId() : null);
        logEntity.setRuleName(rule != null ? rule.getName() : "商品自动发货");
        logEntity.setConversationId(conversationId);
        logEntity.setBuyerId(buyerId);
        logEntity.setBuyerNick(buyerNick);
        logEntity.setItemId(itemId);
        logEntity.setOrderId(orderId);
        logEntity.setDeliveryContent(deliveryContent);
        logEntity.setInventoryCode(inventoryCode);
        logEntity.setInventoryId(inventoryId);
        logEntity.setConsignStatus(consignStatus);
        logEntity.setStatus(status);
        logEntity.setErrorMsg(errorMsg);
        long now = DateUtils.nowMillis();
        logEntity.setCreatedAt(now);
        logEntity.setUpdatedAt(now);

        if (StringUtils.hasText(itemId)) {
            Product p = productService.getByXianyuItemId(itemId);
            if (p != null) {
                logEntity.setItemName(p.getName());
            }
        }
        deliveryLogService.save(logEntity);
    }

    private boolean hasText(String str) {
        return str != null && !str.trim().isEmpty();
    }
}
