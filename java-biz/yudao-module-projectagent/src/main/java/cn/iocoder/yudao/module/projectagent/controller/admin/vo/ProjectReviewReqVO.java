package cn.iocoder.yudao.module.projectagent.controller.admin.vo;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class ProjectReviewReqVO {
    @NotBlank
    private String id;
    /** approve | reject */
    @NotBlank
    private String action;
    private String reviewer;
    private String comment;
}
