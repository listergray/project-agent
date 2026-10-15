package com.ruoyi.system.project.workflow;

import org.springframework.stereotype.Component;
import com.ruoyi.common.exception.ServiceException;
import com.ruoyi.common.utils.SecurityUtils;

@Component
public class FinanceReviewStrategy implements ReviewStrategy
{
    @Override
    public String stage()
    {
        return "finance";
    }

    @Override
    public void assertAuthorized()
    {
        if (!(SecurityUtils.isAdmin(SecurityUtils.getUserId())
                || SecurityUtils.hasRole("pm_finance")
                || SecurityUtils.hasRole("project_admin")
                || SecurityUtils.hasRole("admin")))
        {
            throw new ServiceException("??????????????");
        }
    }

    @Override
    public String expectedStatus()
    {
        return PmStatus.PENDING_FINANCE;
    }

    @Override
    public String approveAction()
    {
        return ProjectStateMachine.ACT_APPROVE_FINANCE;
    }

    @Override
    public String rejectAction()
    {
        return ProjectStateMachine.ACT_REJECT_FINANCE;
    }
}
