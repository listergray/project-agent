package com.xianyu.auto.xianyu.oauth2;

import lombok.Builder;
import lombok.Data;

/**
 * OAuth2.0 Token 模型
 */
@Data
@Builder
public class OAuth2Token {

    /** Access Token */
    private String accessToken;

    /** Refresh Token */
    private String refreshToken;

    /** Access Token 过期时间（毫秒戳） */
    private Long accessTokenExpireAt;

    /** Refresh Token 过期时间（毫秒戳） */
    private Long refreshTokenExpireAt;
}
