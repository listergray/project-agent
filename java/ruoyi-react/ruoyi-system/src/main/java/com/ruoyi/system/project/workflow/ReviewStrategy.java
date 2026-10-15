package com.ruoyi.system.project.workflow;

import com.ruoyi.system.domain.PmProject;

/**
 * ????????????????????/????
 */
public interface ReviewStrategy
{
    /** basic | extend | purchase | finance */
    String stage();

    void assertAuthorized();

    String expectedStatus();

    String approveAction();

    String rejectAction();

    default void beforeReview(PmProject project, String action, String comment)
    {
        // no-op hook
    }
}
