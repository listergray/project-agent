package com.ruoyi.system.domain;

/**
 * ?????
 */
public class PmReviewRequest
{
    private String id;
    /** basic | extend | purchase | finance */
    private String stage;
    /** approve | reject */
    private String action;
    private String comment;

    public String getId()
    {
        return id;
    }

    public void setId(String id)
    {
        this.id = id;
    }

    public String getStage()
    {
        return stage;
    }

    public void setStage(String stage)
    {
        this.stage = stage;
    }

    public String getAction()
    {
        return action;
    }

    public void setAction(String action)
    {
        this.action = action;
    }

    public String getComment()
    {
        return comment;
    }

    public void setComment(String comment)
    {
        this.comment = comment;
    }
}
