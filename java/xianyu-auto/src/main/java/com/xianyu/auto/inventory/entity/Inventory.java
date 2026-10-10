package com.xianyu.auto.inventory.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;

@Data
@TableName("t_inventory")
public class Inventory implements Serializable {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String code;

    private String content;

    private String type;

    private Long productId;

    private Integer stock;

    private Integer usedCount;

    private String status;

    private Long createdAt;

    private Long updatedAt;

    @TableLogic
    private Integer deleted;

    @TableField(exist = false)
    private String productName;

    public static final String STATUS_AVAILABLE = "AVAILABLE";
    public static final String STATUS_USED = "USED";
    public static final String STATUS_DISABLED = "DISABLED";

    public static final String TYPE_CARD = "CARD";
    public static final String TYPE_LINK = "LINK";
    public static final String TYPE_TEXT = "TEXT";
}
