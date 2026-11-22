package com.example.ambiguity.acceptance.dto;

import java.util.List;

public final class AcceptanceDtos {
  private AcceptanceDtos() {}

  public record RunRequest(String text, String promptVersion, String mode) {}

  public record Criterion(String id, String title, String given, String when, String then,
                          String sourceQuote, String priority) {}

  public record TestSample(String id, String kind, String input, String expected, String sourceQuote) {}

  public record Report(String summary,
                       List<Criterion> acceptanceCriteria,
                       List<TestSample> testSamples,
                       List<String> openQuestions) {}

  public record Usage(int promptTokens, int completionTokens, int totalTokens) {}

  public record RunResponse(String runId, String status, String promptVersion, String model,
                            long durationMs, Usage usage, Report report, String error) {}
}