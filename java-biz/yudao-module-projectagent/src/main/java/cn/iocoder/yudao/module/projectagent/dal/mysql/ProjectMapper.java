package cn.iocoder.yudao.module.projectagent.dal.mysql;

import cn.iocoder.yudao.module.projectagent.dal.dataobject.ProjectDO;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface ProjectMapper extends BaseMapper<ProjectDO> {
}
