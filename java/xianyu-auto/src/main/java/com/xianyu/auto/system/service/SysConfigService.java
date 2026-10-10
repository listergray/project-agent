package com.xianyu.auto.system.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.xianyu.auto.common.util.DateUtils;
import com.xianyu.auto.system.entity.SysConfig;
import com.xianyu.auto.system.mapper.SysConfigMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 系统配置服务
 */
@Slf4j
@Service
public class SysConfigService extends ServiceImpl<SysConfigMapper, SysConfig> {

    /**
     * 按 key 获取配置值
     */
    public String getConfigValue(String key) {
        SysConfig config = baseMapper.selectOne(new LambdaQueryWrapper<SysConfig>()
                .eq(SysConfig::getConfigKey, key));
        return config == null ? null : config.getConfigValue();
    }

    /**
     * 按 key 获取配置值（带默认值）
     */
    public String getConfigValue(String key, String defaultValue) {
        String value = getConfigValue(key);
        return StringUtils.hasText(value) ? value : defaultValue;
    }

    /**
     * 按 group 获取配置集合
     */
    public Map<String, String> getConfigsByGroup(String group) {
        List<SysConfig> configs = baseMapper.selectList(new LambdaQueryWrapper<SysConfig>()
                .eq(SysConfig::getConfigGroup, group));
        Map<String, String> map = new HashMap<>();
        configs.forEach(c -> map.put(c.getConfigKey(), c.getConfigValue()));
        return map;
    }

    /**
     * 批量保存（新增或更新）
     */
    public void saveOrUpdate(List<SysConfig> configs) {
        if (configs == null) return;
        long now = DateUtils.nowMillis();
        for (SysConfig config : configs) {
            SysConfig existing = baseMapper.selectOne(new LambdaQueryWrapper<SysConfig>()
                    .eq(SysConfig::getConfigKey, config.getConfigKey()));
            if (existing == null) {
                config.setCreatedAt(now);
                config.setUpdatedAt(now);
                baseMapper.insert(config);
            } else {
                existing.setConfigValue(config.getConfigValue());
                existing.setDescription(config.getDescription());
                existing.setConfigGroup(config.getConfigGroup());
                existing.setUpdatedAt(now);
                baseMapper.updateById(existing);
            }
        }
    }

    public void deleteByKey(String key) {
        baseMapper.delete(new LambdaQueryWrapper<SysConfig>().eq(SysConfig::getConfigKey, key));
    }
}
