package com.xianyu.auto.delivery.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.xianyu.auto.delivery.entity.DeliveryRule;

import java.util.List;

public interface DeliveryRuleService extends IService<DeliveryRule> {

    /**
     * @param paidEvent true=付款事件，可匹配 ORDER；false=普通消息，仅 KEYWORD/ALL
     */
    List<DeliveryRule> matchRules(Long accountId, String content, String itemId, boolean paidEvent);

    /** 兼容旧调用：按普通消息匹配 */
    default List<DeliveryRule> matchRules(Long accountId, String content, String itemId) {
        return matchRules(accountId, content, itemId, false);
    }
}
