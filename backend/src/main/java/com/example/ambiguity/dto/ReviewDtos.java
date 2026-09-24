package com.example.ambiguity.dto;

import java.util.*;

public final class ReviewDtos {
  private ReviewDtos() {}
  public record ReviewRequest(String text, String mode) {}
  public record FollowUpRequest(String question) {}
  public record ParseResponse(String fileName, String text, int characters) {}
  public record ReviewResponse(String id, String text, String mode, String createdAt, Map<String,Object> report, List<Map<String,Object>> versions) {}
  public record HistoryItem(String id, String createdAt, String summary, String riskLevel, Map<String,Object> counts) {}
}
