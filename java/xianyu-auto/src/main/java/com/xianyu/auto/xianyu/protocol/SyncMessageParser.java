package com.xianyu.auto.xianyu.protocol;

import com.xianyu.auto.common.security.MessagePackDecoder;
import com.xianyu.auto.common.util.JsonUtils;
import com.xianyu.auto.message.entity.ChatMessage;
import lombok.extern.slf4j.Slf4j;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 解析闲鱼 syncPushPackage 中的 MessagePack 消息
 */
@Slf4j
public final class SyncMessageParser {

    private static final Pattern ITEM_ID_PATTERN = Pattern.compile("itemId=(\\d+)");
    private static final Pattern ORDER_ID_PATTERN = Pattern.compile(
            "(?:orderId|order_id)=(\\d+)|order_detail\\?id=(\\d+)|[?&]id=(\\d{10,})");

    /** 仅「已付款」相关文案，用于触发 ORDER 发货 */
    private static final String[] PAID_KEYWORDS = {
            "[我已付款，等待你发货]",
            "[已付款，待发货]",
            "我已付款，等待你发货",
            "已付款，待发货",
            "等待卖家发货"
    };

    /** 未付款 / 关单等订单状态，禁止当付款事件，也不走 ALL/KEYWORD */
    private static final String[] UNPAID_OR_STATUS_KEYWORDS = {
            "等待买家付款",
            "待付款",
            "我已拍下",
            "买家拍下",
            "未付款",
            "交易关闭",
            "关闭了订单",
            "关闭订单",
            "not_pay",
            "未支付"
    };

    private static final String[] PAID_RED_REMINDERS = {
            "等待卖家发货",
            "我已付款，等待你发货",
            "已付款，待发货"
    };

    private SyncMessageParser() {}

    /**
     * 从 LWP 消息解析所有 sync 条目
     */
    public static List<ParsedChatMessage> parseSyncPush(LwpMessage lwp, String myUserId) {
        List<ParsedChatMessage> result = new ArrayList<>();
        if (lwp == null || !lwp.isSyncPushPackage()) {
            return result;
        }
        for (Map<String, Object> item : lwp.getSyncPushDataList()) {
            Object data = item.get("data");
            if (data == null) continue;
            try {
                Object decoded = MessagePackDecoder.decryptSyncData(data.toString());
                ParsedChatMessage parsed = parseDecoded(decoded, myUserId);
                if (parsed != null) {
                    result.add(parsed);
                }
            } catch (Exception e) {
                log.warn("解密 syncPush 条目失败: {}", e.getMessage());
            }
        }
        return result;
    }

    @SuppressWarnings("unchecked")
    public static ParsedChatMessage parseDecoded(Object decoded, String myUserId) {
        if (!(decoded instanceof Map)) {
            return null;
        }
        Map<String, Object> message = (Map<String, Object>) decoded;

        // 订单红点提醒：message["3"]["redReminder"]
        String redReminder = extractRedReminder(message);
        if (redReminder != null) {
            boolean paid = isPaidRedReminder(redReminder);
            String userId = extractUserIdFromKey1(message);
            return ParsedChatMessage.builder()
                    .conversationId(userId)
                    .senderId(userId)
                    .content("[" + redReminder + "]")
                    .msgType(ChatMessage.MSG_TYPE_ORDER)
                    .paidEvent(paid)
                    .systemMessage(true)
                    .redReminder(redReminder)
                    .orderId(extractOrderIdDeep(message))
                    .itemId(extractItemIdDeep(message))
                    .build();
        }

        // 正在输入
        if (isTypingStatus(message)) {
            return ParsedChatMessage.builder().typingStatus(true).build();
        }

        // 标准聊天：message["1"] 为 Map 且含 "10"
        Object node1 = message.get("1");
        if (!(node1 instanceof Map)) {
            return null;
        }
        Map<String, Object> chat = (Map<String, Object>) node1;
        Object node10 = chat.get("10");
        if (!(node10 instanceof Map)) {
            return null;
        }
        Map<String, Object> reminder = (Map<String, Object>) node10;

        String senderNick = str(reminder.get("reminderTitle"));
        String senderId = str(reminder.get("senderUserId"));
        String content = str(reminder.get("reminderContent"));
        String reminderUrl = str(reminder.get("reminderUrl"));
        String conversationId = stripGoofish(str(chat.get("2")));
        Long createTime = toLong(chat.get("5"));

        String itemId = extractQueryParam(reminderUrl, ITEM_ID_PATTERN);
        String orderId = extractOrderIdDeep(message);
        if (orderId == null) {
            orderId = extractOrderIdFromText(content);
        }
        if (itemId == null) {
            itemId = extractItemIdDeep(message);
        }

        boolean fromSelf = myUserId != null && myUserId.equals(senderId);
        boolean orderStatus = isOrderStatusContent(content);
        boolean paidEvent = !orderStatus && (isPaidContent(content) || isPaidRedReminder(redReminder));

        String msgType = ChatMessage.MSG_TYPE_TEXT;
        if (paidEvent || orderStatus || isBracketSystem(content)) {
            msgType = ChatMessage.MSG_TYPE_ORDER;
        }

        return ParsedChatMessage.builder()
                .conversationId(conversationId)
                .senderId(senderId)
                .senderNick(senderNick)
                .content(content)
                .itemId(itemId)
                .orderId(orderId)
                .msgType(msgType)
                .createTime(createTime)
                .fromSelf(fromSelf)
                .paidEvent(paidEvent)
                .systemMessage(isSystemNeedPushFalse(message) || isBracketSystem(content) || orderStatus)
                .build();
    }

    public static boolean isPaidContent(String content) {
        if (content == null || content.isEmpty()) return false;
        if (isOrderStatusContent(content)) return false;
        String trimmed = content.trim();
        for (String kw : PAID_KEYWORDS) {
            if (trimmed.contains(kw) || trimmed.equals(kw)) {
                return true;
            }
        }
        return false;
    }

    /** 未付款/关单等订单状态文案（含系统卡片） */
    public static boolean isOrderStatusContent(String content) {
        if (content == null || content.isEmpty()) return false;
        String trimmed = content.trim();
        for (String kw : UNPAID_OR_STATUS_KEYWORDS) {
            if (trimmed.contains(kw)) {
                return true;
            }
        }
        return false;
    }

    public static boolean isPaidRedReminder(String redReminder) {
        if (redReminder == null || redReminder.isEmpty()) return false;
        if (isOrderStatusContent(redReminder)) return false;
        for (String kw : PAID_RED_REMINDERS) {
            if (kw.equals(redReminder) || redReminder.contains(kw)) {
                return true;
            }
        }
        return false;
    }

    /**
     * 是否允许走 ALL/KEYWORD 自动回复。
     * 订单状态系统消息一律不走；发货仅由 paidEvent → onOrderPaid。
     */
    public static boolean isEligibleForChatAutoReply(ParsedChatMessage parsed) {
        if (parsed == null || parsed.isTypingStatus() || parsed.isFromSelf()) {
            return false;
        }
        if (parsed.isPaidEvent() || parsed.isSystemMessage()) {
            return false;
        }
        if (ChatMessage.MSG_TYPE_ORDER.equals(parsed.getMsgType())) {
            return false;
        }
        if (isOrderStatusContent(parsed.getContent()) || isBracketSystem(parsed.getContent())) {
            return false;
        }
        return StringUtilsHasText(parsed.getContent());
    }

    private static boolean StringUtilsHasText(String s) {
        return s != null && !s.trim().isEmpty();
    }

    @SuppressWarnings("unchecked")
    private static String extractRedReminder(Map<String, Object> message) {
        Object node3 = message.get("3");
        if (node3 instanceof Map) {
            Object rr = ((Map<String, Object>) node3).get("redReminder");
            return rr != null ? rr.toString() : null;
        }
        return null;
    }

    private static String extractUserIdFromKey1(Map<String, Object> message) {
        Object node1 = message.get("1");
        if (node1 instanceof String) {
            return stripGoofish(node1.toString());
        }
        return null;
    }

    @SuppressWarnings("unchecked")
    private static boolean isTypingStatus(Map<String, Object> message) {
        Object node1 = message.get("1");
        if (!(node1 instanceof List)) return false;
        List<?> list = (List<?>) node1;
        if (list.isEmpty() || !(list.get(0) instanceof Map)) return false;
        Object inner = ((Map<String, Object>) list.get(0)).get("1");
        return inner instanceof String && inner.toString().contains("@goofish");
    }

    @SuppressWarnings("unchecked")
    private static boolean isSystemNeedPushFalse(Map<String, Object> message) {
        Object node3 = message.get("3");
        if (!(node3 instanceof Map)) return false;
        Object needPush = ((Map<String, Object>) node3).get("needPush");
        return "false".equals(String.valueOf(needPush));
    }

    private static boolean isBracketSystem(String content) {
        if (content == null) return false;
        String t = content.trim();
        return t.startsWith("[") && t.endsWith("]");
    }

    private static String extractQueryParam(String url, Pattern pattern) {
        if (url == null) return null;
        Matcher m = pattern.matcher(url);
        if (m.find()) {
            return m.group(1);
        }
        return null;
    }

    private static String extractOrderIdFromText(String text) {
        if (text == null) return null;
        Matcher m = ORDER_ID_PATTERN.matcher(text);
        if (m.find()) {
            for (int i = 1; i <= m.groupCount(); i++) {
                if (m.group(i) != null) return m.group(i);
            }
        }
        return null;
    }

    /**
     * 深度遍历 Map/List，从 URL / JSON 字符串中提取 orderId
     */
    public static String extractOrderIdDeep(Object node) {
        return extractByPatternDeep(node, ORDER_ID_PATTERN);
    }

    public static String extractItemIdDeep(Object node) {
        return extractByPatternDeep(node, ITEM_ID_PATTERN);
    }

    private static String extractByPatternDeep(Object node, Pattern pattern) {
        if (node == null) return null;
        if (node instanceof String) {
            String s = (String) node;
            Matcher m = pattern.matcher(s);
            if (m.find()) {
                for (int i = 1; i <= m.groupCount(); i++) {
                    if (m.group(i) != null) return m.group(i);
                }
                return m.group();
            }
            // 尝试把字符串当 JSON 再挖
            if (s.startsWith("{") || s.startsWith("[")) {
                try {
                    Object parsed = JsonUtils.fromJson(s, Object.class);
                    return extractByPatternDeep(parsed, pattern);
                } catch (Exception ignored) {
                }
            }
            return null;
        }
        if (node instanceof Map) {
            for (Object v : ((Map<?, ?>) node).values()) {
                String found = extractByPatternDeep(v, pattern);
                if (found != null) return found;
            }
        } else if (node instanceof List) {
            for (Object v : (List<?>) node) {
                String found = extractByPatternDeep(v, pattern);
                if (found != null) return found;
            }
        }
        return null;
    }

    private static String stripGoofish(String id) {
        if (id == null) return null;
        int idx = id.indexOf('@');
        return idx > 0 ? id.substring(0, idx) : id;
    }

    private static String str(Object o) {
        return o == null ? null : o.toString();
    }

    private static Long toLong(Object o) {
        if (o == null) return null;
        if (o instanceof Number) return ((Number) o).longValue();
        try {
            return Long.parseLong(o.toString());
        } catch (Exception e) {
            return null;
        }
    }
}
