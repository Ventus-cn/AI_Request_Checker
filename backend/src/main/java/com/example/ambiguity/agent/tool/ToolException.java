package com.example.ambiguity.agent.tool;

/**
 * 工具调用失败。errorType 使用实验方案 5.2 节的错误分类，直接回传模型并写入运行日志。
 */
public class ToolException extends RuntimeException {
  public static final String ARG_INVALID = "ARG_INVALID";
  public static final String NOT_FOUND = "NOT_FOUND";
  public static final String TOOL_EXCEPTION = "TOOL_EXCEPTION";
  public static final String TIMEOUT = "TIMEOUT";
  public static final String POLICY_DENIED = "POLICY_DENIED";
  public static final String STATE_UNKNOWN = "STATE_UNKNOWN";

  private final String errorType;

  public ToolException(String errorType, String message) {
    super(message);
    this.errorType = errorType;
  }

  public String errorType() {
    return errorType;
  }
}