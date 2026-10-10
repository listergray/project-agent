package com.xianyu.auto.reply.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.xianyu.auto.common.api.CommonResult;
import com.xianyu.auto.common.api.PageResult;
import com.xianyu.auto.common.exception.BusinessException;
import com.xianyu.auto.common.util.DateUtils;
import com.xianyu.auto.reply.entity.KeywordRule;
import com.xianyu.auto.reply.service.KeywordRuleService;
import lombok.RequiredArgsConstructor;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Set;

@RestController
@RequestMapping("/api/reply/keyword")
@RequiredArgsConstructor
public class KeywordRuleController {

    private static final Set<String> MATCH_TYPES = Set.of(
            KeywordRule.MATCH_EXACT,
            KeywordRule.MATCH_CONTAINS,
            KeywordRule.MATCH_REGEX,
            KeywordRule.MATCH_ALL
    );

    private final KeywordRuleService keywordRuleService;

    @GetMapping("/page")
    public CommonResult<PageResult<KeywordRule>> page(@RequestParam(defaultValue = "1") Integer pageNo,
                                                      @RequestParam(defaultValue = "20") Integer pageSize,
                                                      @RequestParam(required = false) String keyword,
                                                      @RequestParam(required = false) Long accountId,
                                                      @RequestParam(required = false) String matchType,
                                                      @RequestParam(required = false) String status) {
        LambdaQueryWrapper<KeywordRule> wrapper = new LambdaQueryWrapper<>();
        if (accountId != null) {
            wrapper.eq(KeywordRule::getAccountId, accountId);
        }
        if (StringUtils.hasText(keyword)) {
            wrapper.and(w -> w.like(KeywordRule::getKeyword, keyword)
                    .or().like(KeywordRule::getReplyContent, keyword));
        }
        if (StringUtils.hasText(matchType)) {
            wrapper.eq(KeywordRule::getMatchType, matchType);
        }
        if (StringUtils.hasText(status)) {
            wrapper.eq(KeywordRule::getStatus, status);
        }
        wrapper.orderByDesc(KeywordRule::getPriority).orderByDesc(KeywordRule::getCreatedAt);
        Page<KeywordRule> page = keywordRuleService.page(new Page<>(pageNo, pageSize), wrapper);
        return CommonResult.success(new PageResult<>(page.getRecords(), page.getTotal()));
    }

    @GetMapping("/list")
    public CommonResult<List<KeywordRule>> list(@RequestParam(required = false) Long accountId) {
        return CommonResult.success(keywordRuleService.listByAccount(accountId));
    }

    @GetMapping("/{id}")
    public CommonResult<KeywordRule> get(@PathVariable Long id) {
        return CommonResult.success(keywordRuleService.getById(id));
    }

    @PostMapping
    public CommonResult<Void> create(@RequestBody KeywordRule rule) {
        normalize(rule);
        long now = DateUtils.nowMillis();
        rule.setId(null);
        rule.setCreatedAt(now);
        rule.setUpdatedAt(now);
        keywordRuleService.save(rule);
        return CommonResult.success();
    }

    @PutMapping("/{id}")
    public CommonResult<Void> update(@PathVariable Long id, @RequestBody KeywordRule rule) {
        KeywordRule existing = keywordRuleService.getById(id);
        if (existing == null) {
            throw new BusinessException("?????");
        }
        normalize(rule);
        rule.setId(id);
        rule.setCreatedAt(existing.getCreatedAt());
        rule.setUpdatedAt(DateUtils.nowMillis());
        keywordRuleService.updateById(rule);
        return CommonResult.success();
    }

    @DeleteMapping("/{id}")
    public CommonResult<Void> delete(@PathVariable Long id) {
        keywordRuleService.removeById(id);
        return CommonResult.success();
    }

    @PutMapping("/{id}/status")
    public CommonResult<Void> updateStatus(@PathVariable Long id, @RequestParam String status) {
        if (!KeywordRule.STATUS_ENABLED.equals(status) && !KeywordRule.STATUS_DISABLED.equals(status)) {
            throw new BusinessException("????");
        }
        KeywordRule existing = keywordRuleService.getById(id);
        if (existing == null) {
            throw new BusinessException("?????");
        }
        existing.setStatus(status);
        existing.setUpdatedAt(DateUtils.nowMillis());
        keywordRuleService.updateById(existing);
        return CommonResult.success();
    }

    private void normalize(KeywordRule rule) {
        if (rule.getAccountId() == null) {
            throw new BusinessException("?????");
        }
        if (!StringUtils.hasText(rule.getMatchType())) {
            rule.setMatchType(KeywordRule.MATCH_CONTAINS);
        }
        String type = rule.getMatchType().toUpperCase();
        if (!MATCH_TYPES.contains(type)) {
            throw new BusinessException("????????: " + rule.getMatchType());
        }
        rule.setMatchType(type);
        if (!KeywordRule.MATCH_ALL.equals(type) && !StringUtils.hasText(rule.getKeyword())) {
            throw new BusinessException("??????");
        }
        if (KeywordRule.MATCH_ALL.equals(type) && !StringUtils.hasText(rule.getKeyword())) {
            rule.setKeyword("*");
        }
        if (!StringUtils.hasText(rule.getReplyContent())) {
            throw new BusinessException("???????");
        }
        if (rule.getPriority() == null) {
            rule.setPriority(100);
        }
        if (!StringUtils.hasText(rule.getStatus())) {
            rule.setStatus(KeywordRule.STATUS_ENABLED);
        }
        if (!StringUtils.hasText(rule.getItemId())) {
            rule.setItemId(null);
        }
    }
}
