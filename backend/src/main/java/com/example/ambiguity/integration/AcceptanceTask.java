package com.example.ambiguity.integration;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

import java.time.Instant;

/**
 * 一次“验收标准生成”任务。界面提交后立即返回任务编号，模型调用在后台线程执行；
 * 状态、阶段、结果、错误与人工处理决定全部落库，刷新页面或重启后端后可恢复。
 */
@Entity
@Table(name = "acceptance_tasks")
public class AcceptanceTask {
  @Id
  @Column(length = 40)
  private String id;

  /** 来源审查档案；为空表示从独立输入框发起。 */
  @Column(length = 40)
  private String reviewId;

  @Column(columnDefinition = "TEXT")
  private String inputText;

  @Column(length = 32)
  private String promptVersion;

  /** model / rule / manual：模型、规则流程、人工填写。 */
  @Column(length = 16)
  private String mode;

  @Column(length = 32)
  private String model;

  /** QUEUED / RUNNING / SUCCEEDED / FAILED / CHECK_FAILED / REFUSED / CANCELLED。 */
  @Column(length = 20)
  private String status;

  /** 界面可见的阶段说明，例如“调用模型（第 2 次）”，不编造百分比。 */
  @Column(length = 120)
  private String phase;

  /** PENDING / ACCEPTED / DISCARDED / MANUAL。 */
  @Column(length = 16)
  private String decision;

  @Column(columnDefinition = "TEXT")
  private String resultJson;

  @Column(columnDefinition = "TEXT")
  private String checksJson;

  /** 提交时快照的检索依据（来自审查档案的 RAG 片段），用于展示来源。 */
  @Column(columnDefinition = "TEXT")
  private String sourcesJson;

  @Column(length = 40)
  private String errorCode;

  @Column(columnDefinition = "TEXT")
  private String errorMessage;

  private boolean degraded;

  @Column(length = 200)
  private String degradeReason;

  private boolean edited;

  private boolean cancelRequested;

  private int attempts;

  private long durationMs;

  private int promptTokens;

  private int completionTokens;

  @Column(length = 200)
  private String dedupeKey;

  @Column(length = 40)
  private String retryOf;

  private Instant createdAt;

  private Instant startedAt;

  private Instant finishedAt;

  private Instant appliedAt;

  protected AcceptanceTask() {}

  public AcceptanceTask(String id, String reviewId, String inputText, String promptVersion,
                        String mode, String model, String dedupeKey, String retryOf) {
    this.id = id;
    this.reviewId = reviewId;
    this.inputText = inputText;
    this.promptVersion = promptVersion;
    this.mode = mode;
    this.model = model;
    this.dedupeKey = dedupeKey;
    this.retryOf = retryOf;
    this.status = TaskStatus.QUEUED;
    this.phase = "排队等待";
    this.decision = "PENDING";
    this.createdAt = Instant.now();
  }

  public String getId() { return id; }
  public String getReviewId() { return reviewId; }
  public String getInputText() { return inputText; }
  public String getPromptVersion() { return promptVersion; }
  public String getMode() { return mode; }
  public String getModel() { return model; }
  public void setModel(String model) { this.model = model; }
  public String getStatus() { return status; }
  public void setStatus(String status) { this.status = status; }
  public String getPhase() { return phase; }
  public void setPhase(String phase) { this.phase = phase; }
  public String getDecision() { return decision; }
  public void setDecision(String decision) { this.decision = decision; }
  public String getResultJson() { return resultJson; }
  public void setResultJson(String resultJson) { this.resultJson = resultJson; }
  public String getChecksJson() { return checksJson; }
  public void setChecksJson(String checksJson) { this.checksJson = checksJson; }
  public String getSourcesJson() { return sourcesJson; }
  public void setSourcesJson(String sourcesJson) { this.sourcesJson = sourcesJson; }
  public String getErrorCode() { return errorCode; }
  public void setErrorCode(String errorCode) { this.errorCode = errorCode; }
  public String getErrorMessage() { return errorMessage; }
  public void setErrorMessage(String errorMessage) { this.errorMessage = errorMessage; }
  public boolean isDegraded() { return degraded; }
  public void setDegraded(boolean degraded) { this.degraded = degraded; }
  public String getDegradeReason() { return degradeReason; }
  public void setDegradeReason(String degradeReason) { this.degradeReason = degradeReason; }
  public boolean isEdited() { return edited; }
  public void setEdited(boolean edited) { this.edited = edited; }
  public boolean isCancelRequested() { return cancelRequested; }
  public void setCancelRequested(boolean cancelRequested) { this.cancelRequested = cancelRequested; }
  public int getAttempts() { return attempts; }
  public void setAttempts(int attempts) { this.attempts = attempts; }
  public long getDurationMs() { return durationMs; }
  public void setDurationMs(long durationMs) { this.durationMs = durationMs; }
  public int getPromptTokens() { return promptTokens; }
  public void setPromptTokens(int promptTokens) { this.promptTokens = promptTokens; }
  public int getCompletionTokens() { return completionTokens; }
  public void setCompletionTokens(int completionTokens) { this.completionTokens = completionTokens; }
  public String getDedupeKey() { return dedupeKey; }
  public String getRetryOf() { return retryOf; }
  public Instant getCreatedAt() { return createdAt; }
  public Instant getStartedAt() { return startedAt; }
  public void setStartedAt(Instant startedAt) { this.startedAt = startedAt; }
  public Instant getFinishedAt() { return finishedAt; }
  public void setFinishedAt(Instant finishedAt) { this.finishedAt = finishedAt; }
  public Instant getAppliedAt() { return appliedAt; }
  public void setAppliedAt(Instant appliedAt) { this.appliedAt = appliedAt; }

  public boolean isSaved() { return appliedAt != null; }
}