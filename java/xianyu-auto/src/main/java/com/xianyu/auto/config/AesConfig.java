package com.xianyu.auto.config;

import com.xianyu.auto.common.util.AesUtils;
import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * 加密配置
 */
@Configuration
@ConfigurationProperties(prefix = "xianyu")
@Data
public class AesConfig {

    private String encryptKey;
    private String defaultAdminPassword;

    @Bean
    public AesUtils aesUtils() {
        return new AesUtils(encryptKey);
    }
}
