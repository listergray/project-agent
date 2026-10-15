package com.ruoyi.system.domain;

import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;

/**
 * ???????MVP ?????
 */
public class PmProject implements Serializable
{
    private static final long serialVersionUID = 1L;

    private String id;
    private String projectCode;
    private String projectName;
    private String projectType;
    private String owner;
    private String department;
    private Double budget;
    private String startDate;
    private String endDate;
    private String description;

    /** ???? */
    private String goals;
    private String members;
    private String riskLevel;
    private String priority;
    private String purchasePlan;
    private String financePlan;

    private String status;
    private String createdBy;
    private Long createdByUserId;
    private Long deptId;
    private String createdAt;
    private String updatedAt;

    private List<PmHistoryItem> history = new ArrayList<>();

    public String getId()
    {
        return id;
    }

    public void setId(String id)
    {
        this.id = id;
    }

    public String getProjectCode()
    {
        return projectCode;
    }

    public void setProjectCode(String projectCode)
    {
        this.projectCode = projectCode;
    }

    public String getProjectName()
    {
        return projectName;
    }

    public void setProjectName(String projectName)
    {
        this.projectName = projectName;
    }

    public String getProjectType()
    {
        return projectType;
    }

    public void setProjectType(String projectType)
    {
        this.projectType = projectType;
    }

    public String getOwner()
    {
        return owner;
    }

    public void setOwner(String owner)
    {
        this.owner = owner;
    }

    public String getDepartment()
    {
        return department;
    }

    public void setDepartment(String department)
    {
        this.department = department;
    }

    public Double getBudget()
    {
        return budget;
    }

    public void setBudget(Double budget)
    {
        this.budget = budget;
    }

    public String getStartDate()
    {
        return startDate;
    }

    public void setStartDate(String startDate)
    {
        this.startDate = startDate;
    }

    public String getEndDate()
    {
        return endDate;
    }

    public void setEndDate(String endDate)
    {
        this.endDate = endDate;
    }

    public String getDescription()
    {
        return description;
    }

    public void setDescription(String description)
    {
        this.description = description;
    }

    public String getGoals()
    {
        return goals;
    }

    public void setGoals(String goals)
    {
        this.goals = goals;
    }

    public String getMembers()
    {
        return members;
    }

    public void setMembers(String members)
    {
        this.members = members;
    }

    public String getRiskLevel()
    {
        return riskLevel;
    }

    public void setRiskLevel(String riskLevel)
    {
        this.riskLevel = riskLevel;
    }

    public String getPriority()
    {
        return priority;
    }

    public void setPriority(String priority)
    {
        this.priority = priority;
    }

    public String getPurchasePlan()
    {
        return purchasePlan;
    }

    public void setPurchasePlan(String purchasePlan)
    {
        this.purchasePlan = purchasePlan;
    }

    public String getFinancePlan()
    {
        return financePlan;
    }

    public void setFinancePlan(String financePlan)
    {
        this.financePlan = financePlan;
    }

    public String getStatus()
    {
        return status;
    }

    public void setStatus(String status)
    {
        this.status = status;
    }

    public String getCreatedBy()
    {
        return createdBy;
    }

    public void setCreatedBy(String createdBy)
    {
        this.createdBy = createdBy;
    }

    public Long getCreatedByUserId()
    {
        return createdByUserId;
    }

    public void setCreatedByUserId(Long createdByUserId)
    {
        this.createdByUserId = createdByUserId;
    }

    public Long getDeptId()
    {
        return deptId;
    }

    public void setDeptId(Long deptId)
    {
        this.deptId = deptId;
    }

    public String getCreatedAt()
    {
        return createdAt;
    }

    public void setCreatedAt(String createdAt)
    {
        this.createdAt = createdAt;
    }

    public String getUpdatedAt()
    {
        return updatedAt;
    }

    public void setUpdatedAt(String updatedAt)
    {
        this.updatedAt = updatedAt;
    }

    public List<PmHistoryItem> getHistory()
    {
        return history;
    }

    public void setHistory(List<PmHistoryItem> history)
    {
        this.history = history;
    }
}
