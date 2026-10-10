package com.xianyu.auto.reply.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.fasterxml.jackson.core.type.TypeReference;
import com.xianyu.auto.common.util.DateUtils;
import com.xianyu.auto.common.util.JsonUtils;
import com.xianyu.auto.reply.entity.AiContext;
import com.xianyu.auto.reply.mapper.AiContextMapper;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class AiContextService extends ServiceImpl<AiContextMapper, AiContext> {

    public List<Map<String, String>> getHistory(String conversationId, int maxMessages) {
        if (!StringUtils.hasText(conversationId)) {
            return new ArrayList<>();
        }
        AiContext ctx = getOne(new LambdaQueryWrapper<AiContext>()
                .eq(AiContext::getConversationId, conversationId)
                .last("LIMIT 1"));
        if (ctx == null || !StringUtils.hasText(ctx.getHistoryJson())) {
            return new ArrayList<>();
        }
        List<Map<String, String>> history = JsonUtils.fromJson(
                ctx.getHistoryJson(), new TypeReference<List<Map<String, String>>>() {});
        if (history == null) {
            return new ArrayList<>();
        }
        if (maxMessages > 0 && history.size() > maxMessages) {
            return new ArrayList<>(history.subList(history.size() - maxMessages, history.size()));
        }
        return history;
    }

    public void appendTurn(String conversationId, String userText, String assistantText, int maxMessages) {
        if (!StringUtils.hasText(conversationId)) {
            return;
        }
        List<Map<String, String>> history = getHistory(conversationId, 0);
        if (StringUtils.hasText(userText)) {
            history.add(msg("user", userText));
        }
        if (StringUtils.hasText(assistantText)) {
            history.add(msg("assistant", assistantText));
        }
        if (maxMessages > 0 && history.size() > maxMessages) {
            history = new ArrayList<>(history.subList(history.size() - maxMessages, history.size()));
        }
        AiContext ctx = getOne(new LambdaQueryWrapper<AiContext>()
                .eq(AiContext::getConversationId, conversationId)
                .last("LIMIT 1"));
        long now = DateUtils.nowMillis();
        String json = JsonUtils.toJson(history);
        if (ctx == null) {
            ctx = new AiContext();
            ctx.setConversationId(conversationId);
            ctx.setHistoryJson(json);
            ctx.setTokenCount(estimateTokens(json));
            ctx.setUpdatedAt(now);
            save(ctx);
        } else {
            ctx.setHistoryJson(json);
            ctx.setTokenCount(estimateTokens(json));
            ctx.setUpdatedAt(now);
            updateById(ctx);
        }
    }

    public void clear(String conversationId) {
        remove(new LambdaQueryWrapper<AiContext>().eq(AiContext::getConversationId, conversationId));
    }

    private Map<String, String> msg(String role, String content) {
        Map<String, String> m = new HashMap<>();
        m.put("role", role);
        m.put("content", content);
        return m;
    }

    private int estimateTokens(String json) {
        return json == null ? 0 : Math.max(1, json.length() / 4);
    }
}
