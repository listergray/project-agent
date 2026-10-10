package com.xianyu.auto.xianyu.handler;

import com.xianyu.auto.xianyu.protocol.LwpMessage;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * 消息处理器注册表
 * 持有所有 MessageHandler 实现，按 lwp 路径分发
 */
@Slf4j
@Component
public class MessageHandlerRegistry {

    private final List<MessageHandler> handlers;

    public MessageHandlerRegistry(List<MessageHandler> handlers) {
        this.handlers = handlers;
        log.info("注册消息处理器: {} 个", handlers.size());
    }

    /**
     * 分发消息给所有匹配的 handler
     */
    public void dispatch(Long accountId, LwpMessage message) {
        if (message == null) {
            return;
        }
        // 无 lwp 的 syncPush：强制交给 SyncPushMessageHandler
        String lwp = message.getLwp();
        if (lwp == null && message.isSyncPushPackage()) {
            lwp = "/s/sync";
        }
        if (lwp == null) {
            return;
        }
        for (MessageHandler handler : handlers) {
            try {
                if (handler.supports(lwp)) {
                    handler.handle(accountId, message);
                }
            } catch (Exception e) {
                log.error("处理器异常: handler={}, lwp={}, error={}",
                        handler.getClass().getSimpleName(), lwp, e.getMessage(), e);
            }
        }
    }
}
