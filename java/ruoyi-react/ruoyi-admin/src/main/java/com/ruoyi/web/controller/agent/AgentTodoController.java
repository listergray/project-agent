package com.ruoyi.web.controller.agent;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import com.ruoyi.common.annotation.Anonymous;
import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.web.agent.AgentTodoItem;
import com.ruoyi.web.agent.AgentTodoQueue;
import com.ruoyi.web.agent.AgentTodoStore;

@Anonymous
@RestController
@RequestMapping("/agent/todo")
public class AgentTodoController extends BaseController
{
    @Autowired
    private AgentTodoStore store;

    @GetMapping("/list")
    public AjaxResult list(@RequestParam(required = false) String status)
    {
        AgentTodoQueue queue = store.load();
        List<AgentTodoItem> items = queue.getItems();
        if (status != null && !status.isBlank() && !"all".equals(status))
        {
            items = items.stream().filter(i -> status.equals(i.getStatus())).toList();
        }
        Map<String, Object> data = new LinkedHashMap<>();
        data.put("file", store.resolveFile().toString());
        data.put("defaults", queue.getDefaults());
        data.put("items", items);
        return success(data);
    }

    @PostMapping
    @Log(title = "Agent待办", businessType = BusinessType.INSERT)
    public AjaxResult add(@RequestBody AgentTodoItem item)
    {
        try
        {
            return success(store.upsert(item, true));
        }
        catch (IllegalArgumentException e)
        {
            return error(e.getMessage());
        }
    }

    @PutMapping
    @Log(title = "Agent待办", businessType = BusinessType.UPDATE)
    public AjaxResult edit(@RequestBody AgentTodoItem item)
    {
        try
        {
            if (item.getId() == null || item.getId().isBlank())
            {
                return error("缺少 id");
            }
            return success(store.upsert(item, false));
        }
        catch (IllegalArgumentException e)
        {
            return error(e.getMessage());
        }
    }

    @PutMapping("/{id}/status")
    @Log(title = "Agent待办状态", businessType = BusinessType.UPDATE)
    public AjaxResult status(@PathVariable String id, @RequestBody Map<String, String> body)
    {
        AgentTodoItem patch = new AgentTodoItem();
        patch.setId(id);
        patch.setStatus(body.get("status"));
        try
        {
            return success(store.upsert(patch, false));
        }
        catch (IllegalArgumentException e)
        {
            return error(e.getMessage());
        }
    }

    @DeleteMapping("/{id}")
    @Log(title = "Agent待办", businessType = BusinessType.DELETE)
    public AjaxResult remove(@PathVariable String id)
    {
        try
        {
            store.delete(id);
            return success();
        }
        catch (IllegalArgumentException e)
        {
            return error(e.getMessage());
        }
    }
}
