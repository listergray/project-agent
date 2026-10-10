package com.xianyu.auto.common.api;

import lombok.Data;

import java.io.Serializable;

/**
 * 分页查询基础参数
 */
@Data
public class PageParam implements Serializable {

    private Integer pageNo = 1;
    private Integer pageSize = 10;

    public Integer getPageNo() {
        return pageNo == null || pageNo < 1 ? 1 : pageNo;
    }

    public Integer getPageSize() {
        if (pageSize == null || pageSize < 1) return 10;
        return Math.min(pageSize, 500);
    }

    public Integer getOffset() {
        return (getPageNo() - 1) * getPageSize();
    }
}
