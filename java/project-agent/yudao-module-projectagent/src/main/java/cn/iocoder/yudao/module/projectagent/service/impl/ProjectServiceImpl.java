package cn.iocoder.yudao.module.projectagent.service.impl;

import cn.iocoder.yudao.module.projectagent.controller.admin.vo.ProjectRespVO;
import cn.iocoder.yudao.module.projectagent.controller.admin.vo.ProjectReviewReqVO;
import cn.iocoder.yudao.module.projectagent.controller.admin.vo.ProjectSaveReqVO;
import cn.iocoder.yudao.module.projectagent.dal.dataobject.ProjectDO;
import cn.iocoder.yudao.module.projectagent.dal.mysql.ProjectMapper;
import cn.iocoder.yudao.module.projectagent.enums.ProjectStatusEnum;
import cn.iocoder.yudao.module.projectagent.service.ProjectService;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import jakarta.annotation.Resource;
import org.springframework.beans.BeanUtils;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * 骨架实现：迁入芋道后可替换为带权限/租户/操作日志的正式写法。
 * 异常请改为芋道 ServiceExceptionUtil.exception(...)
 */
@Service
public class ProjectServiceImpl implements ProjectService {

    @Resource
    private ProjectMapper projectMapper;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public String create(ProjectSaveReqVO req) {
        ProjectDO row = toDO(req);
        row.setId(UUID.randomUUID().toString().replace("-", ""));
        row.setStatus(ProjectStatusEnum.DRAFT.getStatus());
        row.setCreateTime(LocalDateTime.now());
        row.setUpdateTime(LocalDateTime.now());
        if (!StringUtils.hasText(row.getCreatedBy())) {
            row.setCreatedBy("申请人");
        }
        projectMapper.insert(row);
        return row.getId();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void update(ProjectSaveReqVO req) {
        ProjectDO old = require(req.getId());
        String st = old.getStatus();
        if (!ProjectStatusEnum.DRAFT.getStatus().equals(st)
                && !ProjectStatusEnum.REJECTED.getStatus().equals(st)) {
            throw new IllegalStateException("仅草稿或驳回状态可编辑");
        }
        ProjectDO row = toDO(req);
        row.setId(old.getId());
        row.setStatus(ProjectStatusEnum.DRAFT.getStatus());
        row.setUpdateTime(LocalDateTime.now());
        projectMapper.updateById(row);
    }

    @Override
    public ProjectRespVO get(String id) {
        return toVO(require(id));
    }

    @Override
    public List<ProjectRespVO> list(String status) {
        LambdaQueryWrapper<ProjectDO> q = new LambdaQueryWrapper<>();
        if (StringUtils.hasText(status)) {
            q.eq(ProjectDO::getStatus, status);
        }
        q.orderByDesc(ProjectDO::getUpdateTime);
        return projectMapper.selectList(q).stream().map(this::toVO).collect(Collectors.toList());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void submit(String id) {
        ProjectDO old = require(id);
        if (!ProjectStatusEnum.DRAFT.getStatus().equals(old.getStatus())
                && !ProjectStatusEnum.REJECTED.getStatus().equals(old.getStatus())) {
            throw new IllegalStateException("仅草稿或驳回可提交");
        }
        old.setStatus(ProjectStatusEnum.PENDING.getStatus());
        old.setSubmittedAt(LocalDateTime.now());
        old.setUpdateTime(LocalDateTime.now());
        projectMapper.updateById(old);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void review(ProjectReviewReqVO req) {
        ProjectDO old = require(req.getId());
        if (!ProjectStatusEnum.PENDING.getStatus().equals(old.getStatus())) {
            throw new IllegalStateException("仅待审批可审核");
        }
        String action = req.getAction() == null ? "" : req.getAction().trim().toLowerCase();
        if ("approve".equals(action)) {
            old.setStatus(ProjectStatusEnum.APPROVED.getStatus());
        } else if ("reject".equals(action)) {
            old.setStatus(ProjectStatusEnum.REJECTED.getStatus());
        } else {
            throw new IllegalArgumentException("action 仅支持 approve|reject");
        }
        old.setReviewer(StringUtils.hasText(req.getReviewer()) ? req.getReviewer() : "审批人");
        old.setReviewComment(req.getComment());
        old.setReviewedAt(LocalDateTime.now());
        old.setUpdateTime(LocalDateTime.now());
        projectMapper.updateById(old);
        // 通过后由 Python 侧调用 RAG 同步，再回写 ragItemPk
    }

    @Override
    public Map<String, Long> stats() {
        Map<String, Long> map = new HashMap<>();
        for (ProjectStatusEnum e : ProjectStatusEnum.values()) {
            Long c = projectMapper.selectCount(
                    new LambdaQueryWrapper<ProjectDO>().eq(ProjectDO::getStatus, e.getStatus()));
            map.put(e.getStatus(), c == null ? 0L : c);
        }
        return map;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void updateRagItemPk(String id, String ragItemPk) {
        ProjectDO old = require(id);
        old.setRagItemPk(ragItemPk);
        old.setUpdateTime(LocalDateTime.now());
        projectMapper.updateById(old);
    }

    private ProjectDO require(String id) {
        ProjectDO row = projectMapper.selectById(id);
        if (row == null) {
            throw new IllegalArgumentException("项目不存在: " + id);
        }
        return row;
    }

    private ProjectDO toDO(ProjectSaveReqVO req) {
        ProjectDO row = new ProjectDO();
        BeanUtils.copyProperties(req, row);
        return row;
    }

    private ProjectRespVO toVO(ProjectDO row) {
        ProjectRespVO vo = new ProjectRespVO();
        BeanUtils.copyProperties(row, vo);
        return vo;
    }
}
