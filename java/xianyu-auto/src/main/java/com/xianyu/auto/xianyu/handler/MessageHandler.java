package com.xianyu.auto.xianyu.handler;

import com.xianyu.auto.xianyu.protocol.LwpMessage;

/**
 * LWP 消息处理器接口
 * 实现类按 lwp 路径前缀匹配，处理对应消息
 */
public interface MessageHandler {

    /**
     * 是否处理该 lwp 路径的消息
     */
    boolean supports(String lwp);

    /**
     * 处理消息
     *
     * @param accountId 关联的闲鱼账号 ID
     * @param message   LWP 消息
     */
    void handle(Long accountId, LwpMessage message);
}
