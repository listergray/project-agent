package com.xianyu.auto.xianyu.handler;

import com.xianyu.auto.common.security.MessagePackDecoder;
import com.xianyu.auto.common.util.JsonUtils;
import com.xianyu.auto.delivery.engine.AutoDeliveryEngine;
import com.xianyu.auto.message.entity.ChatMessage;
import com.xianyu.auto.message.service.ChatMessageService;
import com.xianyu.auto.reply.engine.AutoReplyEngine;
import com.xianyu.auto.xianyu.constant.XianyuApiConst;
import com.xianyu.auto.xianyu.protocol.LwpMessage;
import com.xianyu.auto.xianyu.protocol.SyncMessageParser;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

import java.util.Map;

/**
 * 兼容旧路径的聊天消息处理器（/p/Message、/r/MessageSend）。
 * 主流消息走 {@link SyncPushMessageHandler}。
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class ChatMessageHandler implements MessageHandler {

    private final ChatMessageService chatMessageService;
    private final AutoDeliveryEngine autoDeliveryEngine;
    private final AutoReplyEngine autoReplyEngine;

    @Override
    public boolean supports(String lwp) {
        if (lwp == null) return false;
        // sync 由 SyncPushMessageHandler 处理
        if (lwp.contains("sync") || lwp.startsWith("/s/")) {
            return false;
        }
        return lwp.startsWith(XianyuApiConst.LWP_PUSH_PREFIX)
                || lwp.contains("Message");
    }

    @Override
    public void handle(Long accountId, LwpMessage message) {
        try {
            // 若意外带 syncPush，转给解析器逻辑
            if (message.isSyncPushPackage()) {
                return;
            }

            String customBase64 = message.getCustomField();
            if (!StringUtils.hasText(customBase64)) {
                log.debug("消息无 custom 字段: accountId={}, lwp={}", accountId, message.getLwp());
                return;
            }

            Map<String, Object> decoded;
            try {
                Object obj = MessagePackDecoder.decryptSyncData(customBase64);
                if (obj instanceof Map) {
                    @SuppressWarnings("unchecked")
                    Map<String, Object> map = (Map<String, Object>) obj;
                    decoded = map;
                } else {
                    decoded = MessagePackDecoder.decode(customBase64);
                }
            } catch (Exception e) {
                decoded = MessagePackDecoder.decode(customBase64);
            }

            String conversationId = getStr(decoded, "conversationId", "cid", "convId");
            String senderId = getStr(decoded, "senderId", "fromUserId", "fromId");
            String senderNick = getStr(decoded, "senderNick", "fromUserNick", "nick");
            String content = getStr(decoded, "content", "text", "message");
            String itemId = getStr(decoded, "itemId", "subjectId");
            String msgType = getStr(decoded, "msgType", "messageType", "type");

            // 嵌套 text.text
            if (!StringUtils.hasText(content)) {
                Object text = decoded.get("text");
                if (text instanceof Map) {
                    Object t = ((Map<?, ?>) text).get("text");
                    if (t != null) content = t.toString();
                }
            }

            String sender = ChatMessage.SENDER_BUYER;
            if (message.getLwp() != null && message.getLwp().startsWith(XianyuApiConst.LWP_REQUEST_PREFIX)) {
                sender = ChatMessage.SENDER_SELLER;
            }

            if (!StringUtils.hasText(conversationId) && StringUtils.hasText(senderId)) {
                conversationId = senderId;
            }
            if (!StringUtils.hasText(conversationId)) {
                log.warn("无法解析消息 conversationId: {}", decoded);
                return;
            }

            conversationId = stripSuffix(conversationId);
            senderId = stripSuffix(senderId);

            chatMessageService.saveReceivedMessage(
                    accountId, conversationId, sender, senderId, senderNick,
                    itemId, msgType, content, JsonUtils.toJson(message));

            log.info("保存消息(legacy): accountId={}, conv={}, sender={}, content={}",
                    accountId, conversationId, sender, truncate(content, 50));

            if (ChatMessage.SENDER_BUYER.equals(sender)) {
                if (SyncMessageParser.isPaidContent(content)) {
                    String orderId = SyncMessageParser.extractOrderIdDeep(decoded);
                    autoDeliveryEngine.onOrderPaid(accountId, conversationId, senderId,
                            senderNick, itemId, orderId);
                } else if (!SyncMessageParser.isOrderStatusContent(content)
                        && !(content != null && content.trim().startsWith("[") && content.trim().endsWith("]"))) {
                    // 未付款等订单系统文案不走 ALL/KEYWORD / 自动回复
                    boolean deliveryHandled = autoDeliveryEngine.onMessageReceived(
                            accountId, conversationId, senderId, senderNick, content, itemId);
                    if (!deliveryHandled) {
                        autoReplyEngine.onBuyerMessage(
                                accountId, conversationId, senderId, senderNick, content, itemId);
                    }
                }
            }
        } catch (Exception e) {
            log.error("处理聊天消息失败: accountId={}, lwp={}, error={}",
                    accountId, message.getLwp(), e.getMessage(), e);
        }
    }

    private String getStr(Map<String, Object> map, String... keys) {
        if (map == null) return null;
        for (String key : keys) {
            Object v = map.get(key);
            if (v != null && !v.toString().isEmpty()) {
                return v.toString();
            }
        }
        return null;
    }

    private String stripSuffix(String id) {
        if (id == null) return null;
        int idx = id.indexOf('@');
        return idx > 0 ? id.substring(0, idx) : id;
    }

    private String truncate(String s, int maxLen) {
        if (s == null) return null;
        return s.length() > maxLen ? s.substring(0, maxLen) + "..." : s;
    }
}
