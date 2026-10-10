package com.xianyu.auto.delivery.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;

@Data
@TableName("t_delivery_rule")
public class DeliveryRule implements Serializable {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String name;

    private Long accountId;

    private Long productId;

    private String triggerType;

    private String triggerKeywords;

    private String deliveryContent;

    private Long inventoryId;

    /** 发送后是否调用确认发货 API：1=是 0=否 */
    private Integer autoConfirm;

    /** 发货前延时秒数 */
    private Integer delaySeconds;

    private Integer priority;

    private Integer enabled;

    private Long createdAt;

    private Long updatedAt;

    @TableLogic
    private Integer deleted;

    public static final String TRIGGER_KEYWORD = "KEYWORD";
    public static final String TRIGGER_ORDER = "ORDER";
    public static final String TRIGGER_ALL = "ALL";

    public boolean isAutoConfirmEnabled() {
        return autoConfirm == null || autoConfirm == 1;
    }

    public int delaySecondsOrZero() {
        return delaySeconds == null || delaySeconds < 0 ? 0 : delaySeconds;
    }
}
