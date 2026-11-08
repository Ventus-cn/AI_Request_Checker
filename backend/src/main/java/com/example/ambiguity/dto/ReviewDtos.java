package com.example.ambiguity.dto;

import java.util.*;

public final class ReviewDtos {
  private ReviewDtos() {}
  public record ReviewRequest(String text, String mode, String promptVersion, DocumentSource document) {
    public ReviewRequest(String text, String mode) { this(text, mode, "revised", null); }
    public ReviewRequest(String text, String mode, String promptVersion) { this(text, mode, promptVersion, null); }
  }
  public record FollowUpRequest(String question) {}
  public record DocumentSource(String fileName, int visualCount, int recognizedVisuals, String visualKind, List<String> warnings) {}
  public record ParseResponse(String fileName, String text, int characters, DocumentSource document) {}
  public record ReviewResponse(String id, String text, String mode, String createdAt, Map<String,Object> report, List<Map<String,Object>> versions) {}
  public record HistoryItem(String id, String createdAt, String summary, String riskLevel, Map<String,Object> counts) {}
}
