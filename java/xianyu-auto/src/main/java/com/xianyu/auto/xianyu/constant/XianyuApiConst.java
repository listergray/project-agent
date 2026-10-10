package com.xianyu.auto.xianyu.constant;

/**
 * 闲鱼 API 协议常量
 * 集中管理闲鱼 WebSocket / MTOP HTTP 协议相关固定值。
 * 协议变更时只需修改本类。
 */
public final class XianyuApiConst {

    private XianyuApiConst() {}

    // ==================== MTOP 协议固定值 ====================

    /** MTOP AppKey（H5 API） */
    public static final String APP_KEY = "34839810";

    /** 闲鱼 IM AppKey（WebSocket 注册用） */
    public static final String IM_APP_KEY = "444e9908a51d1cb236a27862abc769c9";

    /** WebSocket 服务地址 */
    public static final String WS_URL = "wss://wss-goofish.dingtalk.com/";

    /** H5 API 基础地址（含尾斜杠） */
    public static final String H5_API_BASE = "https://h5api.m.goofish.com/h5/";

    /** H5 页面 Referer */
    public static final String REFERER = "https://www.goofish.com/";

    /** 标准 PC 浏览器 UA */
    public static final String USER_AGENT =
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
            "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36";

    /** Cookie 中 _m_h5_tk 字段名 */
    public static final String COOKIE_MH5_TK = "_m_h5_tk";

    /** Cookie 中 _m_h5_tk_enc 字段名 */
    public static final String COOKIE_MH5_TK_ENC = "_m_h5_tk_enc";

    /** Cookie 中 unb 字段名（用户 ID） */
    public static final String COOKIE_UNB = "unb";

    /** Cookie 中 cookie2 字段名 */
    public static final String COOKIE_COOKIE2 = "cookie2";

    /** Cookie 中 _tb_token_ 字段名 */
    public static final String COOKIE_TB_TOKEN = "_tb_token_";

    // ==================== MTOP API 名称 ====================

    /** 获取 WS Token（登录令牌） */
    public static final String API_LOGIN_TOKEN = "mtop.taobao.idlemessage.pc.login.token";

    /**
     * 登录态校验（保活）。
     * 旧接口 mtop.taobao.idle.user.login.check 已下线（FAIL_SYS_API_NOT_FOUNDED），
     * 改用 getUserNav。
     */
    public static final String API_HAS_LOGIN = "mtop.user.getUserNav";

    /** IM 侧用户信息（备选保活） */
    public static final String API_LOGIN_USER_GET = "mtop.taobao.idlemessage.pc.loginuser.get";

    /** 商品详情 */
    public static final String API_ITEM_DETAIL = "mtop.taobao.idle.pc.detail";

    /**
     * 卖家商品列表（个人主页/闲鱼号）。
     * 旧名 mtop.taobao.idle.xyh.item.list 在 H5 入口已返回
     * FAIL_SYS_UNAUTHORIZED_ENTERANCE，改用网页端现行接口。
     */
    public static final String API_SELLER_ITEM_LIST = "mtop.idle.web.xyh.item.list";

    /** PC 发布商品 */
    public static final String API_ITEM_PUBLISH = "mtop.idle.pc.idleitem.publish";

    /** 下架/删除商品（以实际抓包为准，常见为 edit/down） */
    public static final String API_ITEM_DOWN = "mtop.idle.pc.idleitem.downshelf";

    /** 上架 */
    public static final String API_ITEM_UP = "mtop.idle.pc.idleitem.upshelf";

    /**
     * 虚拟商品确认发货（无需物流）。
     * 旧名 mtop.taobao.idle.pc.trade.consignment 已返回 API_NOT_FOUNDED。
     */
    public static final String API_TRADE_CONSIGNMENT = "mtop.taobao.idle.logistic.consign.dummy";

    /** 卖家已售订单列表 */
    public static final String API_TRADE_SOLD = "mtop.taobao.idle.trade.sold.query";

    /** 同步消息 */
    public static final String API_SYNC_MESSAGE = "mtop.taobao.idlemessage.pc.sync.message";

    // ==================== LWP 协议路径 ====================

    /** 注册包 */
    public static final String LWP_REG = "/reg";

    /** 请求路径前缀 */
    public static final String LWP_REQUEST_PREFIX = "/r/";

    /** 推送路径前缀 */
    public static final String LWP_PUSH_PREFIX = "/p/";

    /** 心跳路径 */
    public static final String LWP_HEARTBEAT = "/!";

    /** 同步状态 ackDiff */
    public static final String LWP_SYNC_STATUS = "/r/SyncStatus/ackDiff";

    /** 发送聊天消息（旧路径，保留兼容） */
    public static final String LWP_MESSAGE_SEND = "/r/MessageSend";

    /** 按接收者范围发送聊天消息（真实协议路径） */
    public static final String LWP_MESSAGE_SEND_BY_SCOPE = "/r/MessageSend/sendByReceiverScope";

    /** 接收消息推送 */
    public static final String LWP_MESSAGE_RECEIVE = "/p/Message";

    /** 同步推送（含聊天/订单系统消息） */
    public static final String LWP_SYNC = "/s/sync";

    /** 闲鱼 IM 域名后缀 */
    public static final String GOOFISH_SUFFIX = "@goofish";

    /** PC Web IM UA（注册包 headers） */
    public static final String IM_UA =
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 " +
            "(KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36 DingTalk(2.1.5) " +
            "OS(Windows/10) Browser(Chrome/133.0.0.0) DingWeb/2.1.5 IMPaaS DingWeb/2.1.5";

    // ==================== 错误码 ====================

    /** 滑块验证错误码 */
    public static final String ERROR_RGV587 = "RGV587_ERROR";
}
