package com.xianyu.auto.xianyu.handler;

import com.xianyu.auto.account.entity.Account;
import com.xianyu.auto.account.service.AccountService;
import com.xianyu.auto.common.util.JsonUtils;
import com.xianyu.auto.delivery.engine.AutoDeliveryEngine;
import com.xianyu.auto.message.entity.ChatMessage;
import com.xianyu.auto.message.service.ChatMessageService;
import com.xianyu.auto.order.entity.TradeOrder;
import com.xianyu.auto.order.service.TradeOrderService;
import com.xianyu.auto.reply.engine.AutoReplyEngine;
import com.xianyu.auto.xianyu.auth.CookieManager;
import com.xianyu.auto.xianyu.constant.XianyuApiConst;
import com.xianyu.auto.xianyu.protocol.LwpMessage;
import com.xianyu.auto.xianyu.protocol.ParsedChatMessage;
import com.xianyu.auto.xianyu.protocol.SyncMessageParser;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

import java.util.List;

/**
 * 处理 syncPushPackage 推送（真实聊天/订单消息入口）
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class SyncPushMessageHandler implements MessageHandler {

    /** 丢弃超过 5 分钟的消息 */
    private static final long MESSAGE_EXPIRE_MS = 5 * 60 * 1000L;

    private final ChatMessageService chatMessageService;
    private final AutoDeliveryEngine autoDeliveryEngine;
    private final AutoReplyEngine autoReplyEngine;
    private final AccountService accountService;
    private final CookieManager cookieManager;
    private final TradeOrderService tradeOrderService;

    @Override
    public boolean supports(String lwp) {
        if (lwp == null) return false;
        return lwp.contains("sync") || lwp.startsWith("/s/")
                || XianyuApiConst.LWP_SYNC.equals(lwp);
    }

    @Override
    public void handle(Long accountId, LwpMessage message) {
        if (message == null || !message.isSyncPushPackage()) {
            return;
        }
        String myUserId = resolveMyUserId(accountId);
        List<ParsedChatMessage> parsedList = SyncMessageParser.parseSyncPush(message, myUserId);
        for (ParsedChatMessage parsed : parsedList) {
            try {
                processOne(accountId, myUserId, parsed, message);
            } catch (Exception e) {
                log.error("处理 sync 消息失败: accountId={}, error={}", accountId, e.getMessage(), e);
            }
        }
    }

    private void processOne(Long accountId, String myUserId, ParsedChatMessage parsed, LwpMessage raw) {
        if (parsed == null || parsed.isTypingStatus()) {
            return;
        }

        if (parsed.getCreateTime() != null
                && System.currentTimeMillis() - parsed.getCreateTime() > MESSAGE_EXPIRE_MS) {
            log.debug("过期消息丢弃: accountId={}, createTime={}", accountId, parsed.getCreateTime());
            return;
        }

        String conversationId = parsed.getConversationId();
        if (!StringUtils.hasText(conversationId) && StringUtils.hasText(parsed.getSenderId())) {
            conversationId = parsed.getSenderId();
        }
        if (!StringUtils.hasText(conversationId)) {
            log.debug("无法解析 conversationId，跳过");
            return;
        }

        String sender = parsed.isFromSelf() ? ChatMessage.SENDER_SELLER : ChatMessage.SENDER_BUYER;
        if (parsed.isSystemMessage() || parsed.isPaidEvent()
                || SyncMessageParser.isOrderStatusContent(parsed.getContent())) {
            sender = ChatMessage.SENDER_SYSTEM;
        }

        String content = parsed.getContent();
        if (!StringUtils.hasText(content) && StringUtils.hasText(parsed.getRedReminder())) {
            content = "[" + parsed.getRedReminder() + "]";
        }

        chatMessageService.saveReceivedMessage(
                accountId, conversationId, sender,
                parsed.getSenderId(), parsed.getSenderNick(),
                parsed.getItemId(), parsed.getMsgType(), content,
                JsonUtils.toJson(raw));

        log.info("保存 sync 消息: accountId={}, conv={}, sender={}, paid={}, content={}",
                accountId, conversationId, sender, parsed.isPaidEvent(), truncate(content, 50));

        // 自己发的消息不触发发货
        if (parsed.isFromSelf() || (myUserId != null && myUserId.equals(parsed.getSenderId()))) {
            return;
        }

        String buyerId = parsed.getSenderId();
        if (!StringUtils.hasText(buyerId)) {
            buyerId = conversationId;
        }

        // 订单状态落库
        if (StringUtils.hasText(parsed.getOrderId())
                || ChatMessage.MSG_TYPE_ORDER.equals(parsed.getMsgType())
                || SyncMessageParser.isOrderStatusContent(content)
                || parsed.isPaidEvent()) {
            String orderStatus = resolveOrderStatus(parsed, content);
            try {
                tradeOrderService.upsertFromEvent(
                        accountId, parsed.getOrderId(), parsed.getItemId(), null,
                        buyerId, parsed.getSenderNick(), conversationId,
                        orderStatus, truncate(content, 500));
            } catch (Exception e) {
                log.warn("订单落库失败: {}", e.getMessage());
            }
        }

        // ORDER / 商品自动发货：仅支付完成
        if (parsed.isPaidEvent() || SyncMessageParser.isPaidContent(content)) {
            autoDeliveryEngine.onOrderPaid(
                    accountId, conversationId, buyerId, parsed.getSenderNick(),
                    parsed.getItemId(), parsed.getOrderId());
            return;
        }

        // 未付款/关单等订单状态：不触发 ALL/KEYWORD
        if (!SyncMessageParser.isEligibleForChatAutoReply(parsed)) {
            log.debug("跳过自动回复(非付款订单状态或系统消息): accountId={}, content={}",
                    accountId, truncate(content, 40));
            return;
        }

        boolean deliveryHandled = autoDeliveryEngine.onMessageReceived(
                accountId, conversationId, buyerId, parsed.getSenderNick(),
                content, parsed.getItemId());
        if (!deliveryHandled) {
            autoReplyEngine.onBuyerMessage(
                    accountId, conversationId, buyerId, parsed.getSenderNick(),
                    content, parsed.getItemId());
        }
    }

    private String resolveMyUserId(Long accountId) {
        Account account = accountService.getById(accountId);
        if (account != null && StringUtils.hasText(account.getUserId())) {
            return account.getUserId();
        }
        return cookieManager.getUnb(accountId);
    }

    private String resolveOrderStatus(ParsedChatMessage parsed, String content) {
        if (parsed.isPaidEvent() || SyncMessageParser.isPaidContent(content)) {
            return TradeOrder.STATUS_WAIT_SHIP;
        }
        String c = content == null ? "" : content;
        if (c.contains("交易关闭") || c.contains("关闭了订单") || c.contains("未付款")) {
            return TradeOrder.STATUS_CLOSED;
        }
        if (c.contains("拍下") || c.contains("待付款") || c.contains("等待买家付款")) {
            return TradeOrder.STATUS_WAIT_PAY;
        }
        if (c.contains("已发货") || c.contains("待收货")) {
            return TradeOrder.STATUS_SHIPPED;
        }
        return TradeOrder.STATUS_WAIT_PAY;
    }

    private String truncate(String s, int maxLen) {
        if (s == null) return null;
        return s.length() > maxLen ? s.substring(0, maxLen) + "..." : s;
    }
}
