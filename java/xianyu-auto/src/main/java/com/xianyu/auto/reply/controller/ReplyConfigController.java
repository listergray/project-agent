package com.xianyu.auto.reply.controller;

import com.xianyu.auto.common.api.CommonResult;
import com.xianyu.auto.common.exception.BusinessException;
import com.xianyu.auto.reply.client.OpenAiCompatibleClient;
import com.xianyu.auto.reply.service.AiContextService;
import com.xianyu.auto.reply.service.ReplySettingsService;
import lombok.RequiredArgsConstructor;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.*;

import java.util.Collections;
import java.util.Map;

@RestController
@RequestMapping("/api/reply/config")
@RequiredArgsConstructor
public class ReplyConfigController {

    private final ReplySettingsService replySettingsService;
    private final OpenAiCompatibleClient aiClient;
    private final AiContextService aiContextService;

    @GetMapping
    public CommonResult<Map<String, Object>> get() {
        return CommonResult.success(replySettingsService.getSettingsView());
    }

    @PutMapping
    public CommonResult<Void> save(@RequestBody Map<String, Object> body) {
        replySettingsService.saveSettings(body);
        return CommonResult.success();
    }

    /** ?? AI ??????????? */
    @PostMapping("/ai/test")
    public CommonResult<Map<String, String>> testAi(@RequestBody Map<String, String> body) {
        String prompt = body == null ? null : body.get("prompt");
        if (!StringUtils.hasText(prompt)) {
            prompt = "?????????";
        }
        try {
            String answer = aiClient.chat(
                    replySettingsService.getAiProvider(),
                    replySettingsService.getAiSystemPrompt(),
                    Collections.emptyList(),
                    prompt);
            return CommonResult.success(Map.of("answer", answer == null ? "" : answer));
        } catch (Exception e) {
            throw new BusinessException("AI ????: " + e.getMessage());
        }
    }

    @DeleteMapping("/ai/context")
    public CommonResult<Void> clearContext(@RequestParam String conversationId) {
        aiContextService.clear(conversationId);
        return CommonResult.success();
    }
}
