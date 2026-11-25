package com.example.ambiguity.integration;

/** 任务状态常量与判定。状态只允许按图中方向迁移，终态只能通过新任务（重试/降级/人工）继续。 */
public final class TaskStatus {
  public static final String QUEUED = "QUEUED";
  public static final String RUNNING = "RUNNING";
  public static final String SUCCEEDED = "SUCCEEDED";
  public static final String FAILED = "FAILED";
  public static final String CHECK_FAILED = "CHECK_FAILED";
  public static final String REFUSED = "REFUSED";
  public static final String CANCELLED = "CANCELLED";

  private TaskStatus() {}

  public static boolean terminal(String status) {
    return !QUEUED.equals(status) && !RUNNING.equals(status);
  }

  public static String label(String status) {
    if (status == null) return "未知";
    return switch (status) {
      case QUEUED -> "排队中";
      case RUNNING -> "处理中";
      case SUCCEEDED -> "已生成";
      case FAILED -> "生成失败";
      case CHECK_FAILED -> "校验未通过";
      case REFUSED -> "已拒绝";
      case CANCELLED -> "已取消";
      default -> status;
    };
  }
}