package com.example.ambiguity.agent.tool;

import com.example.ambiguity.dto.ReviewDtos.ReviewResponse;
import com.example.ambiguity.service.ReviewService;
import org.springframework.stereotype.Component;

import java.util.*;

/**
 * 只读工具：按 ID 读取单条审查档案的摘要与问题明细（字段截断，避免上下文膨胀）。
 */
@Component
public class GetReviewDetailTool implements Tool {
  private final ReviewService reviews;

  public GetReviewDetailTool(ReviewService reviews) {
    this.reviews = reviews;
  }

  @Override
  public ToolSpec spec() {
    Map<String, Object> properties = new LinkedHashMap<>();
    properties.put("id", Map.of("type", "string", "pattern", "^[0-9a-fA-F-]{36}$",
        "description", "审查档案 UUID"));
    Map<String, Object> schema = new LinkedHashMap<>();
    schema.put("type", "object");
    schema.put("properties", properties);
    schema.put("required", List.of("id"));
    schema.put("additionalProperties", false);
    return new ToolSpec("get_review_detail", "读取单条审查档案的摘要、风险等级和问题明细，用于回答“这条档案讲了什么、最严重的问题是什么”。", schema);
  }

  @Override
  public Map<String, Object> execute(Map<String, Object> args) {
    UUID id;
    try {
      id = UUID.fromString(String.valueOf(args.get("id")));
    } catch (IllegalArgumentException e) {
      throw new ToolException(ToolException.ARG_INVALID, "id 必须是 UUID：" + args.get("id"));
    }
    ReviewResponse review;
    try {
      review = reviews.get(id);
    } catch (NoSuchElementException e) {
      throw new ToolException(ToolException.NOT_FOUND, "审查记录不存在：" + id);
    }
    Map<String, Object> report = review.report();

    List<Map<String, Object>> issues = new ArrayList<>();
    if (report.get("issues") instanceof List<?> list) {
      for (Object value : list) {
        if (!(value instanceof Map<?, ?> issue)) continue;
        Map<String, Object> row = new LinkedHashMap<>();
        row.put("id", issue.get("id"));
        row.put("type", issue.get("type"));
        row.put("severity", issue.get("severity"));
        row.put("quote", truncate(issue.get("quote"), 120));
        row.put("explanation", truncate(issue.get("explanation"), 200));
        row.put("questions", firstOf(issue.get("questions"), 3));
        row.put("acceptanceCriteria", firstOf(issue.get("acceptanceCriteria"), 3));
        issues.add(row);
      }
    }

    Map<String, Object> result = new LinkedHashMap<>();
    result.put("id", review.id());
    result.put("mode", review.mode());
    result.put("createdAt", review.createdAt());
    result.put("riskLevel", report.getOrDefault("riskLevel", "low"));
    result.put("summary", truncate(report.get("summary"), 300));
    result.put("versionCount", review.versions().size() + 1);
    result.put("issueCount", issues.size());
    result.put("issues", issues);
    return result;
  }

  private static String truncate(Object value, int max) {
    String text = value == null ? "" : String.valueOf(value);
    return text.length() <= max ? text : text.substring(0, max) + "…";
  }

  private static List<?> firstOf(Object value, int max) {
    if (!(value instanceof List<?> list) || list.isEmpty()) return List.of();
    return list.subList(0, Math.min(max, list.size()));
  }
}