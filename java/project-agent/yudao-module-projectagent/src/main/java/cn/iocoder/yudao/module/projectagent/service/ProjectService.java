package cn.iocoder.yudao.module.projectagent.service;

import cn.iocoder.yudao.module.projectagent.controller.admin.vo.ProjectRespVO;
import cn.iocoder.yudao.module.projectagent.controller.admin.vo.ProjectReviewReqVO;
import cn.iocoder.yudao.module.projectagent.controller.admin.vo.ProjectSaveReqVO;

import java.util.List;
import java.util.Map;

/**
 * 项目库基础业务：CRUD + 审批状态机（不含 AI）。
 */
public interface ProjectService {

    String create(ProjectSaveReqVO req);

    void update(ProjectSaveReqVO req);

    ProjectRespVO get(String id);

    List<ProjectRespVO> list(String status);

    void submit(String id);

    void review(ProjectReviewReqVO req);

    Map<String, Long> stats();

    /** 审批通过后由 Python RAG 回写向量主键 */
    void updateRagItemPk(String id, String ragItemPk);
}
