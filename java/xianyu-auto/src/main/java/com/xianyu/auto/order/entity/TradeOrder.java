package com.xianyu.auto.order.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;
import java.math.BigDecimal;

/**
 * 闲鱼订单（ERP 订单中心最小集）
 */
@Data
@TableName("t_order")
public class TradeOrder implements Serializable {

    public static final String STATUS_WAIT_PAY = "WAIT_PAY";
    public static final String STATUS_WAIT_SHIP = "WAIT_SHIP";
    public static final String STATUS_SHIPPED = "SHIPPED";
    public static final String STATUS_SUCCESS = "SUCCESS";
    public static final String STATUS_CLOSED = "CLOSED";

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long accountId;

    private String orderId;

    private String itemId;

    private String itemTitle;

    private String buyerId;

    private String buyerNick;

    private String conversationId;

    private String status;

    private BigDecimal payAmount;

    private Long paidAt;

    private Long shippedAt;

    private String consignStatus;

    private String rawJson;

    private Long createdAt;

    private Long updatedAt;

    @TableLogic
    private Integer deleted;
}
