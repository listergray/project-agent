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
                return "??";
            case PENDING_BASIC:
                return "?????";
            case BASIC_PASSED:
                return "?????";
            case PENDING_EXTEND:
                return "?????";
            case EXTEND_PASSED:
                return "?????";
            case PENDING_PURCHASE:
                return "?????";
            case PENDING_FINANCE:
                return "?????";
            case APPROVED:
                return "?????";
            default:
                return status;
        }
    }
}
