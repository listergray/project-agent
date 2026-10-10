package com.xianyu.auto.xianyu.client;

import com.fasterxml.jackson.databind.JsonNode;
import com.xianyu.auto.common.exception.BusinessException;
import com.xianyu.auto.common.security.CookieUtils;
import com.xianyu.auto.common.security.SignUtils;
import com.xianyu.auto.common.util.JsonUtils;
import com.xianyu.auto.xianyu.constant.XianyuApiConst;
import com.xianyu.auto.xianyu.config.XianyuProperties;
import lombok.extern.slf4j.Slf4j;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.TimeUnit;

/**
 * 闲鱼 MTOP HTTP API 客户端
 *
 * 关键 API：
 *  - loginToken: 获取 WebSocket 注册 token
 *  - hasLogin: Cookie 保活 / 登录态校验
 *  - itemDetail: 商品详情（Phase 3 用）
 *  - tradeConsignment: 确认发货（Phase 3 用）
 *
 * 签名算法：MD5(token + "&" + t + "&" + appKey + "&" + data)
 * token 取 Cookie _m_h5_tk 第一段（_ 之前）
 */
@Slf4j
@Component
public class XianyuApiClient {

    private static final MediaType FORM = MediaType.parse("application/x-www-form-urlencoded");

    private final OkHttpClient httpClient;
    private final XianyuProperties properties;

    public XianyuApiClient(XianyuProperties properties) {
        this.properties = properties;
        this.httpClient = new OkHttpClient.Builder()
                .connectTimeout(10, TimeUnit.SECONDS)
                .readTimeout(30, TimeUnit.SECONDS)
                .writeTimeout(15, TimeUnit.SECONDS)
                .followRedirects(false)
                .build();
    }

    /**
     * 调用 mtop.taobao.idlemessage.pc.login.token 获取 WS Token
     *
     * @param cookie 完整 Cookie 字符串
     * @param deviceId 设备 ID（32 hex）
     * @return WS Token（用于 XianyuWsClient 注册包）
     */
    /** loginToken 结果：token + 绝对过期时间 */
    public record WsLoginToken(String accessToken, long expireAtMs) {}

    public WsLoginToken loginToken(String cookie, String deviceId) {
        String formattedDeviceId = formatDeviceId(deviceId);

        Map<String, Object> params = new HashMap<>();
        params.put("appKey", XianyuApiConst.IM_APP_KEY);
        params.put("deviceId", formattedDeviceId);

        String mh5Tk = CookieUtils.extractMh5Tk(cookie);
        String signToken = SignUtils.extractTokenPart(mh5Tk);
        String unb = CookieUtils.extractUnb(cookie);
        log.debug("loginToken - mh5Tk: {}, signToken: {}, unb: {}, deviceId: {}",
                mh5Tk != null ? mh5Tk.substring(0, Math.min(20, mh5Tk.length())) + "..." : null,
                signToken != null ? signToken.substring(0, Math.min(20, signToken.length())) + "..." : null,
                unb, formattedDeviceId);

        JsonNode result = callApi(XianyuApiConst.API_LOGIN_TOKEN, cookie, params, XianyuApiConst.APP_KEY);
        JsonNode data = result.path("data");
        if (data.isMissingNode()) {
            throw new BusinessException("loginToken 响应缺少 data 字段: " + result);
        }
        String accessToken = data.path("accessToken").asText(null);
        if (accessToken == null || accessToken.isEmpty()) {
            throw new BusinessException("loginToken 响应缺少 accessToken: " + result);
        }
        long expireRaw = data.path("accessTokenExpiredTime").asLong(86_400_000L);
        // 接口返回多为有效期毫秒（如 86400000）；若像时间戳则直接用
        long expireAtMs = expireRaw > 1_000_000_000_000L
                ? expireRaw
                : System.currentTimeMillis() + Math.max(expireRaw, 3_600_000L);
        log.info("获取 WS Token 成功: uid={}, expireAt={}", unb, expireAtMs);
        return new WsLoginToken(accessToken, expireAtMs);
    }

    /**
     * 刷新 _m_h5_tk：访问闲鱼首页，从 Set-Cookie 取新 token。
     * （旧 login.check 接口已下线，不能再用来刷新）
     */
    public String refreshMh5Tk(String cookie) {
        String[] urls = {
                "https://www.goofish.com/",
                "https://h5api.m.goofish.com/h5/" + XianyuApiConst.API_HAS_LOGIN
                        + "/1.0/?jsv=2.7.4&appKey=" + properties.getAppKey()
                        + "&t=" + System.currentTimeMillis()
        };
        for (String url : urls) {
            Request request = new Request.Builder()
                    .url(url)
                    .header("Cookie", cookie)
                    .header("User-Agent", XianyuApiConst.USER_AGENT)
                    .header("Referer", XianyuApiConst.REFERER)
                    .get()
                    .build();
            try (Response response = httpClient.newCall(request).execute()) {
                String updated = mergeSetCookie(cookie, response);
                if (!updated.equals(cookie)) {
                    log.info("刷新 _m_h5_tk 成功 via {}", url.contains("goofish.com/") && !url.contains("h5api") ? "homepage" : "getUserNav");
                    return updated;
                }
            } catch (IOException e) {
                log.debug("刷新 _m_h5_tk 请求失败 url={}: {}", url, e.getMessage());
            }
        }
        log.warn("刷新 _m_h5_tk 未获取到新值，使用原 Cookie");
        return cookie;
    }

    /** 合并响应里所有 Set-Cookie 到原 Cookie */
    private String mergeSetCookie(String cookie, Response response) {
        if (response == null) return cookie;
        java.util.List<String> setCookies = response.headers("Set-Cookie");
        if (setCookies == null || setCookies.isEmpty()) {
            String single = response.header("Set-Cookie");
            if (single == null) return cookie;
            setCookies = java.util.List.of(single);
        }
        String updated = cookie;
        boolean changed = false;
        for (String sc : setCookies) {
            String mh5 = extractCookieValue(sc, "_m_h5_tk");
            String mh5Enc = extractCookieValue(sc, "_m_h5_tk_enc");
            if (mh5 != null) {
                updated = updateCookieValue(updated, "_m_h5_tk", mh5);
                changed = true;
            }
            if (mh5Enc != null) {
                updated = updateCookieValue(updated, "_m_h5_tk_enc", mh5Enc);
                changed = true;
            }
        }
        return changed ? updated : cookie;
    }

    /**
     * 规范化 deviceId：
     * - 已含连字符（UUID 或 UUID-userId）直接使用
     * - 32 位 hex 转为 UUID 形态
     */
    private String formatDeviceId(String deviceId) {
        if (deviceId == null || deviceId.isEmpty()) {
            return deviceId;
        }
        if (deviceId.contains("-")) {
            return deviceId;
        }
        if (deviceId.length() == 32) {
            String hex = deviceId.toUpperCase();
            return hex.substring(0, 8) + "-" + hex.substring(8, 12) + "-"
                    + hex.substring(12, 16) + "-" + hex.substring(16, 20) + "-"
                    + hex.substring(20, 32);
        }
        return deviceId;
    }

    /**
     * 从 Set-Cookie 头中提取指定 cookie 值
     */
    private String extractCookieValue(String setCookieHeader, String cookieName) {
        String[] cookies = setCookieHeader.split(";");
        for (String cookie : cookies) {
            cookie = cookie.trim();
            if (cookie.startsWith(cookieName + "=")) {
                return cookie.substring(cookieName.length() + 1);
            }
        }
        return null;
    }

    /**
     * 更新 Cookie 字符串中指定 key 的值
     */
    private String updateCookieValue(String cookie, String key, String value) {
        if (value == null) return cookie;
        Map<String, String> map = CookieUtils.parseToMap(cookie);
        map.put(key, value);
        return CookieUtils.toCookieString(map);
    }

    /**
     * 校验登录态（Cookie 保活）。
     * 优先 mtop.taobao.idlemessage.pc.loginuser.get（闲鱼 IM 仍可用）；
     * getUserNav / 旧 login.check 在 goofish 上常返回 API_NOT_FOUNDED。
     */
    public boolean hasLogin(String cookie) {
        String unb = CookieUtils.extractUnb(cookie);

        // 主路径：IM loginuser.get
        try {
            JsonNode result = callApi(XianyuApiConst.API_LOGIN_USER_GET, cookie, new HashMap<>());
            if (isApiSuccess(result)) {
                log.info("hasLogin 成功(loginuser.get): unb={}", unb);
                return true;
            }
            String ret = firstRet(result);
            if (isSessionDead(ret)) {
                log.warn("hasLogin 会话失效: ret={}, unb={}", ret, unb);
                return false;
            }
            log.warn("hasLogin loginuser.get 未成功: ret={}, unb={}，尝试 getUserNav", ret, unb);
        } catch (Exception e) {
            log.warn("hasLogin loginuser.get 异常: {}, unb={}", e.getMessage(), unb);
        }

        // 备选
        try {
            JsonNode result = callApi(XianyuApiConst.API_HAS_LOGIN, cookie, new HashMap<>());
            if (isApiSuccess(result)) {
                log.info("hasLogin 成功(getUserNav): unb={}", unb);
                return true;
            }
            String ret = firstRet(result);
            if (isSessionDead(ret)) {
                log.warn("hasLogin 会话失效(getUserNav): ret={}, unb={}", ret, unb);
                return false;
            }
            // API 不存在等：不算 Cookie 失效
            if (ret != null && ret.contains("API_NOT_FOUNDED")) {
                log.warn("hasLogin 接口不可用，跳过误判: ret={}, unb={}", ret, unb);
                return true;
            }
            log.warn("hasLogin 最终未确认: ret={}, unb={}", ret, unb);
            return false;
        } catch (Exception e) {
            log.warn("hasLogin 备选异常: {}, unb={}", e.getMessage(), unb);
            return false;
        }
    }

    private boolean isSessionDead(String ret) {
        if (ret == null) return false;
        return ret.contains("SESSION_EXPIRED")
                || ret.contains("TOKEN_EXOIRED")
                || ret.contains("TOKEN_EXPIRED")
                || ret.contains("ILLEGAL_ACCESS")
                || ret.contains("FAIL_SYS_SESSION");
    }

    private String firstRet(JsonNode result) {
        if (result == null) return null;
        JsonNode ret = result.path("ret");
        if (ret.isArray() && ret.size() > 0) {
            return ret.get(0).asText(null);
        }
        return null;
    }

    /** 商品详情 */
    public JsonNode itemDetail(String cookie, String itemId) {
        Map<String, Object> params = new HashMap<>();
        params.put("itemId", itemId);
        return callApi(XianyuApiConst.API_ITEM_DETAIL, cookie, params);
    }

    /**
     * 卖家商品列表（闲鱼号主页列表）。
     * userId 为闲鱼 unb；pageNumber 从 1 开始。
     * 对齐 goofish personal 页：needGroupInfo + pageSize。
     */
    public JsonNode listSellerItems(String cookie, String userId, int pageNumber, int pageSize) {
        return listSellerItems(cookie, userId, pageNumber, pageSize, null, null);
    }

    public JsonNode listSellerItems(String cookie, String userId, int pageNumber, int pageSize,
                                    String nextPageModel, String nextPageNum) {
        return listSellerItemsBound(cookie, userId, pageNumber, pageSize, nextPageModel, nextPageNum).result();
    }

    public CookieBoundResult listSellerItemsBound(String cookie, String userId, int pageNumber, int pageSize,
                                                 String nextPageModel, String nextPageNum) {
        Map<String, Object> params = new HashMap<>();
        params.put("needGroupInfo", pageNumber <= 1);
        params.put("userId", userId);
        params.put("pageNumber", Math.max(pageNumber, 1));
        params.put("pageSize", pageSize > 0 ? pageSize : 20);
        if (nextPageModel != null && !nextPageModel.isBlank()) {
            params.put("nextPageModel", nextPageModel);
        }
        if (nextPageNum != null && !nextPageNum.isBlank()) {
            params.put("nextPageNum", nextPageNum);
        }
        return callApiBound(XianyuApiConst.API_SELLER_ITEM_LIST, cookie, params);
    }

    /** 发布商品（payload 结构对齐网页端 publish） */
    public JsonNode publishItem(String cookie, Map<String, Object> publishData) {
        return callApi(XianyuApiConst.API_ITEM_PUBLISH, cookie, publishData);
    }

    public JsonNode downShelfItem(String cookie, String itemId) {
        Map<String, Object> params = new HashMap<>();
        params.put("itemId", itemId);
        return callApi(XianyuApiConst.API_ITEM_DOWN, cookie, params);
    }

    public JsonNode upShelfItem(String cookie, String itemId) {
        Map<String, Object> params = new HashMap<>();
        params.put("itemId", itemId);
        return callApi(XianyuApiConst.API_ITEM_UP, cookie, params);
    }

    public JsonNode querySoldOrders(String cookie, int pageNumber, int pageSize) {
        Map<String, Object> params = new HashMap<>();
        params.put("pageNumber", Math.max(pageNumber, 1));
        params.put("pageSize", pageSize > 0 ? pageSize : 20);
        return callApi(XianyuApiConst.API_TRADE_SOLD, cookie, params);
    }

    public boolean isApiSuccess(JsonNode result) {
        if (result == null) return false;
        JsonNode ret = result.path("ret");
        if (ret.isArray() && ret.size() > 0) {
            return ret.get(0).asText("").startsWith("SUCCESS");
        }
        return false;
    }

    /**
     * 确认发货（虚拟商品 / 无需物流）。
     *
     * @param cookie  完整 Cookie
     * @param orderId 闲鱼订单 ID
     * @return true=成功
     */
    public boolean tradeConsignment(String cookie, String orderId) {
        return tradeConsignmentDetail(cookie, orderId).success();
    }

    /** 确认发货详情（含失败原因，便于落库展示） */
    public ConsignResult tradeConsignmentDetail(String cookie, String orderId) {
        if (orderId == null || orderId.isEmpty()) {
            return new ConsignResult(false, "orderId 为空");
        }
        // 网页端虚拟发货常用 bizOrderId；兼容 orderId
        String[][] payloads = {
                {"bizOrderId", orderId},
                {"orderId", orderId}
        };
        String lastRet = null;
        for (String[] kv : payloads) {
            Map<String, Object> params = new HashMap<>();
            params.put(kv[0], kv[1]);
            try {
                CookieBoundResult bound = callApiBound(
                        XianyuApiConst.API_TRADE_CONSIGNMENT, cookie, params);
                JsonNode result = bound.result();
                String retStr = firstRet(result);
                lastRet = retStr;
                if (retStr != null && retStr.startsWith("SUCCESS")) {
                    log.info("确认发货成功: orderId={}, key={}", orderId, kv[0]);
                    return new ConsignResult(true, retStr);
                }
                // 参数名不对时换下一组；API 不存在则直接失败
                if (retStr != null && retStr.contains("API_NOT_FOUNDED")) {
                    log.warn("确认发货 API 不存在: orderId={}, ret={}", orderId, retStr);
                    return new ConsignResult(false, retStr);
                }
                log.warn("确认发货未成功: orderId={}, key={}, ret={}, body={}",
                        orderId, kv[0], retStr, result);
            } catch (Exception e) {
                lastRet = e.getMessage();
                log.warn("确认发货异常: orderId={}, key={}, error={}", orderId, kv[0], e.getMessage());
            }
        }
        return new ConsignResult(false, lastRet != null ? lastRet : "确认发货失败");
    }

    public record ConsignResult(boolean success, String message) {}

    /** API 调用结果（含可能被 Set-Cookie 刷新后的 Cookie） */
    public record CookieBoundResult(JsonNode result, String cookie) {}

    /**
     * 调用闲鱼 MTOP API
     * 完成签名 + 请求 + 响应解析
     *
     * @param apiName API 名称（如 mtop.taobao.idle.user.login.check）
     * @param cookie 完整 Cookie
     * @param params 请求参数（data 字段）
     * @return 响应 JSON 根节点
     */
    private JsonNode callApi(String apiName, String cookie, Map<String, Object> params) {
        return callApi(apiName, cookie, params, properties.getAppKey());
    }

    /**
     * 调用闲鱼 MTOP API（指定 appKey）
     * 令牌过期时会合并 Set-Cookie / 刷新 _m_h5_tk 并自动重试一次。
     */
    private JsonNode callApi(String apiName, String cookie, Map<String, Object> params, String appKey) {
        return callApiBound(apiName, cookie, params, appKey).result();
    }

    /**
     * 与 {@link #callApi} 相同，但额外返回刷新后的 Cookie（供调用方落库）。
     */
    public CookieBoundResult callApiBound(String apiName, String cookie, Map<String, Object> params) {
        return callApiBound(apiName, cookie, params, properties.getAppKey());
    }

    private CookieBoundResult callApiBound(String apiName, String cookie, Map<String, Object> params, String appKey) {
        CookieBoundResult first = doCallOnce(apiName, cookie, params, appKey);
        String ret = firstRet(first.result());
        if (!isTokenExpiredRet(ret)) {
            return first;
        }
        // 优先用响应 Set-Cookie；没有则访问首页刷 _m_h5_tk
        String nextCookie = first.cookie();
        if (nextCookie == null || nextCookie.equals(cookie)
                || mh5TkUnchanged(cookie, nextCookie)) {
            nextCookie = refreshMh5Tk(cookie);
        }
        if (nextCookie == null || nextCookie.equals(cookie)) {
            log.warn("令牌过期且无法刷新 _m_h5_tk: api={}, ret={}", apiName, ret);
            return first;
        }
        log.info("令牌过期，已刷新 _m_h5_tk 并重试: api={}", apiName);
        return doCallOnce(apiName, nextCookie, params, appKey);
    }

    private CookieBoundResult doCallOnce(String apiName, String cookie, Map<String, Object> params, String appKey) {
        long t = System.currentTimeMillis();
        String data = JsonUtils.toJson(params);
        String mh5Tk = CookieUtils.extractMh5Tk(cookie);
        String sign = SignUtils.sign(mh5Tk, t, appKey, data);

        String formBody = String.format(
                "jsv=2.7.4&appKey=%s&t=%d&sign=%s&api=%s&v=1.0&type=originaljson&dataType=json&accountSite=xianyu&sessionOption=AutoLoginOnly&spm_cnt=a21ybx.manage.0.0&spm_pre=widle.manage&timeout=20000&data=%s",
                appKey,
                t,
                sign,
                apiName,
                urlEncode(data)
        );

        log.debug("callApi - apiName={}, cookieLength={}, data={}",
                apiName, cookie != null ? cookie.length() : 0, data);

        Request request = new Request.Builder()
                .url(XianyuApiConst.H5_API_BASE + apiName + "/1.0/")
                .header("Cookie", cookie)
                .header("Content-Type", "application/x-www-form-urlencoded")
                .header("Referer", XianyuApiConst.REFERER)
                .header("User-Agent", XianyuApiConst.USER_AGENT)
                .header("Accept", "application/json")
                .header("X-Requested-With", "XMLHttpRequest")
                .header("mtop-ttid", "@")
                .header("mtop-device-id", params.getOrDefault("deviceId", "").toString())
                .header("mtop-x-features", "27")
                .post(RequestBody.create(formBody, FORM))
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                throw new BusinessException(apiName + " HTTP 失败: " + response.code());
            }
            String updatedCookie = mergeSetCookie(cookie, response);
            String body = response.body() != null ? response.body().string() : "{}";
            JsonNode result = JsonUtils.fromJson(body, JsonNode.class);
            if (result == null) {
                throw new BusinessException(apiName + " 响应非 JSON: " + body);
            }

            JsonNode ret = result.path("ret");
            if (ret.isArray() && ret.size() > 0
                    && ret.get(0).asText("").contains(XianyuApiConst.ERROR_RGV587)) {
                throw new BusinessException("触发滑块验证，需手动访问 https://www.goofish.com/im 完成");
            }
            return new CookieBoundResult(result, updatedCookie);
        } catch (IOException e) {
            throw new BusinessException(apiName + " 调用异常: " + e.getMessage(), e);
        }
    }

    private boolean isTokenExpiredRet(String ret) {
        if (ret == null) return false;
        return ret.contains("TOKEN_EXOIRED") || ret.contains("TOKEN_EXPIRED");
    }

    private boolean mh5TkUnchanged(String before, String after) {
        String a = CookieUtils.extractMh5Tk(before);
        String b = CookieUtils.extractMh5Tk(after);
        return a != null && a.equals(b);
    }

    /**
     * 简化 URL 编码（仅对 JSON 中的特殊字符）
     */
    private String urlEncode(String data) {
        try {
            return java.net.URLEncoder.encode(data, "UTF-8");
        } catch (Exception e) {
            return data;
        }
    }
}
