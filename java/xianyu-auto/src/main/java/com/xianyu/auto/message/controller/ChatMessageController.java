package com.xianyu.auto.message.controller;

import com.xianyu.auto.account.service.AccountService;
import com.xianyu.auto.common.api.CommonResult;
import com.xianyu.auto.common.api.PageParam;
import com.xianyu.auto.common.api.PageResult;
import com.xianyu.auto.common.exception.BusinessException;
import com.xianyu.auto.message.entity.ChatMessage;
import com.xianyu.auto.message.service.ChatMessageService;
import com.xianyu.auto.xianyu.client.XianyuWsManager;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 聊天消息管理
 */
@Slf4j
@RestController
@RequestMapping("/api/message")
@RequiredArgsConstructor
public class ChatMessageController {

    private final ChatMessageService chatMessageService;
    private final AccountService accountService;
    private final XianyuWsManager wsManager;

    /**
     * 分页查询消息
     */
    @GetMapping("/page")
    public CommonResult<PageResult<ChatMessage>> page(PageParam page,
                                                      @RequestParam(required = false) Long accountId,
                                                      @RequestParam(required = false) String conversationId,
                                                      @RequestParam(required = false) Long startTime,
                                                      @RequestParam(required = false) Long endTime) {
        return CommonResult.success(chatMessageService.page(
                page.getPageNo(), page.getPageSize(), accountId, conversationId, startTime, endTime));
    }

    /**
     * 查询某账号的会话列表
     */
    @GetMapping("/conversations/{accountId}")
    public CommonResult<List<Map<String, Object>>> conversations(@PathVariable Long accountId) {
        return CommonResult.success(chatMessageService.listConversations(accountId));
    }

    /**
     * 标记会话已读
     */
    @PutMapping("/read/{accountId}")
    public CommonResult<Void> markRead(@PathVariable Long accountId,
                                      @RequestParam String conversationId) {
        chatMessageService.markRead(accountId, conversationId);
        return CommonResult.success("标记成功", null);
    }

    /**
     * 手动发送消息
     * Body: { "accountId", "conversationId", "content", "buyerId"(可选), "itemId"(可选) }
     */
    @PostMapping("/send")
    public CommonResult<Void> send(@RequestBody Map<String, String> body) {
        Long accountId = parseLong(body.get("accountId"));
        String conversationId = body.get("conversationId");
        String content = body.get("content");
        String itemId = body.get("itemId");
        String buyerId = body.get("buyerId");
        if (accountId == null || conversationId == null || content == null) {
            throw new BusinessException("accountId / conversationId / content 不能为空");
        }
        if (!wsManager.isAccountOnline(accountId)) {
            throw new BusinessException("账号未连接，无法发送消息");
        }
        if (buyerId == null || buyerId.isEmpty()) {
            buyerId = resolveBuyerId(accountId, conversationId);
        }
        if (buyerId == null || buyerId.isEmpty()) {
            buyerId = conversationId;
        }
        boolean sent = wsManager.sendChatMessage(accountId, conversationId, buyerId, content);
        if (!sent) {
            throw new BusinessException("发送失败，请查看日志");
        }
        String senderNick = accountService.getById(accountId).getUserNick();
        chatMessageService.saveSentMessage(accountId, conversationId, content, senderNick, itemId);
        return CommonResult.success("发送成功", null);
    }

    /** 从最近买家消息推断 buyerId */
    private String resolveBuyerId(Long accountId, String conversationId) {
        var page = chatMessageService.page(1, 20, accountId, conversationId, null, null);
        if (page == null || page.getList() == null) return null;
        for (int i = page.getList().size() - 1; i >= 0; i--) {
            ChatMessage msg = page.getList().get(i);
            if (ChatMessage.SENDER_BUYER.equals(msg.getSender())
                    && msg.getSenderId() != null && !msg.getSenderId().isEmpty()) {
                return msg.getSenderId();
            }
        }
        return null;
    }

    private Long parseLong(String s) {
        if (s == null || s.isEmpty()) return null;
        try {
            return Long.parseLong(s);
        } catch (NumberFormatException e) {
            return null;
        }
    }
}
