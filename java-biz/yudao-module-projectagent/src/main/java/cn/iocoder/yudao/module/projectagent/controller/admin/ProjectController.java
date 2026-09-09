package cn.iocoder.yudao.module.projectagent.controller.admin;

import cn.iocoder.yudao.module.projectagent.controller.admin.vo.ProjectRespVO;
import cn.iocoder.yudao.module.projectagent.controller.admin.vo.ProjectReviewReqVO;
import cn.iocoder.yudao.module.projectagent.controller.admin.vo.ProjectSaveReqVO;
import cn.iocoder.yudao.module.projectagent.service.ProjectService;
import jakarta.annotation.Resource;
import jakarta.validation.Valid;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 项目库 Admin API（芋道风格路径）。
 * 迁入正式芋道后请改为 CommonResult&lt;T&gt; + @PreAuthorize 权限注解。
 */
@RestController
@RequestMapping("/admin-api/project-agent/project")
@Validated
public class ProjectController {

    @Resource
    private ProjectService projectService;

    @PostMapping("/create")
    public Map<String, Object> create(@Valid @RequestBody ProjectSaveReqVO req) {
        String id = projectService.create(req);
        return ok(id);
    }

    @PutMapping("/update")
    public Map<String, Object> update(@Valid @RequestBody ProjectSaveReqVO req) {
        projectService.update(req);
        return ok(true);
    }

    @GetMapping("/get")
    public Map<String, Object> get(@RequestParam("id") String id) {
        return ok(projectService.get(id));
    }

    @GetMapping("/page")
    public Map<String, Object> page(@RequestParam(value = "status", required = false) String status) {
        List<ProjectRespVO> list = projectService.list(status);
        Map<String, Object> page = new HashMap<>();
        page.put("list", list);
        page.put("total", list.size());
        return ok(page);
    }

    @PostMapping("/submit")
    public Map<String, Object> submit(@RequestParam("id") String id) {
        projectService.submit(id);
        return ok(true);
    }

    @PostMapping("/review")
    public Map<String, Object> review(@Valid @RequestBody ProjectReviewReqVO req) {
        projectService.review(req);
        return ok(true);
    }

    @GetMapping("/stats")
    public Map<String, Object> stats() {
        return ok(projectService.stats());
    }

    @PutMapping("/rag-item-pk")
    public Map<String, Object> ragItemPk(@RequestParam("id") String id,
                                         @RequestParam("ragItemPk") String ragItemPk) {
        projectService.updateRagItemPk(id, ragItemPk);
        return ok(true);
    }

    private static Map<String, Object> ok(Object data) {
        Map<String, Object> m = new HashMap<>();
        m.put("code", 0);
        m.put("data", data);
        m.put("msg", "");
        return m;
    }
}
