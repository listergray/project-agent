package com.ruoyi.system.domain;

import java.io.Serializable;

/**
 * ????????
 */
public class PmHistoryItem implements Serializable
{
    private static final long serialVersionUID = 1L;

    private String at;
    private String action;
    private String by;
    private String role;
    private String note;

    public PmHistoryItem()
    {
    }

    public PmHistoryItem(String at, String action, String by, String role, String note)
    {
        this.at = at;
        this.action = action;
        this.by = by;
        this.role = role;
        this.note = note;
    }

    public String getAt()
    {
        return at;
    }

    public void setAt(String at)
    {
        this.at = at;
    }

    public String getAction()
    {
        return action;
    }

    public void setAction(String action)
    {
        this.action = action;
    }

    public String getBy()
    {
        return by;
    }

    public void setBy(String by)
    {
        this.by = by;
    }

    public String getRole()
    {
        return role;
    }

    public void setRole(String role)
    {
        this.role = role;
    }

    public String getNote()
    {
        return note;
    }

    public void setNote(String note)
    {
        this.note = note;
    }
}
