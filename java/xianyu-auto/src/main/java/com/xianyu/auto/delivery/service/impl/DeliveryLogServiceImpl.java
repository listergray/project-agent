package com.xianyu.auto.delivery.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.xianyu.auto.delivery.entity.DeliveryLog;
import com.xianyu.auto.delivery.mapper.DeliveryLogMapper;
import com.xianyu.auto.delivery.service.DeliveryLogService;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

@Service
public class DeliveryLogServiceImpl extends ServiceImpl<DeliveryLogMapper, DeliveryLog> implements DeliveryLogService {

    @Override
    public boolean existsSuccessByOrderId(Long accountId, String orderId) {
        if (accountId == null || !StringUtils.hasText(orderId)) {
            return false;
        }
        Long count = this.count(new LambdaQueryWrapper<DeliveryLog>()
                .eq(DeliveryLog::getAccountId, accountId)
                .eq(DeliveryLog::getOrderId, orderId)
                .eq(DeliveryLog::getStatus, DeliveryLog.STATUS_SUCCESS));
        return count != null && count > 0;
    }
}
