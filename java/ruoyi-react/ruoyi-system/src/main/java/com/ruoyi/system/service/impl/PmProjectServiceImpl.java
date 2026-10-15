package com.ruoyi.system.service.impl;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import com.ruoyi.common.core.domain.entity.SysRole;
import com.ruoyi.common.core.domain.model.LoginUser;
import com.ruoyi.common.exception.ServiceException;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.system.domain.PmHistoryItem;
import com.ruoyi.system.domain.PmProject;
import com.ruoyi.system.domain.PmReviewRequest;
import com.ruoyi.system.project.workflow.PmStatus;
import com.ruoyi.system.project.workflow.ProjectStateMachine;
import com.ruoyi.system.project.workflow.ReviewStrategy;
import com.ruoyi.system.project.workflow.ReviewStrategyFactory;
import com.ruoyi.system.service.IPmProjectService;

/**
 * PM workflow facade (in-memory MVP).
 */
@Service
public class PmProjectServiceImpl implements IPmProjectService
{
    private final ConcurrentHashMap<String, PmProject> store = new ConcurrentHashMap<>();
    private final ProjectStateMachine stateMachine = new ProjectStateMachine();

    @Autowired
    private ReviewStrategyFactory reviewStrategyFactory;

    private static final DateTimeFormatter FMT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");

    @PostConstruct
    public void seed()
    {
        PmProject p1 = baseSeed("seed-001", "PRJ-2026-DEMO-01", "?????????", "??",
                "??", "????", 80000.0, PmStatus.DRAFT, "????????????");
        p1.setCreatedBy("pm_biz");
        p1.setCreatedByUserId(101L);
        store.put(p1.getId(), p1);

        PmProject p2 = baseSeed("seed-002", "PRJ-2026-DEMO-02", "????????", "??",
                "??", "????", 250000.0, PmStatus.PENDING_BASIC, "????????????");
        p2.setCreatedBy("pm_biz");
        p2.setCreatedByUserId(101L);
        p2.getHistory().add(new PmHistoryItem(now(), "submitted_basic", "pm_biz", "pm_applicant", "??????"));
        store.put(p2.getId(), p2);

        PmProject p3 = baseSeed("seed-003", "PRJ-2026-DEMO-03", "????????", "??",
                "??", "???", 120000.0, PmStatus.BASIC_PASSED, "????????????");
        p3.setCreatedBy("pm_biz");
        p3.setCreatedByUserId(101L);
        p3.setGoals("???????????");
        p3.setMembers("??,??");
        p3.setRiskLevel("?");
        p3.setPriority("P1");
        p3.getHistory().add(new PmHistoryItem(now(), "approved_basic", "pm_office", "pm_basic_auditor", "????"));
        store.put(p3.getId(), p3);
    }

    private PmProject baseSeed(String id, String code, String name, String type, String owner,
            String dept, double budget, String status, String desc)
    {
        PmProject p = new PmProject();
        p.setId(id);
        p.setProjectCode(code);
        p.setProjectName(name);
        p.setProjectType(type);
        p.setOwner(owner);
        p.setDepartment(dept);
        p.setBudget(budget);
        p.setStartDate("2026-04-01");
        p.setEndDate("2026-09-30");
        p.setDescription(desc);
        p.setStatus(status);
        p.setDeptId(103L);
        p.setCreatedAt(now());
        p.setUpdatedAt(now());
        p.setHistory(new ArrayList<>());
        return p;
    }

    private String now()
    {
        return LocalDateTime.now().format(FMT);
    }

    private String currentRoleKey()
    {
        try
        {
            LoginUser loginUser = SecurityUtils.getLoginUser();
            List<SysRole> roles = loginUser.getUser().getRoles();
            if (roles == null || roles.isEmpty())
            {
                return "";
            }
            return roles.stream().map(SysRole::getRoleKey).collect(Collectors.joining(","));
        }
        catch (Exception e)
        {
            return "";
        }
    }

    private void appendHistory(PmProject project, String action, String note)
    {
        project.getHistory().add(new PmHistoryItem(now(), action, SecurityUtils.getUsername(), currentRoleKey(), note));
        project.setUpdatedAt(now());
    }

    @Override
    public List<PmProject> selectList(String status, String keyword)
    {
        return store.values().stream()
                .filter(p -> StringUtils.isEmpty(status) || status.equals(p.getStatus()))
                .filter(p -> {
                    if (StringUtils.isEmpty(keyword))
                    {
                        return true;
                    }
                    String q = keyword.toLowerCase();
                    return (p.getProjectName() != null && p.getProjectName().toLowerCase().contains(q))
                            || (p.getProjectCode() != null && p.getProjectCode().toLowerCase().contains(q))
                            || (p.getOwner() != null && p.getOwner().toLowerCase().contains(q));
                })
                .sorted(Comparator.comparing(PmProject::getUpdatedAt, Comparator.nullsLast(Comparator.reverseOrder())))
                .collect(Collectors.toList());
    }

    @Override
    public PmProject selectById(String id)
    {
        PmProject project = store.get(id);
        if (project == null)
        {
            throw new ServiceException("?????");
        }
        return project;
    }

    @Override
    public PmProject createBasic(PmProject body)
    {
        if (StringUtils.isEmpty(body.getProjectName()))
        {
            throw new ServiceException("????????");
        }
        PmProject p = new PmProject();
        p.setId(UUID.randomUUID().toString().replace("-", "").substring(0, 16));
        copyBasic(body, p);
        if (StringUtils.isEmpty(p.getProjectCode()))
        {
            p.setProjectCode("PRJ-" + LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss")));
        }
        p.setStatus(PmStatus.DRAFT);
        p.setCreatedBy(SecurityUtils.getUsername());
        p.setCreatedByUserId(SecurityUtils.getUserId());
        p.setDeptId(SecurityUtils.getDeptId());
        p.setCreatedAt(now());
        p.setUpdatedAt(now());
        p.setHistory(new ArrayList<>());
        appendHistory(p, "created", "????????");
        store.put(p.getId(), p);
        return p;
    }

    @Override
    public PmProject updateBasic(PmProject body)
    {
        PmProject p = selectById(body.getId());
        if (!PmStatus.DRAFT.equals(p.getStatus()))
        {
            throw new ServiceException("????????????");
        }
        assertApplicantOrAdmin(p);
        copyBasic(body, p);
        appendHistory(p, "updated_basic", "??????");
        return p;
    }

    @Override
    public PmProject submitBasic(String id)
    {
        PmProject p = selectById(id);
        assertApplicantOrAdmin(p);
        String next = stateMachine.transit(p.getStatus(), ProjectStateMachine.ACT_SUBMIT_BASIC);
        p.setStatus(next);
        appendHistory(p, "submitted_basic", "??????");
        return p;
    }

    @Override
    public PmProject updateExtend(PmProject body)
    {
        PmProject p = selectById(body.getId());
        if (!(PmStatus.BASIC_PASSED.equals(p.getStatus()) || PmStatus.EXTEND_PASSED.equals(p.getStatus())))
        {
            throw new ServiceException("????????????????????");
        }
        assertApplicantOrAdmin(p);
        p.setGoals(body.getGoals());
        p.setMembers(body.getMembers());
        p.setRiskLevel(body.getRiskLevel());
        p.setPriority(body.getPriority());
        p.setPurchasePlan(body.getPurchasePlan());
        p.setFinancePlan(body.getFinancePlan());
        appendHistory(p, "updated_extend", "??????");
        return p;
    }

    @Override
    public PmProject submitExtend(String id)
    {
        PmProject p = selectById(id);
        assertApplicantOrAdmin(p);
        if (StringUtils.isEmpty(p.getGoals()))
        {
            throw new ServiceException("???????????????");
        }
        String next = stateMachine.transit(p.getStatus(), ProjectStateMachine.ACT_SUBMIT_EXTEND);
        p.setStatus(next);
        appendHistory(p, "submitted_extend", "??????");
        return p;
    }

    @Override
    public PmProject submitPurchase(String id)
    {
        PmProject p = selectById(id);
        assertApplicantOrAdmin(p);
        String next = stateMachine.transit(p.getStatus(), ProjectStateMachine.ACT_SUBMIT_PURCHASE);
        p.setStatus(next);
        appendHistory(p, "submitted_purchase", "??????");
        return p;
    }

    @Override
    public PmProject review(PmReviewRequest request)
    {
        if (request == null || StringUtils.isEmpty(request.getId()) || StringUtils.isEmpty(request.getStage()))
        {
            throw new ServiceException("???????");
        }
        String action = request.getAction();
        if (!"approve".equals(action) && !"reject".equals(action))
        {
            throw new ServiceException("action ??? approve / reject");
        }
        ReviewStrategy strategy = reviewStrategyFactory.get(request.getStage());
        strategy.assertAuthorized();
        PmProject p = selectById(request.getId());
        if (!strategy.expectedStatus().equals(p.getStatus()))
        {
            throw new ServiceException("?????????????????=" + p.getStatus());
        }
        strategy.beforeReview(p, action, request.getComment());
        String machineAction = "approve".equals(action) ? strategy.approveAction() : strategy.rejectAction();
        String next = stateMachine.transit(p.getStatus(), machineAction);
        p.setStatus(next);
        String note = StringUtils.isEmpty(request.getComment())
                ? ("approve".equals(action) ? "??" : "??")
                : request.getComment();
        appendHistory(p, action + "_" + request.getStage(), note);
        return p;
    }

    @Override
    public Map<String, Long> stats()
    {
        Map<String, Long> map = new LinkedHashMap<>();
        String[] keys = {
                PmStatus.DRAFT, PmStatus.PENDING_BASIC, PmStatus.BASIC_PASSED, PmStatus.PENDING_EXTEND,
                PmStatus.EXTEND_PASSED, PmStatus.PENDING_PURCHASE, PmStatus.PENDING_FINANCE, PmStatus.APPROVED
        };
        for (String k : keys)
        {
            map.put(k, 0L);
        }
        long total = 0;
        for (PmProject p : store.values())
        {
            total++;
            map.computeIfPresent(p.getStatus(), (k, v) -> v + 1);
        }
        map.put("total", total);
        return map;
    }

    private void copyBasic(PmProject src, PmProject dest)
    {
        if (StringUtils.isNotEmpty(src.getProjectCode()))
        {
            dest.setProjectCode(src.getProjectCode());
        }
        dest.setProjectName(src.getProjectName());
        dest.setProjectType(StringUtils.isEmpty(src.getProjectType()) ? "??" : src.getProjectType());
        dest.setOwner(src.getOwner());
        dest.setDepartment(src.getDepartment());
        dest.setBudget(src.getBudget() == null ? 0D : src.getBudget());
        dest.setStartDate(src.getStartDate());
        dest.setEndDate(src.getEndDate());
        dest.setDescription(src.getDescription());
    }

    private void assertApplicantOrAdmin(PmProject p)
    {
        if (SecurityUtils.isAdmin(SecurityUtils.getUserId())
                || SecurityUtils.hasRole("admin")
                || SecurityUtils.hasRole("project_admin")
                || SecurityUtils.hasRole("pm_applicant"))
        {
            return;
        }
        if (p.getCreatedByUserId() != null && p.getCreatedByUserId().equals(SecurityUtils.getUserId()))
        {
            return;
        }
        throw new ServiceException("???????");
    }
}