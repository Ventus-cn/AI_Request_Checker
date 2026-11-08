package com.example.ambiguity.agent.dto;

import java.util.List;

/**
 * Agent 对外传输对象。字段与实验方案第 6.1 节的接口契约一致。
 */
public final class AgentDtos {
  private AgentDtos() {}

  public record RunRequest(String question) {}

  public record ConfirmRequest(Boolean approved) {}

  public record StepView(int index, String tool, String args, String resultPreview, String status, long durationMs) {}

  public record ConfirmView(String tool, String impact) {}

  public record RunResponse(String taskId, String status, String answer,
                            List<StepView> steps, ConfirmView confirm, String error) {}
}