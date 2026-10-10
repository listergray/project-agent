package com.xianyu.auto.reply.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;

@Data
@TableName("t_keyword_rule")
public class KeywordRule implements Serializable {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Long accountId;

    /** ???????????? ID */
    private String itemId;

    private String keyword;

    /** EXACT / CONTAINS / REGEX / ALL */
    private String matchType;

    private String replyContent;

    private Integer priority;

    /** ENABLED / DISABLED */
    private String status;

    private Long createdAt;

    private Long updatedAt;

    @TableLogic
    private Integer deleted;

    public static final String MATCH_EXACT = "EXACT";
    public static final String MATCH_CONTAINS = "CONTAINS";
    public static final String MATCH_REGEX = "REGEX";
    public static final String MATCH_ALL = "ALL";

    public static final String STATUS_ENABLED = "ENABLED";
    public static final String STATUS_DISABLED = "DISABLED";

    public boolean isEnabled() {
        return STATUS_ENABLED.equalsIgnoreCase(status);
    }

    public int matchRank() {
        if (matchType == null) return 50;
        return switch (matchType.toUpperCase()) {
            case MATCH_EXACT -> 100;
            case MATCH_CONTAINS -> 80;
            case MATCH_REGEX -> 60;
            case MATCH_ALL -> 10;
            default -> 50;
        };
    }
}
