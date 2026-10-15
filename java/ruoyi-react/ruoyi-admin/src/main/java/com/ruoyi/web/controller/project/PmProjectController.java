package com.ruoyi.web.controller.project;

import java.util.List;
import java.util.Map;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.constant.HttpStatus;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.core.page.TableSupport;
import com.ruoyi.common.core.page.PageDomain;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.system.domain.PmProject;
import com.ruoyi.system.domain.PmReviewRequest;
import com.ruoyi.system.service.IPmProjectService;

/**
 * ???? API
 */
@RestController
@RequestMapping("/project/pm")
public class PmProjectController extends BaseController
{
    @Autowired
    private IPmProjectService pmProjectService;

    @PreAuthorize("@ss.hasPermi('project:pm:list')")
    @GetMapping("/list")
    public TableDataInfo list(@RequestParam(required = false) String status,
            @RequestParam(required = false) String keyword)
    {
        List<PmProject> all = pmProjectService.selectList(status, keyword);
        PageDomain pageDomain = TableSupport.buildPageRequest();
        int pageNum = pageDomain.getPageNum() == null ? 1 : pageDomain.getPageNum();
        int pageSize = pageDomain.getPageSize() == null ? 10 : pageDomain.getPageSize();
        int from = Math.max(0, (pageNum - 1) * pageSize);
        int to = Math.min(all.size(), from + pageSize);
        List<PmProject> page = from >= all.size() ? List.of() : all.subList(from, to);
        TableDataInfo rsp = new TableDataInfo();
        rsp.setCode(HttpStatus.SUCCESS);
        rsp.setMsg("????");
        rsp.setRows(page);
        rsp.setTotal(all.size());
        return rsp;
    }

    @PreAuthorize("@ss.hasPermi('project:pm:list')")
    @GetMapping("/stats")
    public AjaxResult stats()
    {
        Map<String, Long> stats = pmProjectService.stats();
        return success(stats);
    }

    @PreAuthorize("@ss.hasPermi('project:pm:list')")
    @GetMapping("/{id}")
    public AjaxResult getInfo(@PathVariable String id)
    {
        return success(pmProjectService.selectById(id));
    }

    @PreAuthorize("@ss.hasPermi('project:pm:basic:edit')")
    @Log(title = "??????", businessType = BusinessType.INSERT)
    @PostMapping("/basic")
    public AjaxResult createBasic(@RequestBody PmProject project)
    {
        return success(pmProjectService.createBasic(project));
    }

    @PreAuthorize("@ss.hasPermi('project:pm:basic:edit')")
    @Log(title = "??????", businessType = BusinessType.UPDATE)
    @PutMapping("/basic")
    public AjaxResult updateBasic(@RequestBody PmProject project)
    {
        return success(pmProjectService.updateBasic(project));
    }

    @PreAuthorize("@ss.hasPermi('project:pm:basic:edit')")
    @Log(title = "??????", businessType = BusinessType.UPDATE)
    @PostMapping("/basic/submit")
    public AjaxResult submitBasic(@RequestBody Map<String, String> body)
    {
        return success(pmProjectService.submitBasic(body.get("id")));
    }

    @PreAuthorize("@ss.hasPermi('project:pm:extend:edit')")
    @Log(title = "??????", businessType = BusinessType.UPDATE)
    @PutMapping("/extend")
    public AjaxResult updateExtend(@RequestBody PmProject project)
    {
        return success(pmProjectService.updateExtend(project));
    }

    @PreAuthorize("@ss.hasPermi('project:pm:extend:edit')")
    @Log(title = "??????", businessType = BusinessType.UPDATE)
    @PostMapping("/extend/submit")
    public AjaxResult submitExtend(@RequestBody Map<String, String> body)
    {
        return success(pmProjectService.submitExtend(body.get("id")));
    }

    @PreAuthorize("@ss.hasPermi('project:pm:extend:edit')")
    @Log(title = "??????", businessType = BusinessType.UPDATE)
    @PostMapping("/purchase/submit")
    public AjaxResult submitPurchase(@RequestBody Map<String, String> body)
    {
        return success(pmProjectService.submitPurchase(body.get("id")));
    }

    @PreAuthorize("@ss.hasAnyPermi('project:pm:audit:basic,project:pm:audit:extend,project:pm:audit:purchase,project:pm:audit:finance')")
    @Log(title = "????", businessType = BusinessType.UPDATE)
    @PostMapping("/review")
    public AjaxResult review(@RequestBody PmReviewRequest request)
    {
        return success(pmProjectService.review(request));
    }
}
