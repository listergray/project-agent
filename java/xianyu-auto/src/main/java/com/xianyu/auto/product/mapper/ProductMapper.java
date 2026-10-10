package com.xianyu.auto.product.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.xianyu.auto.product.entity.Product;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface ProductMapper extends BaseMapper<Product> {
}
