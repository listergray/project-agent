package com.xianyu.auto.delivery.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.xianyu.auto.delivery.entity.DeliveryRule;
import com.xianyu.auto.delivery.mapper.DeliveryRuleMapper;
import com.xianyu.auto.delivery.service.DeliveryRuleService;
import com.xianyu.auto.product.entity.Product;
import com.xianyu.auto.product.service.ProductService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class DeliveryRuleServiceImpl extends ServiceImpl<DeliveryRuleMapper, DeliveryRule> implements DeliveryRuleService {

    private final ProductService productService;

    @Override
    public List<DeliveryRule> matchRules(Long accountId, String content, String itemId, boolean paidEvent) {
        List<DeliveryRule> enabledRules = this.list(new LambdaQueryWrapper<DeliveryRule>()
                .eq(DeliveryRule::getEnabled, 1)
                .and(w -> w.isNull(DeliveryRule::getAccountId).or().eq(DeliveryRule::getAccountId, accountId))
                .orderByDesc(DeliveryRule::getPriority));

        List<DeliveryRule> matched = new ArrayList<>();
        Long productId = resolveProductId(itemId);

        for (DeliveryRule rule : enabledRules) {
            boolean matchedRule = false;

            if (DeliveryRule.TRIGGER_ORDER.equals(rule.getTriggerType())) {
                // ORDER 仅在付款事件触发
                if (paidEvent && itemId != null && !itemId.isEmpty()) {
                    if (rule.getProductId() == null || rule.getProductId().equals(productId)) {
                        matchedRule = true;
                    }
                } else if (paidEvent && rule.getProductId() == null) {
                    // 付款事件但无 itemId：允许通用 ORDER 规则
                    matchedRule = true;
                }
            } else if (DeliveryRule.TRIGGER_KEYWORD.equals(rule.getTriggerType())) {
                if (content != null && rule.getTriggerKeywords() != null) {
                    String[] keywords = rule.getTriggerKeywords().split(",");
                    for (String keyword : keywords) {
                        String kw = keyword.trim();
                        if (!kw.isEmpty() && content.contains(kw)) {
                            matchedRule = true;
                            break;
                        }
                    }
                }
            } else if (DeliveryRule.TRIGGER_ALL.equals(rule.getTriggerType())) {
                // ALL 仅对普通消息；付款事件优先走 ORDER，避免重复
                matchedRule = !paidEvent;
            }

            if (matchedRule) {
                matched.add(rule);
                log.debug("Rule {} matched paidEvent={} account={} content={}",
                        rule.getName(), paidEvent, accountId, content);
            }
        }

        return matched;
    }

    private Long resolveProductId(String itemId) {
        if (itemId == null || itemId.isEmpty()) return null;
        Product product = productService.getByXianyuItemId(itemId);
        return product != null ? product.getId() : null;
    }
}
