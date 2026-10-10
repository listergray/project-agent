package com.xianyu.auto.common.security;

import org.junit.jupiter.api.Test;
import org.msgpack.core.MessagePack;
import org.msgpack.core.MessagePacker;

import java.io.ByteArrayOutputStream;
import java.util.Base64;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * MessagePackDecoder 单元测试
 * 使用 msgpack-core 编码器生成测试样本，再用解码器验证
 */
class MessagePackDecoderTest {

    @Test
    void testDecodeSimpleMap() throws Exception {
        // 编码一个简单 Map
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        try (MessagePacker packer = MessagePack.newDefaultPacker(out)) {
            packer.packMapHeader(2)
                    .packString("key1").packString("value1")
                    .packString("key2").packInt(42);
        }
        String base64 = Base64.getEncoder().encodeToString(out.toByteArray());

        Map<String, Object> result = MessagePackDecoder.decode(base64);
        assertEquals("value1", result.get("key1"));
        assertEquals(42L, result.get("key2"));
    }

    @Test
    void testDecodeNestedMap() throws Exception {
        // 编码嵌套 Map（闲鱼消息结构）
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        try (MessagePacker packer = MessagePack.newDefaultPacker(out)) {
            packer.packMapHeader(2)
                    .packString("conversationId").packString("conv_123")
                    .packString("body").packMapHeader(2)
                        .packString("content").packString("你好")
                        .packString("type").packString("TEXT");
        }
        String base64 = Base64.getEncoder().encodeToString(out.toByteArray());

        Map<String, Object> result = MessagePackDecoder.decode(base64);
        assertEquals("conv_123", result.get("conversationId"));

        @SuppressWarnings("unchecked")
        Map<String, Object> body = (Map<String, Object>) result.get("body");
        assertEquals("你好", body.get("content"));
        assertEquals("TEXT", body.get("type"));
    }

    @Test
    void testDecodeArray() throws Exception {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        try (MessagePacker packer = MessagePack.newDefaultPacker(out)) {
            packer.packMapHeader(1)
                    .packString("list").packArrayHeader(3)
                        .packString("a")
                        .packString("b")
                        .packString("c");
        }
        String base64 = Base64.getEncoder().encodeToString(out.toByteArray());

        Map<String, Object> result = MessagePackDecoder.decode(base64);
        Object list = result.get("list");
        assertNotNull(list);
        assertTrue(list instanceof java.util.List);
        @SuppressWarnings("unchecked")
        java.util.List<Object> arr = (java.util.List<Object>) list;
        assertEquals(3, arr.size());
        assertEquals("a", arr.get(0));
    }

    @Test
    void testDecodeEmptyBase64() {
        Map<String, Object> result = MessagePackDecoder.decode("");
        assertTrue(result.isEmpty());

        result = MessagePackDecoder.decode(null);
        assertTrue(result.isEmpty());
    }

    @Test
    void testDecodeInvalidBase64() {
        // 非 Base64 字符被清洗后为空，返回空 Map（优雅降级）
        Map<String, Object> empty = MessagePackDecoder.decode("这不是有效的base64");
        assertTrue(empty.isEmpty());
    }

    @Test
    void testDecodeBooleanAndLong() throws Exception {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        try (MessagePacker packer = MessagePack.newDefaultPacker(out)) {
            packer.packMapHeader(3)
                    .packString("flag").packBoolean(true)
                    .packString("count").packLong(123456789L)
                    .packString("pi").packFloat(3.14f);
        }
        String base64 = Base64.getEncoder().encodeToString(out.toByteArray());

        Map<String, Object> result = MessagePackDecoder.decode(base64);
        assertEquals(Boolean.TRUE, result.get("flag"));
        assertEquals(123456789L, result.get("count"));
        assertEquals(3.14, (Double) result.get("pi"), 0.001);
    }

    @Test
    void testEncodeRoundTrip() {
        Map<String, Object> data = new java.util.LinkedHashMap<>();
        data.put("1", "hello");
        data.put("2", 42L);
        String encoded = MessagePackDecoder.encode(data);
        Map<String, Object> decoded = MessagePackDecoder.decode(encoded);
        assertEquals("hello", decoded.get("1"));
        assertEquals(42L, decoded.get("2"));
    }

    @Test
    void testDecryptPlainJsonBase64() {
        String json = "{\"contentType\":1,\"text\":{\"text\":\"hi\"}}";
        String base64 = Base64.getEncoder().encodeToString(json.getBytes());
        Object result = MessagePackDecoder.decryptSyncData(base64);
        assertTrue(result instanceof Map);
        @SuppressWarnings("unchecked")
        Map<String, Object> map = (Map<String, Object>) result;
        assertEquals(1, ((Number) map.get("contentType")).intValue());
    }
}
