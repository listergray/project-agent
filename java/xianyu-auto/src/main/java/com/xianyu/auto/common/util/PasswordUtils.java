package com.xianyu.auto.common.util;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

/**
 * 密码工具类（基于 Spring Security BCrypt）
 */
public class PasswordUtils {

    private static final BCryptPasswordEncoder ENCODER = new BCryptPasswordEncoder(10);

    public static String hash(String plain) {
        if (plain == null || plain.isEmpty()) {
            throw new IllegalArgumentException("密码不能为空");
        }
        return ENCODER.encode(plain);
    }

    public static boolean verify(String plain, String hash) {
        if (plain == null || hash == null || hash.isEmpty()) return false;
        try {
            return ENCODER.matches(plain, hash);
        } catch (Exception e) {
            return false;
        }
    }
}
