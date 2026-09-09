package cn.iocoder.yudao.module.projectagent.controller.admin.vo;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.math.BigDecimal;

@Data
public class ProjectSaveReqVO {
    private String id;
    private String projectCode;
    @NotBlank(message = "项目名称不能为空")
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
}
