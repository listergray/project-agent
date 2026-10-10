package com.xianyu.auto.xianyu.protocol;

import lombok.Builder;
import lombok.Data;

import java.util.HashMap;
import java.util.Map;

/**
 * 注册包 payload（用于 /reg 路径）
 * 闲鱼 WebSocket 连接建立后必须先发注册包，否则服务端会断开连接
 */
@Data
@Builder
public class RegPayload {

    /** appKey（IM_APP_KEY） */
    private String appKey;

    /** token（wsToken，由 loginToken API 获取） */
    private String token;

    /** did（device ID，32 hex） */
    private String did;

    /** mid（消息 ID，UUID） */
    private String mid;

    /**
     * 转换为 Map 用于 JSON 序列化
     */
    public Map<String, Object> toMap() {
        Map<String, Object> map = new HashMap<>();
        map.put("appKey", appKey);
        map.put("token", token);
        map.put("did", did);
        map.put("mid", mid);
        return map;
    }
}
