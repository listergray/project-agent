package com.xianyu.auto.system.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableLogic;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Data;

import java.io.Serializable;

/**
 * 系统用户
 */
@Data
@TableName("t_sys_user")
public class SysUser implements Serializable {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String username;

    @JsonIgnore
    private String passwordHash;

    private String nickname;
    private String email;
    private String phone;
    private String role;
    private Integer status;
    private Long lastLoginAt;
    private String lastLoginIp;
    private Long createdAt;
    private Long updatedAt;

    @TableLogic
    @JsonIgnore
    private Integer deleted;
}
