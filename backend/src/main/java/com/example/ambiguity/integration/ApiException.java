package com.example.ambiguity.integration;

import java.util.List;

/**
 * 统一错误返回：code 供程序判断，error 供用户阅读，actions 给出下一步可选操作，
 * retryable 表示原操作是否可直接重试（写操作重试前需先核对执行状态）。
 */
public class ApiException extends RuntimeException {
  private final int status;
  private final String code;
  private final boolean retryable;
  private final List<String> actions;

  public ApiException(int status, String code, String message, boolean retryable, List<String> actions) {
    super(message);
    this.status = status;
    this.code = code;
    this.retryable = retryable;
    this.actions = actions == null ? List.of() : List.copyOf(actions);
  }

  public int getStatus() { return status; }
  public String getCode() { return code; }
  public boolean isRetryable() { return retryable; }
  public List<String> getActions() { return actions; }
}