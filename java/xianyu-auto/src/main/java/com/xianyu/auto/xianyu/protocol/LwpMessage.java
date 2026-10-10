package com.xianyu.auto.xianyu.protocol;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.io.Serializable;
import java.util.List;
import java.util.Map;

/**
 * LWP 协议消息模型。
 * 闲鱼 WebSocket 外层 JSON 使用 body（非 payload）：
 * {
 *   "lwp": "/s/sync",
 *   "headers": {...},
 *   "body": {...} | [...]
 * }
 */
@Data
public class LwpMessage implements Serializable {

    private String lwp;

    private Map<String, Object> headers;

    /** 响应码（心跳 ACK 等） */
    private Integer code;

    /** 协议负载（发送/推送均用 body） */
    @JsonProperty("body")
    private Object body;

    /** 兼容旧字段名 */
    @JsonProperty("payload")
    private Object payload;

    @JsonIgnore
    public Object getBodyOrPayload() {
        return body != null ? body : payload;
    }

    @SuppressWarnings("unchecked")
    public Map<String, Object> getBodyAsMap() {
        Object b = getBodyOrPayload();
        if (b instanceof Map) {
            return (Map<String, Object>) b;
        }
        return null;
    }

    @SuppressWarnings("unchecked")
    public List<Object> getBodyAsList() {
        Object b = getBodyOrPayload();
        if (b instanceof List) {
            return (List<Object>) b;
        }
        return null;
    }

    /**
     * 兼容旧调用：payload.body.custom
     */
    @SuppressWarnings("unchecked")
    public Map<String, Object> getNestedBodyMap() {
        Map<String, Object> map = getBodyAsMap();
        if (map == null) return null;
        Object nested = map.get("body");
        if (nested instanceof Map) {
            return (Map<String, Object>) nested;
        }
        return map;
    }

    public String getCustomField() {
        Map<String, Object> nested = getNestedBodyMap();
        if (nested == null) return null;
        Object custom = nested.get("custom");
        return custom == null ? null : custom.toString();
    }

    /**
     * 是否为 syncPushPackage 推送
     */
    @SuppressWarnings("unchecked")
    public boolean isSyncPushPackage() {
        Map<String, Object> map = getBodyAsMap();
        if (map == null) return false;
        Object pkg = map.get("syncPushPackage");
        if (!(pkg instanceof Map)) return false;
        Object data = ((Map<String, Object>) pkg).get("data");
        return data instanceof List && !((List<?>) data).isEmpty();
    }

    @SuppressWarnings("unchecked")
    public List<Map<String, Object>> getSyncPushDataList() {
        Map<String, Object> map = getBodyAsMap();
        if (map == null) return List.of();
        Object pkg = map.get("syncPushPackage");
        if (!(pkg instanceof Map)) return List.of();
        Object data = ((Map<String, Object>) pkg).get("data");
        if (!(data instanceof List)) return List.of();
        List<?> list = (List<?>) data;
        java.util.ArrayList<Map<String, Object>> result = new java.util.ArrayList<>();
        for (Object item : list) {
            if (item instanceof Map) {
                result.add((Map<String, Object>) item);
            }
        }
        return result;
    }
}
