package com.xianyu.auto.product.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.xianyu.auto.product.entity.Product;
import com.xianyu.auto.product.mapper.ProductMapper;
import com.xianyu.auto.product.service.ProductService;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class ProductServiceImpl extends ServiceImpl<ProductMapper, Product> implements ProductService {

    @Override
    public Product getByXianyuItemId(String itemId) {
        return this.baseMapper.selectOne(new LambdaQueryWrapper<Product>()
                .eq(Product::getXianyuItemId, itemId)
                .eq(Product::getStatus, Product.STATUS_ENABLED));
    }
}
