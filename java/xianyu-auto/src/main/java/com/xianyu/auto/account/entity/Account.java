package com.xianyu.auto.account.entity;

import com.baomidou.mybatisplus.annotation.FieldStrategy;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.baomidou.mybatisplus.annotation.TableField;
import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Data;

import java.io.Serializable;

/**
 * 闲鱼账号
 * Cookie 字段 AES 加密后存储，永不返回前端
 */
@Data
@TableName("t_account")
public class Account implements Serializable {

    /** 状态枚举（与 status 字段对应） */
    public static final String STATUS_DISABLED     = "DISABLED";      // 已禁用
    public static final String STATUS_OFFLINE      = "OFFLINE";       // 离线
    public static final String STATUS_CONNECTING   = "CONNECTING";    // 连接中
    public static final String STATUS_ONLINE       = "ONLINE";        // 在线
    public static final String STATUS_ERROR        = "ERROR";         // 错误
    public static final String STATUS_NEED_VERIFY  = "NEED_VERIFY";   // 需滑块验证
    public static final String STATUS_EXPIRED      = "EXPIRED";       // Cookie 失效

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 备注 */
    private String nickname;

    /** 闲鱼用户 ID */
    private String userId;

    /** 闲鱼用户昵称 */
    private String userNick;

    /** 头像 URL */
    private String avatar;

    /** AES 加密的 Cookie 字符串 */
    @JsonIgnore
    private String cookieText;

    /** 设备 ID（32 hex） */
    private String deviceId;

    /** WebSocket 注册 token */
    @JsonIgnore
    private String wsToken;

    /** WS Token 过期时间（毫秒戳） */
    @JsonIgnore
    private Long wsTokenExpireAt;

    /** OAuth2.0 Access Token（开放平台） */
    @JsonIgnore
    private String accessToken;

    /** OAuth2.0 Refresh Token（开放平台） */
    @JsonIgnore
    private String refreshToken;

    /** Access Token 过期时间（毫秒戳） */
    private Long accessTokenExpireAt;

    /** Refresh Token 过期时间（毫秒戳） */
    private Long refreshTokenExpireAt;

    /** 授权类型：COOKIE / OAUTH2 */
    private String authType;

    /** 当前状态 */
    private String status;

    /** 最后错误信息（允许更新为 null 以清除残留） */
    @TableField(updateStrategy = FieldStrategy.ALWAYS)
    private String lastError;

    /** 最后登录时间（毫秒戳） */
    private Long lastLoginAt;

    /** 最后保活时间（毫秒戳） */
    private Long lastKeepaliveAt;

    /** 启动时是否自动连接 */
    private Integer autoStart;

    private Long createdAt;
    private Long updatedAt;

    /** 逻辑删除字段，不返回前端 */
    @JsonIgnore
    @TableField("deleted")
    private Integer deleted;

    /**
     * 判断是否处于连接中状态
     */
    public boolean isActive() {
        return STATUS_CONNECTING.equals(status) || STATUS_ONLINE.equals(status);
    }

    /**
     * 是否可启动连接（必须满足：未禁用、Cookie 已录入）
     */
    public boolean canConnect() {
        return !STATUS_DISABLED.equals(status) && cookieText != null && !cookieText.isEmpty();
    }
}
