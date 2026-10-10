package com.xianyu.auto.config;

import com.xianyu.auto.common.constant.CommonConstants;
import com.xianyu.auto.common.util.DateUtils;
import com.xianyu.auto.common.util.PasswordUtils;
import com.xianyu.auto.system.entity.SysUser;
import com.xianyu.auto.system.service.SysConfigService;
import com.xianyu.auto.system.service.SysUserService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.CommandLineRunner;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

/**
 * 数据初始化器：首次启动时创建默认管理员账号
 *
 * <p>判断逻辑：t_sys_user 表中如果没有 admin 账号，则用 DEFAULT_ADMIN_PASSWORD 环境变量创建
 */
@Slf4j
@Component
@RequiredArgsConstructor
@Order(1)
public class DataInitializer implements CommandLineRunner {

    private final SysUserService userService;
    private final SysConfigService configService;
    private final AesConfig aesConfig;

    @Override
    public void run(String... args) {
        initAdminUser();
        initDefaultConfigs();
    }

    private void initAdminUser() {
        SysUser existing = userService.findByUsername(CommonConstants.DEFAULT_ADMIN_USERNAME);
        if (existing != null) {
            log.info("[DataInit] admin 账号已存在，跳过初始化");
            return;
        }
        String password = aesConfig.getDefaultAdminPassword();
        if (password == null || password.isEmpty()) {
            password = "admin123";
        }
        SysUser admin = new SysUser();
        admin.setUsername(CommonConstants.DEFAULT_ADMIN_USERNAME);
        admin.setPasswordHash(PasswordUtils.hash(password));
        admin.setNickname("超级管理员");
        admin.setRole(CommonConstants.DEFAULT_ADMIN_ROLE);
        admin.setStatus(1);
        admin.setCreatedAt(DateUtils.nowMillis());
        admin.setUpdatedAt(DateUtils.nowMillis());
        userService.save(admin);
        log.info("[DataInit] 初始化默认 admin 账号成功（密码：{}），请尽快修改！", password);
    }

    private void initDefaultConfigs() {
        // 清掉 schema.sql 中插入的占位行
        configService.deleteByKey("system.init.admin.password");
    }
}
