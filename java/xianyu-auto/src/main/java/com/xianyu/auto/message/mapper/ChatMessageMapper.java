package com.xianyu.auto.message.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.xianyu.auto.message.entity.ChatMessage;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface ChatMessageMapper extends BaseMapper<ChatMessage> {
}
