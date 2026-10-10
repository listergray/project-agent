package com.xianyu.auto.reply.engine;

import com.xianyu.auto.account.entity.Account;
import com.xianyu.auto.account.service.AccountService;
import com.xianyu.auto.message.service.ChatMessageService;
import com.xianyu.auto.reply.client.OpenAiCompatibleClient;
import com.xianyu.auto.reply.config.AiProperties;
import com.xianyu.auto.reply.config.ReplyProperties;
import com.xianyu.auto.reply.entity.KeywordRule;
import com.xianyu.auto.reply.service.AiContextService;
import com.xianyu.auto.reply.service.KeywordRuleService;
import com.xianyu.auto.reply.service.ReplySettingsService;
import com.xianyu.auto.xianyu.client.XianyuWsManager;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.context.ApplicationContext;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * ?????????????>??>??>ALL?? AI ?? ? ????
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class AutoReplyEngine {

    private final ReplySettingsService replySettingsService;
    private final KeywordRuleService keywordRuleService;
    private final AiContextService aiContextService;
    private final OpenAiCompatibleClient aiClient;
    private final AiProperties aiProperties;
    private final ReplyProperties replyProperties;
    private final AccountService accountService;
    private final ChatMessageService chatMessageService;
    private final ApplicationContext applicationContext;

    private final ExecutorService replyExecutor = Executors.newCachedThreadPool(r -> {
        Thread t = new Thread(r, "auto-reply");
        t.setDaemon(true);
        return t;
    });

    private XianyuWsManager getWsManager() {
        return applicationContext.getBean(XianyuWsManager.class);
    }

    /**
     * ????????????????????????
     */
    public void onBuyerMessage(Long accountId, String conversationId, String buyerId,
                               String buyerNick, String content, String itemId) {
        if (!replySettingsService.isReplyEnabled()) {
            return;
        }
        if (!StringUtils.hasText(content) || !StringUtils.hasText(conversationId)) {
            return;
        }
        Account account = accountService.getById(accountId);
        if (account == null || Account.STATUS_DISABLED.equals(account.getStatus())) {
            return;
        }

        replyExecutor.execute(() -> {
            try {
                process(account, conversationId, buyerId, buyerNick, content, itemId);
            } catch (Exception e) {
                log.error("?????? accountId={}, conv={}: {}",
                        accountId, conversationId, e.getMessage(), e);
            }
        });
    }

    private void process(Account account, String conversationId, String buyerId,
                         String buyerNick, String content, String itemId) throws InterruptedException {
        String reply = null;
        String source = null;

        KeywordRule rule = keywordRuleService.match(account.getId(), content, itemId);
        if (rule != null && StringUtils.hasText(rule.getReplyContent())) {
            reply = rule.getReplyContent().trim();
            source = "KEYWORD:" + rule.getMatchType() + "#" + rule.getId();
        }

        if (reply == null && replySettingsService.isAiEnabled()) {
            try {
                reply = generateAiReply(conversationId, content);
                source = "AI:" + replySettingsService.getAiProvider();
            } catch (Exception e) {
                log.warn("AI ???????????: {}", e.getMessage());
            }
        }

        if (reply == null) {
            String def = replySettingsService.getDefaultContent();
            if (StringUtils.hasText(def)) {
                reply = def.trim();
                source = "DEFAULT";
            }
        }

        if (!StringUtils.hasText(reply)) {
            log.debug("???????????/AI: accountId={}, content={}",
                    account.getId(), truncate(content, 40));
            return;
        }

        int delayMs = replyProperties.randomDelayMs();
        if (delayMs > 0) {
            Thread.sleep(delayMs);
        }

        String toBuyer = StringUtils.hasText(buyerId) ? buyerId : conversationId;
        boolean sent = getWsManager().sendChatMessage(
                account.getId(), conversationId, toBuyer, reply);
        if (sent) {
            chatMessageService.saveSentMessage(
                    account.getId(), conversationId, reply, account.getNickname(), itemId);
            log.info("???????: accountId={}, source={}, buyer={}, content={}",
                    account.getId(), source, buyerNick, truncate(reply, 60));
        } else {
            log.warn("????????: accountId={}, source={}, conv={}",
                    account.getId(), source, conversationId);
        }
    }

    private String generateAiReply(String conversationId, String userMessage) {
        int window = aiProperties.getContextWindow() == null ? 20 : aiProperties.getContextWindow();
        List<Map<String, String>> history = aiContextService.getHistory(conversationId, window);
        String answer = aiClient.chat(
                replySettingsService.getAiProvider(),
                replySettingsService.getAiSystemPrompt(),
                history,
                userMessage);
        if (StringUtils.hasText(answer)) {
            aiContextService.appendTurn(conversationId, userMessage, answer, window);
        }
        return answer;
    }

    private String truncate(String s, int max) {
        if (s == null) return null;
        return s.length() > max ? s.substring(0, max) + "..." : s;
    }
}
