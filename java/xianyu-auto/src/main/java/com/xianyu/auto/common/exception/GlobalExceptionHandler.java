package com.xianyu.auto.common.exception;

import cn.dev33.satoken.exception.NotLoginException;
import cn.dev33.satoken.exception.NotPermissionException;
import cn.dev33.satoken.exception.NotRoleException;
import com.xianyu.auto.common.api.CommonResult;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.ConstraintViolationException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.BindException;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.util.stream.Collectors;

/**
 * 全局异常处理器
 */
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    /**
     * 业务异常
     */
    @ExceptionHandler(BusinessException.class)
    public CommonResult<Void> handleBusinessException(BusinessException e) {
        log.warn("[BusinessException] code={}, message={}", e.getCode(), e.getMessage());
        return CommonResult.error(e.getCode(), e.getMessage());
    }

    /**
     * 未登录
     */
    @ExceptionHandler(NotLoginException.class)
    public ResponseEntity<CommonResult<Void>> handleNotLogin(NotLoginException e) {
        log.warn("[NotLoginException] {}", e.getMessage());
        return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                .body(CommonResult.error(401, "未登录或登录已过期"));
    }

    /**
     * 无权限
     */
    @ExceptionHandler(NotPermissionException.class)
    public ResponseEntity<CommonResult<Void>> handleNotPermission(NotPermissionException e) {
        log.warn("[NotPermissionException] {}", e.getMessage());
        return ResponseEntity.status(HttpStatus.FORBIDDEN)
                .body(CommonResult.error(403, "无权限：" + e.getMessage()));
    }

    /**
     * 无角色
     */
    @ExceptionHandler(NotRoleException.class)
    public ResponseEntity<CommonResult<Void>> handleNotRole(NotRoleException e) {
        log.warn("[NotRoleException] {}", e.getMessage());
        return ResponseEntity.status(HttpStatus.FORBIDDEN)
                .body(CommonResult.error(403, "无角色权限"));
    }

    /**
     * 参数校验失败 - @RequestBody @Valid
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public CommonResult<Void> handleMethodArgNotValid(MethodArgumentNotValidException e) {
        String msg = e.getBindingResult().getFieldErrors().stream()
                .map(fe -> fe.getField() + ": " + fe.getDefaultMessage())
                .collect(Collectors.joining("; "));
        log.warn("[MethodArgumentNotValidException] {}", msg);
        return CommonResult.error(400, "参数校验失败: " + msg);
    }

    /**
     * 参数校验失败 - 表单绑定
     */
    @ExceptionHandler(BindException.class)
    public CommonResult<Void> handleBindException(BindException e) {
        String msg = e.getBindingResult().getFieldErrors().stream()
                .map(FieldError::getDefaultMessage)
                .collect(Collectors.joining("; "));
        log.warn("[BindException] {}", msg);
        return CommonResult.error(400, "参数校验失败: " + msg);
    }

    /**
     * 参数校验失败 - @RequestParam @PathVariable
     */
    @ExceptionHandler(ConstraintViolationException.class)
    public CommonResult<Void> handleConstraintViolation(ConstraintViolationException e) {
        String msg = e.getConstraintViolations().stream()
                .map(ConstraintViolation::getMessage)
                .collect(Collectors.joining("; "));
        log.warn("[ConstraintViolationException] {}", msg);
        return CommonResult.error(400, "参数校验失败: " + msg);
    }

    /**
     * 缺少必填参数
     */
    @ExceptionHandler(MissingServletRequestParameterException.class)
    public CommonResult<Void> handleMissingParam(MissingServletRequestParameterException e) {
        return CommonResult.error(400, "缺少必填参数: " + e.getParameterName());
    }

    /**
     * 兜底异常
     */
    @ExceptionHandler(Exception.class)
    public CommonResult<Void> handleException(Exception e) {
        log.error("[未捕获异常]", e);
        return CommonResult.error(500, "系统异常: " + e.getMessage());
    }
}
