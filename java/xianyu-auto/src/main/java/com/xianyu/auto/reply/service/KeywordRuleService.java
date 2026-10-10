package com.xianyu.auto.reply.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.xianyu.auto.reply.entity.KeywordRule;
import com.xianyu.auto.reply.mapper.KeywordRuleMapper;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.Comparator;
import java.util.List;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

@Service
public class KeywordRuleService extends ServiceImpl<KeywordRuleMapper, KeywordRule> {

    /**
     * ???? + ??????????????
     */
    public KeywordRule match(Long accountId, String content, String itemId) {
        if (accountId == null || !StringUtils.hasText(content)) {
            return null;
        }
        List<KeywordRule> rules = list(new LambdaQueryWrapper<KeywordRule>()
                .eq(KeywordRule::getAccountId, accountId)
                .eq(KeywordRule::getStatus, KeywordRule.STATUS_ENABLED)
                .orderByDesc(KeywordRule::getPriority)
                .orderByDesc(KeywordRule::getId));

        if (rules.isEmpty()) {
            return null;
        }

        String text = content.trim();
        return rules.stream()
                .filter(r -> matchesItem(r, itemId))
                .filter(r -> matchesContent(r, text))
                .sorted(Comparator
                        .comparing((KeywordRule r) -> r.getPriority() == null ? 0 : r.getPriority()).reversed()
                        .thenComparing(KeywordRule::matchRank, Comparator.reverseOrder())
                        .thenComparing(r -> r.getId() == null ? 0L : r.getId(), Comparator.reverseOrder()))
                .findFirst()
                .orElse(null);
    }

    public List<KeywordRule> listByAccount(Long accountId) {
        LambdaQueryWrapper<KeywordRule> wrapper = new LambdaQueryWrapper<>();
        if (accountId != null) {
            wrapper.eq(KeywordRule::getAccountId, accountId);
        }
        wrapper.orderByDesc(KeywordRule::getPriority).orderByDesc(KeywordRule::getCreatedAt);
        return list(wrapper);
    }

    private boolean matchesItem(KeywordRule rule, String itemId) {
        if (!StringUtils.hasText(rule.getItemId())) {
            return true;
        }
        return StringUtils.hasText(itemId) && rule.getItemId().equals(itemId);
    }

    private boolean matchesContent(KeywordRule rule, String text) {
        String type = rule.getMatchType() == null ? KeywordRule.MATCH_CONTAINS : rule.getMatchType().toUpperCase();
        String keyword = rule.getKeyword() == null ? "" : rule.getKeyword().trim();
        return switch (type) {
            case KeywordRule.MATCH_ALL -> true;
            case KeywordRule.MATCH_EXACT -> text.equalsIgnoreCase(keyword);
            case KeywordRule.MATCH_REGEX -> {
                if (!StringUtils.hasText(keyword)) {
                    yield false;
                }
                try {
                    yield Pattern.compile(keyword, Pattern.CASE_INSENSITIVE | Pattern.DOTALL)
                            .matcher(text).find();
                } catch (Exception e) {
                    yield false;
                }
            }
            default -> {
                // CONTAINS??????????????????
                if (!StringUtils.hasText(keyword)) {
                    yield false;
                }
                String lower = text.toLowerCase();
                for (String part : keyword.split("[,?]")) {
                    String p = part.trim().toLowerCase();
                    if (!p.isEmpty() && lower.contains(p)) {
                        yield true;
                    }
                }
                yield false;
            }
        };
    }

    /** ???/?????????? */
    public List<KeywordRule> listCandidates(Long accountId, String itemId) {
        return listByAccount(accountId).stream()
                .filter(KeywordRule::isEnabled)
                .filter(r -> matchesItem(r, itemId))
                .collect(Collectors.toList());
    }
}
