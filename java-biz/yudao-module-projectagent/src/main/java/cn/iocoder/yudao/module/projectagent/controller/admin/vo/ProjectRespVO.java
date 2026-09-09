package cn.iocoder.yudao.module.projectagent.controller.admin.vo;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class ProjectRespVO {
    private String id;
    private String projectCode;
    private String projectName;
    private String projectType;
    private String owner;
    private String department;
    private String sponsor;
    private String startDate;
    private String endDate;
    private BigDecimal budget;
    private String priority;
    private String riskLevel;
    private String members;
    private String description;
    private String goals;
    private String sourceFile;
    private String remark;
    private String status;
    private String createdBy;
    private String reviewer;
    private String reviewComment;
    private String ragItemPk;
    private LocalDateTime submittedAt;
    private LocalDateTime reviewedAt;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}
