package com.xianyu.auto.common.security;

import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * CookieUtils 单元测试
 */
class CookieUtilsTest {

    @Test
    void testParseStandardCookie() {
        String cookie = "_m_h5_tk=abc_123; _m_h5_tk_enc=xyz; unb=12345; cookie2=abc";
        Map<String, String> map = CookieUtils.parseToMap(cookie);

        assertEquals("abc_123", map.get("_m_h5_tk"));
        assertEquals("xyz", map.get("_m_h5_tk_enc"));
        assertEquals("12345", map.get("unb"));
        assertEquals("abc", map.get("cookie2"));
    }

    @Test
    void testParseMultilineCookie() {
        // 浏览器 DevTools 复制的 Cookie 可能有换行
        String cookie = "_m_h5_tk=abc_123\n_m_h5_tk_enc=xyz\nunb=12345";
        Map<String, String> map = CookieUtils.parseToMap(cookie);

        assertEquals("abc_123", map.get("_m_h5_tk"));
        assertEquals("xyz", map.get("_m_h5_tk_enc"));
        assertEquals("12345", map.get("unb"));
    }

    @Test
    void testParseWithSpaces() {
        String cookie = "  key1 = value1 ; key2=value2  ";
        Map<String, String> map = CookieUtils.parseToMap(cookie);
        assertEquals("value1", map.get("key1"));
        assertEquals("value2", map.get("key2"));
    }

    @Test
    void testExtractMh5Tk() {
        String cookie = "_m_h5_tk=abc_123; _m_h5_tk_enc=xyz; unb=12345";
        assertEquals("abc_123", CookieUtils.extractMh5Tk(cookie));
    }

    @Test
    void testExtractSignToken() {
        String cookie = "_m_h5_tk=abc_123_456; unb=12345";
        assertEquals("abc", CookieUtils.extractSignToken(cookie));
    }

    @Test
    void testExtractUnb() {
        String cookie = "_m_h5_tk=abc; unb=12345";
        assertEquals("12345", CookieUtils.extractUnb(cookie));
    }

    @Test
    void testIsValidCookie() {
        String valid = "_m_h5_tk=abc; _m_h5_tk_enc=xyz; unb=12345";
        String missingUnb = "_m_h5_tk=abc; _m_h5_tk_enc=xyz";
        String empty = "";

        assertTrue(CookieUtils.isCookieValid(valid));
        assertFalse(CookieUtils.isCookieValid(missingUnb));
        assertFalse(CookieUtils.isCookieValid(empty));
        assertFalse(CookieUtils.isCookieValid(null));
    }

    @Test
    void testToCookieString() {
        Map<String, String> map = Map.of(
                "_m_h5_tk", "abc",
                "unb", "12345"
        );
        String cookie = CookieUtils.toCookieString(map);
        // 顺序可能变化，但应包含两个 key=value
        assertTrue(cookie.contains("_m_h5_tk=abc"));
        assertTrue(cookie.contains("unb=12345"));
    }

    @Test
    void testEmptyInput() {
        Map<String, String> map = CookieUtils.parseToMap(null);
        assertTrue(map.isEmpty());

        map = CookieUtils.parseToMap("");
        assertTrue(map.isEmpty());
    }
}
