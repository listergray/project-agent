package com.ruoyi.system.project.workflow;

public final class PmStatus
{
    public static final String DRAFT = "draft";
    public static final String PENDING_BASIC = "pending_basic";
    public static final String BASIC_PASSED = "basic_passed";
    public static final String PENDING_EXTEND = "pending_extend";
    public static final String EXTEND_PASSED = "extend_passed";
    public static final String PENDING_PURCHASE = "pending_purchase";
    public static final String PENDING_FINANCE = "pending_finance";
    public static final String APPROVED = "approved";

    private PmStatus() {}

    public static String label(String status)
    {
        if (status == null)
        {
            return "";
        }
        switch (status)
        {
            case DRAFT:
                return "草稿";
            case PENDING_BASIC:
                return "待一次审核";
            case BASIC_PASSED:
                return "一次审通过";
            case PENDING_EXTEND:
                return "待二次审核";
            case EXTEND_PASSED:
                return "二次审通过";
            case PENDING_PURCHASE:
                return "购买联审中";
            case PENDING_FINANCE:
                return "财务联审中";
            case APPROVED:
                return "已立项通过";
            default:
                return status;
        }
    }
}
