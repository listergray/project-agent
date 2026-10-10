package com.xianyu.auto.xianyu.protocol;

import com.xianyu.auto.message.entity.ChatMessage;
import org.junit.jupiter.api.Test;

import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

class SyncMessageParserTest {

    @Test
    void testIsPaidContent() {
        assertTrue(SyncMessageParser.isPaidContent("[我已付款，等待你发货]"));
        assertTrue(SyncMessageParser.isPaidContent("等待卖家发货"));
        assertFalse(SyncMessageParser.isPaidContent("这个多少钱"));
        assertFalse(SyncMessageParser.isPaidContent("[等待买家付款]"));
        assertFalse(SyncMessageParser.isPaidContent("[我已拍下，待付款]"));
        assertFalse(SyncMessageParser.isPaidContent("[未付款，买家关闭了订单]"));
    }

    @Test
    void testUnpaidOrderNotEligibleForChatAutoReply() {
        ParsedChatMessage unpaid = ParsedChatMessage.builder()
                .content("[我已拍下，待付款]")
                .msgType(ChatMessage.MSG_TYPE_ORDER)
                .systemMessage(true)
                .paidEvent(false)
                .build();
        assertFalse(SyncMessageParser.isEligibleForChatAutoReply(unpaid));

        ParsedChatMessage normal = ParsedChatMessage.builder()
                .content("你好在吗")
                .msgType(ChatMessage.MSG_TYPE_TEXT)
                .paidEvent(false)
                .systemMessage(false)
                .build();
        assertTrue(SyncMessageParser.isEligibleForChatAutoReply(normal));
    }

    @Test
    void testParseChatMessage() {
        Map<String, Object> reminder = new LinkedHashMap<>();
        reminder.put("reminderTitle", "买家A");
        reminder.put("senderUserId", "12345");
        reminder.put("reminderContent", "你好");
        reminder.put("reminderUrl", "https://www.goofish.com/im?itemId=999888&peerUserId=12345");

        Map<String, Object> chat = new LinkedHashMap<>();
        chat.put("2", "12345@goofish");
        chat.put("5", System.currentTimeMillis());
        chat.put("10", reminder);

        Map<String, Object> root = new HashMap<>();
        root.put("1", chat);

        ParsedChatMessage parsed = SyncMessageParser.parseDecoded(root, "99999");
        assertNotNull(parsed);
        assertEquals("12345", parsed.getConversationId());
        assertEquals("12345", parsed.getSenderId());
        assertEquals("买家A", parsed.getSenderNick());
        assertEquals("你好", parsed.getContent());
        assertEquals("999888", parsed.getItemId());
        assertFalse(parsed.isFromSelf());
        assertFalse(parsed.isPaidEvent());
    }

    @Test
    void testParsePaidChatMessage() {
        Map<String, Object> reminder = new LinkedHashMap<>();
        reminder.put("reminderTitle", "买家B");
        reminder.put("senderUserId", "222");
        reminder.put("reminderContent", "[我已付款，等待你发货]");
        reminder.put("reminderUrl", "https://www.goofish.com/im?itemId=111&peerUserId=222");

        Map<String, Object> chat = new LinkedHashMap<>();
        chat.put("2", "222@goofish");
        chat.put("5", System.currentTimeMillis());
        chat.put("10", reminder);

        Map<String, Object> root = new HashMap<>();
        root.put("1", chat);

        ParsedChatMessage parsed = SyncMessageParser.parseDecoded(root, "99999");
        assertNotNull(parsed);
        assertTrue(parsed.isPaidEvent());
    }

    @Test
    void testExtractOrderIdDeep() {
        Map<String, Object> nested = new HashMap<>();
        nested.put("url", "fleamarket://order_detail?id=9876543210&other=1");
        Map<String, Object> root = new HashMap<>();
        root.put("card", nested);
        assertEquals("9876543210", SyncMessageParser.extractOrderIdDeep(root));
    }
}
