package com.xianyu.auto.system.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;

/**
 * 操作日志
 */
@Data
@TableName("t_sys_log")
public class SysLog implements Serializable {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String operator;
    private String action;
    private String method;
    private String params;
    private String result;
    private String ip;
    private Long durationMs;
    private String errorMsg;
    private Long createdAt;

    @TableLogic
    private Integer deleted;
}
