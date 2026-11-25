package com.example.ambiguity.integration;

import com.example.ambiguity.acceptance.dto.AcceptanceDtos.Checks;
import com.example.ambiguity.acceptance.dto.AcceptanceDtos.Report;

import java.util.List;

/** 任务接口的统一字段：界面、业务层、AI 模块共用同一套名称、状态和错误码。 */
public final class TaskDtos {
  private TaskDtos() {}

  /** 提交：reviewId 优先；没有档案时用 text。mode 可选 model/rule/manual。 */
  public record SubmitRequest(String reviewId, String text, String promptVersion, String mode) {}

  /** 人工修改后的完整结果。 */
  public record EditRequest(Report report) {}

  public record SourceRef(String id, String source, String title, double score, String text) {}

  public record TaskView(
      String taskId,
      String reviewId,
      String status,
      String statusLabel,
      String phase,
      String promptVersion,
      String mode,
      String model,
      boolean degraded,
      String degradeReason,
      String errorCode,
      String errorMessage,
      boolean retryable,
      boolean duplicate,
      int attempts,
      long durationMs,
      int promptTokens,
      int completionTokens,
      String createdAt,
      String startedAt,
      String finishedAt,
      boolean cancelRequested,
      String decision,
      boolean edited,
      boolean saved,
      String savedAt,
      String retryOf,
      Report report,
      Checks checks,
      List<SourceRef> sources,
      List<String> actions) {

    public TaskView withDuplicate(boolean value) {
      return new TaskView(taskId, reviewId, status, statusLabel, phase, promptVersion, mode, model,
          degraded, degradeReason, errorCode, errorMessage, retryable, value, attempts, durationMs,
          promptTokens, completionTokens, createdAt, startedAt, finishedAt, cancelRequested,
          decision, edited, saved, savedAt, retryOf, report, checks, sources, actions);
    }
  }

  public record ApplyResponse(TaskView task, String reviewId, String acceptanceTaskId) {}
}