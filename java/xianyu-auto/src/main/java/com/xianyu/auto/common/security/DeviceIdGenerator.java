package com.xianyu.auto.common.security;

import java.security.SecureRandom;

/**
 * 闲鱼设备 ID 生成器。
 * 与网页端一致：UUID（含连字符）+ "-" + 用户 unb。
 * 例：6EF2D7B2-8239-4EFD-AB15-D5B71B330377-866221285
 */
public final class DeviceIdGenerator {

    private DeviceIdGenerator() {}

    private static final SecureRandom RANDOM = new SecureRandom();
    private static final char[] HEX = "0123456789ABCDEF".toCharArray();

    /**
     * 生成不带用户后缀的 32 位 hex（兼容旧逻辑）
     */
    public static String generate() {
        return generateUuidPart().replace("-", "").toLowerCase();
    }

    /**
     * 生成带用户 ID 的完整设备 ID（推荐，用于 WS did / loginToken）
     */
    public static String generate(String userId) {
        String uuid = generateUuidPart();
        if (userId == null || userId.isEmpty()) {
            return uuid;
        }
        return uuid + "-" + userId;
    }

    /**
     * 若已有 deviceId 缺少 userId 后缀，则补齐；格式错误则重新生成
     */
    public static String ensureWithUserId(String deviceId, String userId) {
        if (userId == null || userId.isEmpty()) {
            return deviceId != null ? deviceId : generate();
        }
        if (deviceId != null && deviceId.endsWith("-" + userId)) {
            return deviceId;
        }
        // 旧版 32 hex → 转成 UUID 形态再拼 userId
        if (deviceId != null && deviceId.matches("(?i)[0-9a-f]{32}")) {
            String hex = deviceId.toUpperCase();
            String uuid = hex.substring(0, 8) + "-" + hex.substring(8, 12) + "-"
                    + hex.substring(12, 16) + "-" + hex.substring(16, 20) + "-"
                    + hex.substring(20, 32);
            return uuid + "-" + userId;
        }
        return generate(userId);
    }

    private static String generateUuidPart() {
        char[] chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz".toCharArray();
        StringBuilder sb = new StringBuilder(36);
        for (int i = 0; i < 36; i++) {
            if (i == 8 || i == 13 || i == 18 || i == 23) {
                sb.append('-');
            } else if (i == 14) {
                sb.append('4');
            } else if (i == 19) {
                int rand = RANDOM.nextInt(16);
                sb.append(HEX[(rand & 0x3) | 0x8]);
            } else {
                sb.append(chars[RANDOM.nextInt(16)]);
            }
        }
        return sb.toString();
    }
}
