package com.xianyu.auto.reply.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Data
@Configuration
@ConfigurationProperties(prefix = "xianyu.reply")
public class ReplyProperties {

    /** ?????????? */
    private Integer delayMinSec = 3;

    /** ?????????? */
    private Integer delayMaxSec = 7;

    public int randomDelayMs() {
        int min = delayMinSec == null || delayMinSec < 0 ? 0 : delayMinSec;
        int max = delayMaxSec == null || delayMaxSec < min ? min : delayMaxSec;
        if (max == 0) return 0;
        int sec = min + (int) (Math.random() * (max - min + 1));
        return sec * 1000;
    }
}
