package com.xianyu.auto;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * 闲鱼自动发货系统启动类
 */
@SpringBootApplication
@MapperScan("com.xianyu.auto.**.mapper")
@EnableScheduling
@EnableAsync
public class XianyuAutoApplication {

    public static void main(String[] args) {
        SpringApplication.run(XianyuAutoApplication.class, args);
    }
}
