package com.ruoyi.system.service;

import java.util.List;
import java.util.Map;
import com.ruoyi.system.domain.PmProject;
import com.ruoyi.system.domain.PmReviewRequest;

/**
 * ???? Facade
 */
public interface IPmProjectService
{
    List<PmProject> selectList(String status, String keyword);

    PmProject selectById(String id);

    PmProject createBasic(PmProject project);

    PmProject updateBasic(PmProject project);

    PmProject submitBasic(String id);

    PmProject updateExtend(PmProject project);

    PmProject submitExtend(String id);

    PmProject submitPurchase(String id);

    PmProject review(PmReviewRequest request);

    Map<String, Long> stats();
}
