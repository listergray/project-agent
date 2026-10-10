package com.xianyu.auto.config;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

/**
 * Prevent browsers / iframes from sticky-caching SPA shell (index.html).
 * Hashed /assets/* remain cacheable.
 */
@Component
@Order(Ordered.HIGHEST_PRECEDENCE + 20)
public class SpaCacheConfig extends OncePerRequestFilter {

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {
        String path = request.getRequestURI();
        boolean spaShell = "/".equals(path) || "/index.html".equals(path)
                || (path != null && !path.startsWith("/api/") && !path.contains("."));
        if (spaShell) {
            response.setHeader("Cache-Control", "no-store, no-cache, must-revalidate");
            response.setHeader("Pragma", "no-cache");
        }
        filterChain.doFilter(request, response);
    }
}
