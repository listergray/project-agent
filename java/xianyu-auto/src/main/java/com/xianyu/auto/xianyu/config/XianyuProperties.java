package com.xianyu.auto.xianyu.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

/**
 * 闲鱼集成配置（绑定 application.yml 中 xianyu.xianyu.* 节点）
 */
@Data
@Configuration
@ConfigurationProperties(prefix = "xianyu.xianyu")
public class XianyuProperties {

    /** MTOP AppKey（H5 API） */
    private String appKey = "34839810";

    /** 开放平台 AppKey（OAuth2.0） */
    private String openAppKey;

    /** 开放平台 AppSecret（OAuth2.0） */
    private String openAppSecret;

    /** OAuth2.0 回调地址 */
    private String oauthCallbackUrl;

    /**
     * 离线账号轻量保活间隔（分钟）。ONLINE 账号跳过 HTTP。
     * 实际调度会加 ±20% 抖动与账号错峰。
     */
    private Integer cookieKeepaliveMin = 360;

    /** _m_h5_tk 刷新下限（小时，兼容旧配置；已并入离线保活） */
    private Double mh5tkRefreshMinHours = 6.0;

    /** _m_h5_tk 刷新上限（小时） */
    private Double mh5tkRefreshMaxHours = 12.0;

    /** WS Token 无过期信息时的刷新下限（小时） */
    private Double wsTokenRefreshMinHours = 20.0;

    /** WS Token 无过期信息时的刷新上限（小时） */
    private Double wsTokenRefreshMaxHours = 22.0;

    /** 心跳间隔（秒） */
    private Integer heartbeatIntervalSec = 20;

    /** 心跳超时（秒） */
    private Integer heartbeatTimeoutSec = 30;

    /**
     * 计算下次 _m_h5_tk 刷新的延迟（毫秒）
     */
    public long nextMh5TkRefreshDelayMs() {
        double minMs = mh5tkRefreshMinHours * 3600_000L;
        double maxMs = mh5tkRefreshMaxHours * 3600_000L;
        double delta = maxMs - minMs;
        return (long) (minMs + Math.random() * delta);
    }

    /**
     * 计算下次 WS Token 刷新的延迟（毫秒）
     */
    public long nextWsTokenRefreshDelayMs() {
        double minMs = wsTokenRefreshMinHours * 3600_000L;
        double maxMs = wsTokenRefreshMaxHours * 3600_000L;
        double delta = maxMs - minMs;
        return (long) (minMs + Math.random() * delta);
    }

    /**
     * Cookie 保活间隔（毫秒）
     */
    public long cookieKeepaliveMs() {
        return cookieKeepaliveMin * 60_000L;
    }
}
