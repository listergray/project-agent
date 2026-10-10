package com.xianyu.auto.system.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.xianyu.auto.common.api.PageResult;
import com.xianyu.auto.common.exception.BusinessException;
import com.xianyu.auto.common.util.DateUtils;
import com.xianyu.auto.common.util.PasswordUtils;
import com.xianyu.auto.system.entity.SysUser;
import com.xianyu.auto.system.mapper.SysUserMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.util.List;

/**
 * 系统用户服务
 */
@Slf4j
@Service
public class SysUserService extends ServiceImpl<SysUserMapper, SysUser> {

    /**
     * 根据用户名查找用户（含密码 hash，用于登录）
     */
    public SysUser findByUsername(String username) {
        return baseMapper.selectOne(new LambdaQueryWrapper<SysUser>()
                .eq(SysUser::getUsername, username));
    }

    /**
     * 分页查询
     */
    public PageResult<SysUser> page(Integer pageNo, Integer pageSize, String keyword) {
        Page<SysUser> page = new Page<>(pageNo, pageSize);
        LambdaQueryWrapper<SysUser> wrapper = new LambdaQueryWrapper<>();
        if (StringUtils.hasText(keyword)) {
            wrapper.like(SysUser::getUsername, keyword)
                    .or().like(SysUser::getNickname, keyword)
                    .or().like(SysUser::getEmail, keyword);
        }
        wrapper.orderByDesc(SysUser::getCreatedAt);
        IPage<SysUser> result = baseMapper.selectPage(page, wrapper);
        return new PageResult<>(result.getRecords(), result.getTotal());
    }

    public void createUser(SysUser user) {
        if (!StringUtils.hasText(user.getUsername()) || !StringUtils.hasText(user.getPasswordHash())) {
            throw new BusinessException("用户名和密码不能为空");
        }
        // passwordHash 字段临时接收明文密码（前端传来的是明文）
        String plainPassword = user.getPasswordHash();
        if (findByUsername(user.getUsername()) != null) {
            throw new BusinessException("用户名已存在");
        }
        if (!StringUtils.hasText(user.getRole())) {
            user.setRole("USER");
        }
        user.setPasswordHash(PasswordUtils.hash(plainPassword));
        user.setStatus(1);
        user.setCreatedAt(DateUtils.nowMillis());
        user.setUpdatedAt(DateUtils.nowMillis());
        baseMapper.insert(user);
    }

    public void updateUser(SysUser user) {
        SysUser existing = baseMapper.selectById(user.getId());
        if (existing == null) {
            throw new BusinessException("用户不存在");
        }
        existing.setNickname(user.getNickname());
        existing.setEmail(user.getEmail());
        existing.setPhone(user.getPhone());
        existing.setRole(user.getRole());
        existing.setStatus(user.getStatus());
        existing.setUpdatedAt(DateUtils.nowMillis());
        baseMapper.updateById(existing);
    }

    /**
     * 修改密码
     */
    public void changePassword(Long userId, String oldPassword, String newPassword) {
        SysUser user = baseMapper.selectById(userId);
        if (user == null) {
            throw new BusinessException("用户不存在");
        }
        if (!PasswordUtils.verify(oldPassword, user.getPasswordHash())) {
            throw new BusinessException("原密码错误");
        }
        if (!StringUtils.hasText(newPassword) || newPassword.length() < 6) {
            throw new BusinessException("新密码长度不能少于 6 位");
        }
        user.setPasswordHash(PasswordUtils.hash(newPassword));
        user.setUpdatedAt(DateUtils.nowMillis());
        baseMapper.updateById(user);
    }

    /**
     * 管理员重置密码
     */
    public void resetPassword(Long userId, String newPassword) {
        SysUser user = baseMapper.selectById(userId);
        if (user == null) {
            throw new BusinessException("用户不存在");
        }
        if (!StringUtils.hasText(newPassword) || newPassword.length() < 6) {
            throw new BusinessException("密码长度不能少于 6 位");
        }
        user.setPasswordHash(PasswordUtils.hash(newPassword));
        user.setUpdatedAt(DateUtils.nowMillis());
        baseMapper.updateById(user);
    }

    public void deleteUsers(List<Long> ids) {
        if (ids == null || ids.isEmpty()) return;
        baseMapper.deleteBatchIds(ids);
    }
}
