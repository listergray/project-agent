package com.xianyu.auto.reply.service;

import com.xianyu.auto.reply.config.AiProperties;
import com.xianyu.auto.reply.config.ReplyProperties;
import com.xianyu.auto.system.entity.SysConfig;
import com.xianyu.auto.system.service.SysConfigService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * ??????????DB ??????? application.yml / .env?
 */
@Service
@RequiredArgsConstructor
public class ReplySettingsService {

    public static final String GROUP = "reply";

    public static final String KEY_ENABLED = "reply.enabled";
    public static final String KEY_DEFAULT_CONTENT = "reply.default_content";
    public static final String KEY_AI_ENABLED = "reply.ai_enabled";
    public static final String KEY_AI_PROVIDER = "reply.ai_provider";
    public static final String KEY_AI_SYSTEM_PROMPT = "reply.ai_system_prompt";

    private static final String DEFAULT_SYSTEM_PROMPT =
            "?????????????????????????????"
                    + "??????????????????/??????????????????"
                    + "????? 120 ????";

    private final SysConfigService sysConfigService;
    private final AiProperties aiProperties;
    private final ReplyProperties replyProperties;

    public boolean isReplyEnabled() {
        return parseBool(sysConfigService.getConfigValue(KEY_ENABLED, "true"), true);
    }

    public boolean isAiEnabled() {
        return parseBool(sysConfigService.getConfigValue(KEY_AI_ENABLED, "false"), false);
    }

    public String getDefaultContent() {
        return sysConfigService.getConfigValue(KEY_DEFAULT_CONTENT, "");
    }

    public String getAiProvider() {
        String v = sysConfigService.getConfigValue(KEY_AI_PROVIDER, "");
        return StringUtils.hasText(v) ? v : aiProperties.getDefaultProvider();
    }

    public String getAiSystemPrompt() {
        return sysConfigService.getConfigValue(KEY_AI_SYSTEM_PROMPT, DEFAULT_SYSTEM_PROMPT);
    }

    public Map<String, Object> getSettingsView() {
        Map<String, Object> map = new HashMap<>();
        map.put("enabled", isReplyEnabled());
        map.put("defaultContent", getDefaultContent());
        map.put("aiEnabled", isAiEnabled());
        map.put("aiProvider", getAiProvider());
        map.put("aiSystemPrompt", getAiSystemPrompt());
        map.put("delayMinSec", replyProperties.getDelayMinSec());
        map.put("delayMaxSec", replyProperties.getDelayMaxSec());
        map.put("contextWindow", aiProperties.getContextWindow());
        map.put("yamlDefaultProvider", aiProperties.getDefaultProvider());

        Map<String, Object> providers = new HashMap<>();
        providers.put("dashscope", providerStatus("dashscope"));
        providers.put("openai", providerStatus("openai"));
        providers.put("deepseek", providerStatus("deepseek"));
        map.put("providers", providers);
        return map;
    }

    public void saveSettings(Map<String, Object> body) {
        if (body == null) return;
        List<SysConfig> configs = new ArrayList<>();
        put(configs, KEY_ENABLED, body.get("enabled"), "???????");
        put(configs, KEY_DEFAULT_CONTENT, body.get("defaultContent"), "???/AI ??????");
        put(configs, KEY_AI_ENABLED, body.get("aiEnabled"), "AI ????");
        put(configs, KEY_AI_PROVIDER, body.get("aiProvider"), "AI ???");
        put(configs, KEY_AI_SYSTEM_PROMPT, body.get("aiSystemPrompt"), "AI ?????");
        for (SysConfig c : configs) {
            c.setConfigGroup(GROUP);
        }
        sysConfigService.saveOrUpdate(configs);
    }

    private Map<String, Object> providerStatus(String name) {
        Map<String, Object> m = new HashMap<>();
        m.put("configured", aiProperties.hasApiKey(name));
        m.put("model", aiProperties.resolveModel(name));
        m.put("baseUrl", aiProperties.resolveBaseUrl(name));
        return m;
    }

    private void put(List<SysConfig> list, String key, Object value, String desc) {
        if (value == null) return;
        SysConfig c = new SysConfig();
        c.setConfigKey(key);
        c.setConfigValue(String.valueOf(value));
        c.setDescription(desc);
        list.add(c);
    }

    private boolean parseBool(String v, boolean def) {
        if (!StringUtils.hasText(v)) return def;
        return "1".equals(v) || "true".equalsIgnoreCase(v) || "yes".equalsIgnoreCase(v);
    }
}
