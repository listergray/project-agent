package com.xianyu.auto.product.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.xianyu.auto.product.entity.Product;

public interface ProductService extends IService<Product> {

    Product getByXianyuItemId(String itemId);
}
