package com.xianyu.auto.controller;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;

/**
 * SPA 入口控制器
 * 处理前端路由，将所有非 API 请求转发到 index.html
 */
@Controller
@RequestMapping("/")
public class IndexController {

    /**
     * 转发所有非 API 请求到 index.html（SPA 路由）
     */
    @GetMapping(value = {"/", "/**/{path:[^.]*}"})
    public String forward() {
        return "forward:/index.html";
    }
}
