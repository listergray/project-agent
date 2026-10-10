package com.xianyu.auto.common.util;

import java.time.Duration;
import java.time.Instant;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;

/**
 * 时间工具类
 */
public class DateUtils {

    private static final ZoneId ZONE = ZoneId.of("Asia/Shanghai");
    private static final DateTimeFormatter DEFAULT_FMT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final DateTimeFormatter DATE_FMT = DateTimeFormatter.ofPattern("yyyy-MM-dd");

    public static long nowMillis() {
        return System.currentTimeMillis();
    }

    public static LocalDateTime toLocalDateTime(Long millis) {
        if (millis == null) return null;
        return LocalDateTime.ofInstant(Instant.ofEpochMilli(millis), ZONE);
    }

    public static String format(Long millis) {
        if (millis == null) return null;
        return toLocalDateTime(millis).format(DEFAULT_FMT);
    }

    public static String formatDate(Long millis) {
        if (millis == null) return null;
        return toLocalDateTime(millis).format(DATE_FMT);
    }

    public static String formatDuration(Long startMillis, Long endMillis) {
        if (startMillis == null || endMillis == null) return null;
        long seconds = Duration.between(
                Instant.ofEpochMilli(startMillis),
                Instant.ofEpochMilli(endMillis)
        ).getSeconds();
        if (seconds < 60) return seconds + "秒";
        if (seconds < 3600) return (seconds / 60) + "分" + (seconds % 60) + "秒";
        return (seconds / 3600) + "时" + ((seconds % 3600) / 60) + "分";
    }
}
