package cn.iocoder.yudao.module.projectagent.dal.dataobject;

import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 项目库 · 立项单（芋道 DataObject）。
 * 表名建议：project_agent_project
 */
@TableName("project_agent_project")
@Data
public class ProjectDO {

    @TableId
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
    /** draft / pending / approved / rejected */
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
