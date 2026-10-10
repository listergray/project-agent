package com.xianyu.auto.message.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;

/**
 * 聊天消息
 */
@Data
@TableName("t_chat_message")
public class ChatMessage implements Serializable {

    /** 发送方枚举 */
    public static final String SENDER_BUYER  = "BUYER";
    public static final String SENDER_SELLER = "SELLER";
    public static final String SENDER_SYSTEM = "SYSTEM";

    /** 消息类型枚举 */
    public static final String MSG_TYPE_TEXT   = "TEXT";
    public static final String MSG_TYPE_IMAGE  = "IMAGE";
    public static final String MSG_TYPE_ORDER  = "ORDER";
    public static final String MSG_TYPE_SYSTEM = "SYSTEM";

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 关联闲鱼账号 ID */
    private Long accountId;

    /** 会话 ID（通常是 buyer_id 或 buyer_id#item_id） */
    private String conversationId;

    /** 发送方：BUYER / SELLER / SYSTEM */
    private String sender;

    /** 发送方用户 ID */
    private String senderId;

    /** 发送方昵称 */
    private String senderNick;

    /** 关联商品 ID */
    private String itemId;

    /** 消息类型：TEXT / IMAGE / ORDER / SYSTEM */
    private String msgType;

    /** 消息内容 */
    private String content;

    /** 原始协议数据 JSON */
    private String rawData;

    /** 已读状态：0=未读 1=已读 */
    private Integer readStatus;

    /** 创建时间（毫秒戳） */
    private Long createdAt;

    @TableLogic
    private Integer deleted;
}
