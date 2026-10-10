package com.xianyu.auto.message.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.xianyu.auto.common.api.PageResult;
import com.xianyu.auto.common.util.DateUtils;
import com.xianyu.auto.message.entity.ChatMessage;
import com.xianyu.auto.message.mapper.ChatMessageMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 聊天消息服务
 */
@Slf4j
@Service
public class ChatMessageService extends ServiceImpl<ChatMessageMapper, ChatMessage> {

    /**
     * 保存接收到的消息
     */
    public ChatMessage saveReceivedMessage(Long accountId, String conversationId, String sender,
                                           String senderId, String senderNick, String itemId,
                                           String msgType, String content, String rawData) {
        ChatMessage msg = new ChatMessage();
        msg.setAccountId(accountId);
        msg.setConversationId(conversationId);
        msg.setSender(sender);
        msg.setSenderId(senderId);
        msg.setSenderNick(senderNick);
        msg.setItemId(itemId);
        msg.setMsgType(StringUtils.hasText(msgType) ? msgType : ChatMessage.MSG_TYPE_TEXT);
        msg.setContent(content);
        msg.setRawData(rawData);
        msg.setReadStatus(0);
        msg.setCreatedAt(DateUtils.nowMillis());
        baseMapper.insert(msg);
        return msg;
    }

    /**
     * 保存发送的消息（手动回复或自动发货）
     */
    public ChatMessage saveSentMessage(Long accountId, String conversationId, String content,
                                       String senderNick, String itemId) {
        ChatMessage msg = new ChatMessage();
        msg.setAccountId(accountId);
        msg.setConversationId(conversationId);
        msg.setSender(ChatMessage.SENDER_SELLER);
        msg.setSenderNick(senderNick);
        msg.setItemId(itemId);
        msg.setMsgType(ChatMessage.MSG_TYPE_TEXT);
        msg.setContent(content);
        msg.setReadStatus(1);
        msg.setCreatedAt(DateUtils.nowMillis());
        baseMapper.insert(msg);
        return msg;
    }

    /**
     * 分页查询某会话的消息
     */
    public PageResult<ChatMessage> page(Integer pageNo, Integer pageSize, Long accountId,
                                       String conversationId, Long startTime, Long endTime) {
        Page<ChatMessage> page = new Page<>(pageNo, pageSize);
        LambdaQueryWrapper<ChatMessage> wrapper = new LambdaQueryWrapper<>();
        if (accountId != null) {
            wrapper.eq(ChatMessage::getAccountId, accountId);
        }
        if (StringUtils.hasText(conversationId)) {
            wrapper.eq(ChatMessage::getConversationId, conversationId);
        }
        if (startTime != null) {
            wrapper.ge(ChatMessage::getCreatedAt, startTime);
        }
        if (endTime != null) {
            wrapper.le(ChatMessage::getCreatedAt, endTime);
        }
        wrapper.orderByAsc(ChatMessage::getCreatedAt);
        IPage<ChatMessage> result = baseMapper.selectPage(page, wrapper);
        return new PageResult<>(result.getRecords(), result.getTotal());
    }

    /**
     * 会话列表（按 accountId 分组，每会话取最近一条消息）
     * SQLite 不支持窗口函数，简化实现：先 GROUP BY 取每会话的 max id，再 IN 查询
     */
    public List<Map<String, Object>> listConversations(Long accountId) {
        // 1. 查所有会话的最近一条消息 ID
        LambdaQueryWrapper<ChatMessage> wrapper = new LambdaQueryWrapper<>();
        if (accountId != null) {
            wrapper.eq(ChatMessage::getAccountId, accountId);
        }
        wrapper.orderByDesc(ChatMessage::getCreatedAt);
        List<ChatMessage> all = baseMapper.selectList(wrapper);

        // 2. 按 conversationId 分组取最新一条
        Map<String, ChatMessage> latestByConv = new HashMap<>();
        Map<String, Integer> unreadByConv = new HashMap<>();
        for (ChatMessage msg : all) {
            String conv = msg.getConversationId();
            if (conv == null) continue;
            if (!latestByConv.containsKey(conv)) {
                latestByConv.put(conv, msg);
            }
            if (ChatMessage.SENDER_BUYER.equals(msg.getSender()) && Integer.valueOf(0).equals(msg.getReadStatus())) {
                unreadByConv.merge(conv, 1, Integer::sum);
            }
        }

        // 3. 转换为 List<Map>
        List<Map<String, Object>> result = new ArrayList<>();
        for (Map.Entry<String, ChatMessage> entry : latestByConv.entrySet()) {
            ChatMessage latest = entry.getValue();
            Map<String, Object> conv = new HashMap<>();
            conv.put("conversationId", entry.getKey());
            conv.put("accountId", latest.getAccountId());
            conv.put("sender", latest.getSender());
            conv.put("senderId", latest.getSenderId());
            conv.put("senderNick", latest.getSenderNick());
            conv.put("itemId", latest.getItemId());
            conv.put("lastContent", latest.getContent());
            conv.put("lastMsgType", latest.getMsgType());
            conv.put("lastMsgAt", latest.getCreatedAt());
            conv.put("unreadCount", unreadByConv.getOrDefault(entry.getKey(), 0));
            result.add(conv);
        }
        return result;
    }

    /**
     * 标记会话所有消息为已读
     */
    public void markRead(Long accountId, String conversationId) {
        ChatMessage update = new ChatMessage();
        update.setReadStatus(1);
        baseMapper.update(update, new LambdaQueryWrapper<ChatMessage>()
                .eq(ChatMessage::getAccountId, accountId)
                .eq(ChatMessage::getConversationId, conversationId)
                .eq(ChatMessage::getReadStatus, 0));
    }
}
