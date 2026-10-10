package com.xianyu.auto.common.security;

import org.apache.commons.codec.digest.DigestUtils;

/**
 * 闲鱼 MTOP HTTP API 签名工具
 * 算法：MD5(token + "&" + t + "&" + appKey + "&" + data)
 * 其中 token 取 Cookie 中 _m_h5_tk 第一段（_ 之前）
 */
public final class SignUtils {

    private SignUtils() {}

    /**
     * 生成 MTOP API 签名
     *
     * @param mh5Tk Cookie 中 _m_h5_tk 完整值（形如 "abc_123"）
     * @param t     时间戳（毫秒）
     * @param appKey 应用 Key（参考 XianyuApiConst.APP_KEY）
     * @param data  请求体 JSON 字符串
     * @return 32 位小写 MD5 hex
     */
    public static String sign(String mh5Tk, long t, String appKey, String data) {
        String tokenPart = extractTokenPart(mh5Tk);
        String raw = tokenPart + "&" + t + "&" + appKey + "&" + data;
        return DigestUtils.md5Hex(raw);
    }

    /**
     * 从 _m_h5_tk 提取第一段（_ 之前部分）作为签名 token
     *
     * @param mh5Tk 完整 _m_h5_tk 值，如 "abc123_456789"
     * @return 第一段，如 "abc123"；若不含 _ 返回原值
     */
    public static String extractTokenPart(String mh5Tk) {
        if (mh5Tk == null || mh5Tk.isEmpty()) {
            return "";
        }
        int idx = mh5Tk.indexOf('_');
        return idx >= 0 ? mh5Tk.substring(0, idx) : mh5Tk;
    }
}
