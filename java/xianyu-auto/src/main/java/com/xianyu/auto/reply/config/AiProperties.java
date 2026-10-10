package com.xianyu.auto.reply.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Data
@Configuration
@ConfigurationProperties(prefix = "xianyu.ai")
public class AiProperties {

    private String defaultProvider = "dashscope";
    private Integer timeoutMs = 30000;
    private Integer retryCount = 2;
    private Integer contextWindow = 20;

    private Provider openai = new Provider();
    private Provider dashscope = new Provider();
    private Provider deepseek = new Provider();

    @Data
    public static class Provider {
        private String apiKey = "";
        private String baseUrl = "";
        private String model = "";
    }

    public Provider resolveProvider(String name) {
        String p = name == null || name.isBlank() ? defaultProvider : name.trim().toLowerCase();
        return switch (p) {
            case "openai" -> openai;
            case "deepseek" -> deepseek;
            default -> dashscope;
        };
    }

    public String resolveBaseUrl(String name) {
        String p = name == null || name.isBlank() ? defaultProvider : name.trim().toLowerCase();
        Provider provider = resolveProvider(p);
        if (provider.getBaseUrl() != null && !provider.getBaseUrl().isBlank()) {
            return trimSlash(provider.getBaseUrl());
        }
        return switch (p) {
            case "openai" -> "https://api.openai.com/v1";
            case "deepseek" -> "https://api.deepseek.com/v1";
            default -> "https://dashscope.aliyuncs.com/compatible-mode/v1";
        };
    }

    public String resolveModel(String name) {
        String p = name == null || name.isBlank() ? defaultProvider : name.trim().toLowerCase();
        Provider provider = resolveProvider(p);
        if (provider.getModel() != null && !provider.getModel().isBlank()) {
            return provider.getModel();
        }
        return switch (p) {
            case "openai" -> "gpt-4o-mini";
            case "deepseek" -> "deepseek-chat";
            default -> "qwen-plus";
        };
    }

    public boolean hasApiKey(String name) {
        Provider provider = resolveProvider(name);
        return provider.getApiKey() != null && !provider.getApiKey().isBlank();
    }

    private static String trimSlash(String url) {
        if (url.endsWith("/")) {
            return url.substring(0, url.length() - 1);
        }
        return url;
    }
}
