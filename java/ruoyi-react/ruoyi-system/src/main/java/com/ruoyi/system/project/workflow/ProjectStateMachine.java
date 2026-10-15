package com.ruoyi.system.project.workflow;

import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import com.ruoyi.common.exception.ServiceException;

/** State machine for PM workflow transitions. */
public class ProjectStateMachine
{
    public static final String ACT_SUBMIT_BASIC = "submit_basic";
    public static final String ACT_APPROVE_BASIC = "approve_basic";
    public static final String ACT_REJECT_BASIC = "reject_basic";
    public static final String ACT_SUBMIT_EXTEND = "submit_extend";
    public static final String ACT_APPROVE_EXTEND = "approve_extend";
    public static final String ACT_REJECT_EXTEND = "reject_extend";
    public static final String ACT_SUBMIT_PURCHASE = "submit_purchase";
    public static final String ACT_APPROVE_PURCHASE = "approve_purchase";
    public static final String ACT_REJECT_PURCHASE = "reject_purchase";
    public static final String ACT_APPROVE_FINANCE = "approve_finance";
    public static final String ACT_REJECT_FINANCE = "reject_finance";

    private static final Map<String, Map<String, String>> TRANSITIONS = new HashMap<>();

    static
    {
        put(PmStatus.DRAFT, ACT_SUBMIT_BASIC, PmStatus.PENDING_BASIC);
        put(PmStatus.PENDING_BASIC, ACT_APPROVE_BASIC, PmStatus.BASIC_PASSED);
        put(PmStatus.PENDING_BASIC, ACT_REJECT_BASIC, PmStatus.DRAFT);
        put(PmStatus.BASIC_PASSED, ACT_SUBMIT_EXTEND, PmStatus.PENDING_EXTEND);
        put(PmStatus.PENDING_EXTEND, ACT_APPROVE_EXTEND, PmStatus.EXTEND_PASSED);
        put(PmStatus.PENDING_EXTEND, ACT_REJECT_EXTEND, PmStatus.BASIC_PASSED);
        put(PmStatus.EXTEND_PASSED, ACT_SUBMIT_PURCHASE, PmStatus.PENDING_PURCHASE);
        put(PmStatus.PENDING_PURCHASE, ACT_APPROVE_PURCHASE, PmStatus.PENDING_FINANCE);
        put(PmStatus.PENDING_PURCHASE, ACT_REJECT_PURCHASE, PmStatus.EXTEND_PASSED);
        put(PmStatus.PENDING_FINANCE, ACT_APPROVE_FINANCE, PmStatus.APPROVED);
        put(PmStatus.PENDING_FINANCE, ACT_REJECT_FINANCE, PmStatus.EXTEND_PASSED);
    }

    private static void put(String from, String action, String to)
    {
        TRANSITIONS.computeIfAbsent(from, k -> new HashMap<>()).put(action, to);
    }

    public String transit(String currentStatus, String action)
    {
        Map<String, String> actions = TRANSITIONS.getOrDefault(currentStatus, Collections.emptyMap());
        String next = actions.get(action);
        if (next == null)
        {
            throw new ServiceException("illegal transition: status=" + currentStatus + " action=" + action);
        }
        return next;
    }

    public Set<String> allowedActions(String currentStatus)
    {
        return TRANSITIONS.getOrDefault(currentStatus, Collections.emptyMap()).keySet();
    }
}
