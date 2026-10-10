package com.xianyu.auto.common.security;

import com.xianyu.auto.xianyu.constant.XianyuApiConst;

import java.util.HashMap;
import java.util.Map;

/**
 * 闲鱼 Cookie 解析工具
 * 支持从浏览器复制的 Cookie 字符串解析为 KV，并提取关键字段。
 */
public final class CookieUtils {

    private CookieUtils() {}

    /**
     * 解析 Cookie 字符串为 KV Map
     * 支持两种格式：
     * 1. "key1=value1; key2=value2"
     * 2. 多行 / 制表符分隔
     *
     * @param cookieText Cookie 原文
     * @return KV Map（key 小写），null 入参返回空 Map
     */
    public static Map<String, String> parseToMap(String cookieText) {
        Map<String, String> result = new HashMap<>();
        if (cookieText == null || cookieText.isEmpty()) {
            return result;
        }
        // 统一换行/制表符为分号分隔
        String normalized = cookieText.replaceAll("[\r\n\t]+", ";");
        String[] parts = normalized.split(";");
        for (String part : parts) {
            int eq = part.indexOf('=');
            if (eq > 0) {
                String key = part.substring(0, eq).trim();
                String value = part.substring(eq + 1).trim();
                if (!key.isEmpty()) {
                    result.put(key, value);
                }
            }
        }
        return result;
    }

    /**
     * 提取 _m_h5_tk 值
     */
    public static String extractMh5Tk(String cookieText) {
        return parseToMap(cookieText).get(XianyuApiConst.COOKIE_MH5_TK);
    }

    /**
     * 提取 _m_h5_tk 第一段（用于签名）
     */
    public static String extractSignToken(String cookieText) {
        String mh5Tk = extractMh5Tk(cookieText);
        return SignUtils.extractTokenPart(mh5Tk);
    }

    /**
     * 提取 unb（用户 ID）
     */
    public static String extractUnb(String cookieText) {
        return parseToMap(cookieText).get(XianyuApiConst.COOKIE_UNB);
    }

    /**
     * 基础校验 Cookie 是否含必要字段
     * 必须包含：_m_h5_tk、_m_h5_tk_enc、unb
     */
    public static boolean isCookieValid(String cookieText) {
        if (cookieText == null || cookieText.trim().isEmpty()) {
            return false;
        }
        Map<String, String> map = parseToMap(cookieText);
        return map.containsKey(XianyuApiConst.COOKIE_MH5_TK)
                && map.containsKey(XianyuApiConst.COOKIE_MH5_TK_ENC)
                && map.containsKey(XianyuApiConst.COOKIE_UNB);
    }

    /**
     * 将 KV Map 拼回 Cookie 字符串
     */
    public static String toCookieString(Map<String, String> cookieMap) {
        if (cookieMap == null || cookieMap.isEmpty()) {
            return "";
        }
        StringBuilder sb = new StringBuilder();
        boolean first = true;
        for (Map.Entry<String, String> entry : cookieMap.entrySet()) {
            if (!first) {
                sb.append("; ");
            }
            sb.append(entry.getKey()).append('=').append(entry.getValue());
            first = false;
        }
        return sb.toString();
    }
}
