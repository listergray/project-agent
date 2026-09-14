package cn.iocoder.yudao.module.projectagent.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * 立项状态（与 Python ProjectStatus 对齐）。
 */
@Getter
@AllArgsConstructor
public enum ProjectStatusEnum {
    DRAFT("draft", "草稿"),
    PENDING("pending", "待审批"),
    APPROVED("approved", "已通过"),
    REJECTED("rejected", "已驳回");

    private final String status;
    private final String label;
}
