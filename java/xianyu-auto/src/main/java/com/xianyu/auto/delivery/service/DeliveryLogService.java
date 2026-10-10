package com.xianyu.auto.delivery.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.xianyu.auto.delivery.entity.DeliveryLog;

public interface DeliveryLogService extends IService<DeliveryLog> {

    /**
     * 同一账号下该订单是否已成功发货（幂等）
     */
    boolean existsSuccessByOrderId(Long accountId, String orderId);
}
