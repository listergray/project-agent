package com.xianyu.auto.delivery.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;

@Data
@TableName("t_delivery_log")
public class DeliveryLog implements Serializable {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long accountId;

    private String accountNickname;

    private Long ruleId;

    private String ruleName;

    private String conversationId;

    private String buyerId;

    private String buyerNick;

    private String itemId;

    private String itemName;

    /** 闲鱼订单 ID（幂等键） */
    private String orderId;

    private String deliveryContent;

    private String inventoryCode;

    private Long inventoryId;

    /** 确认发货状态 */
    private String consignStatus;

    private String status;

    private String errorMsg;

    private Long createdAt;

    private Long updatedAt;

    @TableLogic
    private Integer deleted;

    public static final String STATUS_SUCCESS = "SUCCESS";
    public static final String STATUS_FAILED = "FAILED";
    public static final String STATUS_PENDING = "PENDING";

    public static final String CONSIGN_SUCCESS = "SUCCESS";
    public static final String CONSIGN_FAILED = "FAILED";
    public static final String CONSIGN_SKIPPED = "SKIPPED";
}
