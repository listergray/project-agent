package com.ruoyi.system.project.workflow;

import org.springframework.stereotype.Component;
import com.ruoyi.common.exception.ServiceException;
import com.ruoyi.common.utils.SecurityUtils;

@Component
public class BasicReviewStrategy implements ReviewStrategy
{
    @Override
    public String stage()
    {
        return "basic";
    }

    @Override
    public void assertAuthorized()
    {
        if (!(SecurityUtils.isAdmin(SecurityUtils.getUserId())
                || SecurityUtils.hasRole("pm_basic_auditor")
                || SecurityUtils.hasRole("project_admin")
                || SecurityUtils.hasRole("admin")))
        {
            throw new ServiceException("??????????????");
        }
    }

    @Override
    public String expectedStatus()
    {
        return PmStatus.PENDING_BASIC;
    }

    @Override
    public String approveAction()
    {
        return ProjectStateMachine.ACT_APPROVE_BASIC;
    }

    @Override
    public String rejectAction()
    {
        return ProjectStateMachine.ACT_REJECT_BASIC;
    }
}
