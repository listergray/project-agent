package com.xianyu.auto.product.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;
import java.math.BigDecimal;

@Data
@TableName("t_product")
public class Product implements Serializable {

    public static final String STATUS_ENABLED = "ENABLED";
    public static final String STATUS_DISABLED = "DISABLED";

    public static final String SHELF_ON_SALE = "ON_SALE";
    public static final String SHELF_OFF = "OFF_SHELF";
    public static final String SHELF_DELETED = "DELETED";

    public static final String SYNC_LOCAL = "LOCAL";
    public static final String SYNC_OK = "SYNCED";
    public static final String SYNC_ERROR = "ERROR";

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long accountId;

    private String name;

    private String title;

    private String xianyuItemId;

    private String description;

    private BigDecimal price;

    private BigDecimal originalPrice;

    private Integer stockQty;

    private String shelfStatus;

    private String imagesJson;

    private String categoryId;

    private String province;

    private String city;

    private String deliveryContent;

    private Long defaultInventoryId;

    private Integer autoDelivery;

    private String status;

    private String syncStatus;

    private Long lastSyncedAt;

    private Long createdAt;

    private Long updatedAt;

    @TableLogic
    private Integer deleted;

    @TableField(exist = false)
    private Integer totalStock;

    @TableField(exist = false)
    private Integer usedCount;
}
