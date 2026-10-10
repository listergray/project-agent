package com.xianyu.auto.reply.client;

import com.fasterxml.jackson.databind.JsonNode;
import com.xianyu.auto.common.exception.BusinessException;
import com.xianyu.auto.common.util.JsonUtils;
import com.xianyu.auto.reply.config.AiProperties;
import lombok.extern.slf4j.Slf4j;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

/**
 * OpenAI ?? Chat Completions?OpenAI / DashScope / DeepSeek?
 */
@Slf4j
@Component
public class OpenAiCompatibleClient {

    private static final MediaType JSON = MediaType.parse("application/json; charset=utf-8");

    private final AiProperties aiProperties;
    private final OkHttpClient httpClient;

    public OpenAiCompatibleClient(AiProperties aiProperties) {
        this.aiProperties = aiProperties;
        int timeout = aiProperties.getTimeoutMs() == null ? 30000 : aiProperties.getTimeoutMs();
        this.httpClient = new OkHttpClient.Builder()
                .connectTimeout(timeout, TimeUnit.MILLISECONDS)
                .readTimeout(timeout, TimeUnit.MILLISECONDS)
                .writeTimeout(timeout, TimeUnit.MILLISECONDS)
                .build();
    }

    public String chat(String provider, String systemPrompt, List<Map<String, String>> history, String userMessage) {
        String p = StringUtils.hasText(provider) ? provider : aiProperties.getDefaultProvider();
        AiProperties.Provider cfg = aiProperties.resolveProvider(p);
        if (!StringUtils.hasText(cfg.getApiKey())) {
            throw new BusinessException("AI ??? API Key?provider=" + p + "???? .env ???");
        }

        List<Map<String, String>> messages = new ArrayList<>();
        if (StringUtils.hasText(systemPrompt)) {
            messages.add(roleMsg("system", systemPrompt));
        }
        if (history != null) {
            messages.addAll(history);
        }
        messages.add(roleMsg("user", userMessage));

        Map<String, Object> body = new HashMap<>();
        body.put("model", aiProperties.resolveModel(p));
        body.put("messages", messages);
        body.put("temperature", 0.7);

        String url = aiProperties.resolveBaseUrl(p) + "/chat/completions";
        int retries = aiProperties.getRetryCount() == null ? 0 : Math.max(0, aiProperties.getRetryCount());
        Exception last = null;
        for (int i = 0; i <= retries; i++) {
            try {
                return doRequest(url, cfg.getApiKey(), body);
            } catch (Exception e) {
                last = e;
                log.warn("AI ???? provider={}, attempt={}/{}: {}", p, i + 1, retries + 1, e.getMessage());
            }
        }
        throw new BusinessException("AI ????: " + (last != null ? last.getMessage() : "unknown"));
    }

    private String doRequest(String url, String apiKey, Map<String, Object> body) throws IOException {
        Request request = new Request.Builder()
                .url(url)
                .header("Authorization", "Bearer " + apiKey)
                .header("Content-Type", "application/json")
                .post(RequestBody.create(JsonUtils.toJson(body), JSON))
                .build();
        try (Response response = httpClient.newCall(request).execute()) {
            String respBody = response.body() != null ? response.body().string() : "";
            if (!response.isSuccessful()) {
                throw new BusinessException("HTTP " + response.code() + ": " + truncate(respBody, 200));
            }
            JsonNode root = JsonUtils.fromJson(respBody, JsonNode.class);
            if (root == null) {
                throw new BusinessException("AI ??? JSON");
            }
            JsonNode content = root.path("choices").path(0).path("message").path("content");
            if (content.isMissingNode() || !StringUtils.hasText(content.asText())) {
                throw new BusinessException("AI ??? content: " + truncate(respBody, 200));
            }
            return content.asText().trim();
        }
    }

    private Map<String, String> roleMsg(String role, String content) {
        Map<String, String> m = new HashMap<>();
        m.put("role", role);
        m.put("content", content);
        return m;
    }

    private String truncate(String s, int max) {
        if (s == null) return "";
        return s.length() > max ? s.substring(0, max) + "..." : s;
    }
}
