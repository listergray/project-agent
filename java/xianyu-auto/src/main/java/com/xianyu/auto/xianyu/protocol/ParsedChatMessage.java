package com.xianyu.auto.xianyu.protocol;

import lombok.Builder;
import lombok.Data;

/**
 * 从 syncPush MessagePack 解析出的标准化聊天/订单消息
 */
@Data
@Builder
public class ParsedChatMessage {

    private String conversationId;
    private String senderId;
    private String senderNick;
    private String content;
    private String itemId;
    private String orderId;
    private String msgType;
    private Long createTime;
    private boolean fromSelf;
    private boolean paidEvent;
    private boolean typingStatus;
    private boolean systemMessage;
    private String redReminder;
}
