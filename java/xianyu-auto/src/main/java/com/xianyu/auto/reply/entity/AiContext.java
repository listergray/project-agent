package com.xianyu.auto.reply.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;

@Data
@TableName("t_ai_context")
public class AiContext implements Serializable {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String conversationId;

    private String historyJson;

    private Integer tokenCount;

    private Long updatedAt;
}
