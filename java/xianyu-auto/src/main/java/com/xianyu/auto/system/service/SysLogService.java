package com.xianyu.auto.system.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.xianyu.auto.common.api.PageResult;
import com.xianyu.auto.common.util.DateUtils;
import com.xianyu.auto.system.entity.SysLog;
import com.xianyu.auto.system.mapper.SysLogMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

/**
 * 操作日志服务
 */
@Slf4j
@Service
public class SysLogService extends ServiceImpl<SysLogMapper, SysLog> {

    public void record(String operator, String action, String method, String params,
                        String result, String ip, Long durationMs, String errorMsg) {
        SysLog log = new SysLog();
        log.setOperator(operator);
        log.setAction(action);
        log.setMethod(method);
        log.setParams(params);
        log.setResult(result);
        log.setIp(ip);
        log.setDurationMs(durationMs);
        log.setErrorMsg(errorMsg);
        log.setCreatedAt(DateUtils.nowMillis());
        baseMapper.insert(log);
    }

    public PageResult<SysLog> page(Integer pageNo, Integer pageSize, String keyword, String action) {
        Page<SysLog> page = new Page<>(pageNo, pageSize);
        LambdaQueryWrapper<SysLog> wrapper = new LambdaQueryWrapper<>();
        if (StringUtils.hasText(keyword)) {
            wrapper.like(SysLog::getOperator, keyword)
                    .or().like(SysLog::getMethod, keyword)
                    .or().like(SysLog::getParams, keyword);
        }
        if (StringUtils.hasText(action)) {
            wrapper.eq(SysLog::getAction, action);
        }
        wrapper.orderByDesc(SysLog::getCreatedAt);
        IPage<SysLog> result = baseMapper.selectPage(page, wrapper);
        return new PageResult<>(result.getRecords(), result.getTotal());
    }
}
