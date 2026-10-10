package com.xianyu.auto.common.security;

import org.msgpack.core.MessageBufferPacker;
import org.msgpack.core.MessagePack;
import org.msgpack.core.MessageUnpacker;
import org.msgpack.value.Value;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 闲鱼 MessagePack 解码 / 编码工具。
 * syncPush 消息：Base64 → MessagePack → Map（键多为数字字符串 "1"/"2"/"10"）
 * 发送消息 custom.data：JSON 的 Base64（见 XianyuWsClient），不走本类 encode。
 */
public final class MessagePackDecoder {

    private MessagePackDecoder() {}

    /**
     * 解码 Base64 字符串为 Map（根必须是 Map）
     */
    public static Map<String, Object> decode(String base64) {
        Object value = decryptSyncData(base64);
        if (value instanceof Map) {
            @SuppressWarnings("unchecked")
            Map<String, Object> map = (Map<String, Object>) value;
            return map;
        }
        return new HashMap<>();
    }

    /**
     * 解密 syncPushPackage.data 字段：
     * 1) 尝试 Base64 → UTF-8 JSON
     * 2) 失败则 Base64 → MessagePack → Java 对象
     */
    public static Object decryptSyncData(String raw) {
        if (raw == null || raw.isEmpty()) {
            return new HashMap<>();
        }
        // 先尝试明文 JSON（部分推送无需 MessagePack）
        try {
            byte[] maybeJson = Base64.getDecoder().decode(cleanBase64(raw));
            String asText = new String(maybeJson, StandardCharsets.UTF_8).trim();
            if (asText.startsWith("{") || asText.startsWith("[")) {
                return com.xianyu.auto.common.util.JsonUtils.fromJson(asText, Object.class);
            }
        } catch (Exception ignored) {
            // fall through to MessagePack
        }

        byte[] bytes;
        try {
            bytes = Base64.getDecoder().decode(cleanBase64(raw));
        } catch (Exception e) {
            throw new RuntimeException("Base64 解码失败: " + e.getMessage(), e);
        }
        return decodeBytesToObject(bytes);
    }

    public static Map<String, Object> decodeBytes(byte[] bytes) {
        Object converted = decodeBytesToObject(bytes);
        if (converted instanceof Map) {
            @SuppressWarnings("unchecked")
            Map<String, Object> map = (Map<String, Object>) converted;
            return map;
        }
        return new HashMap<>();
    }

    public static Object decodeBytesToObject(byte[] bytes) {
        if (bytes == null || bytes.length == 0) {
            return new HashMap<>();
        }
        try (MessageUnpacker unpacker = MessagePack.newDefaultUnpacker(bytes)) {
            Value value = unpacker.unpackValue();
            return convertValue(value);
        } catch (IOException e) {
            throw new RuntimeException("MessagePack 解码失败: " + e.getMessage(), e);
        }
    }

    @SuppressWarnings("unchecked")
    private static Object convertValue(Value value) {
        if (value == null) {
            return null;
        }
        switch (value.getValueType()) {
            case NIL:
                return null;
            case BOOLEAN:
                return value.asBooleanValue().getBoolean();
            case INTEGER:
                try {
                    return value.asIntegerValue().asLong();
                } catch (Exception e) {
                    return value.asIntegerValue().toString();
                }
            case FLOAT:
                return value.asFloatValue().toDouble();
            case STRING:
                return value.asStringValue().asString();
            case BINARY:
                return value.asBinaryValue().asByteArray();
            case ARRAY:
                List<Object> list = new ArrayList<>();
                for (Value item : value.asArrayValue()) {
                    list.add(convertValue(item));
                }
                return list;
            case MAP:
                // 保留插入顺序；键统一 toString（数字键 → "1"）
                Map<String, Object> map = new LinkedHashMap<>();
                for (Map.Entry<Value, Value> entry : value.asMapValue().entrySet()) {
                    String key = convertValue(entry.getKey()).toString();
                    map.put(key, convertValue(entry.getValue()));
                }
                return map;
            case EXTENSION:
                return value.toString();
            default:
                return value.toString();
        }
    }

    /**
     * 将 Map/List 编码为真正的 MessagePack Base64（可用于单测或未来扩展）
     */
    public static String encode(Map<String, Object> data) {
        if (data == null || data.isEmpty()) {
            return "";
        }
        try {
            MessageBufferPacker packer = MessagePack.newDefaultBufferPacker();
            packValue(packer, data);
            packer.close();
            return Base64.getEncoder().encodeToString(packer.toByteArray());
        } catch (Exception e) {
            throw new RuntimeException("MessagePack 编码失败: " + e.getMessage(), e);
        }
    }

    @SuppressWarnings("unchecked")
    private static void packValue(MessageBufferPacker packer, Object value) throws IOException {
        if (value == null) {
            packer.packNil();
        } else if (value instanceof Boolean) {
            packer.packBoolean((Boolean) value);
        } else if (value instanceof Integer) {
            packer.packInt((Integer) value);
        } else if (value instanceof Long) {
            packer.packLong((Long) value);
        } else if (value instanceof Float) {
            packer.packFloat((Float) value);
        } else if (value instanceof Double) {
            packer.packDouble((Double) value);
        } else if (value instanceof byte[]) {
            byte[] bytes = (byte[]) value;
            packer.packBinaryHeader(bytes.length);
            packer.writePayload(bytes);
        } else if (value instanceof String) {
            packer.packString((String) value);
        } else if (value instanceof List) {
            List<?> list = (List<?>) value;
            packer.packArrayHeader(list.size());
            for (Object item : list) {
                packValue(packer, item);
            }
        } else if (value instanceof Map) {
            Map<?, ?> map = (Map<?, ?>) value;
            packer.packMapHeader(map.size());
            for (Map.Entry<?, ?> entry : map.entrySet()) {
                packValue(packer, entry.getKey() == null ? null : entry.getKey().toString());
                packValue(packer, entry.getValue());
            }
        } else if (value instanceof Number) {
            packer.packLong(((Number) value).longValue());
        } else {
            packer.packString(value.toString());
        }
    }

    private static String cleanBase64(String data) {
        StringBuilder sb = new StringBuilder(data.length());
        for (int i = 0; i < data.length(); i++) {
            char c = data.charAt(i);
            if ((c >= 'A' && c <= 'Z') || (c >= 'a' && c <= 'z')
                    || (c >= '0' && c <= '9') || c == '+' || c == '/' || c == '=') {
                sb.append(c);
            }
        }
        while (sb.length() % 4 != 0) {
            sb.append('=');
        }
        return sb.toString();
    }
}
