package com.example.ambiguity.agent.tool;

import com.example.ambiguity.dto.ReviewDtos.HistoryItem;
import com.example.ambiguity.service.ReviewService;
import org.springframework.stereotype.Component;

import java.util.*;

/**
 * 只读工具：列出审查档案摘要（创建时间倒序）。
 */
@Component
public class ListReviewsTool implements Tool {
  private final ReviewService reviews;

  public ListReviewsTool(ReviewService reviews) {
    this.reviews = reviews;
  }

  @Override
  public ToolSpec spec() {
    Map<String, Object> properties = new LinkedHashMap<>();
    properties.put("limit", Map.of("type", "integer", "minimum", 1, "maximum", 20, "default", 5,
        "description", "返回条数，1-20"));
    properties.put("riskLevel", Map.of("type", "string", "enum", List.of("all", "high", "medium", "low"),
        "default", "all", "description", "按总体风险过滤"));
    Map<String, Object> schema = new LinkedHashMap<>();
    schema.put("type", "object");
    schema.put("properties", properties);
    schema.put("required", List.of());
    schema.put("additionalProperties", false);
    return new ToolSpec("list_reviews", "列出审查档案摘要（按创建时间倒序），用于回答“有哪些档案、最近几条是什么”。", schema);
  }

  @Override
  public Map<String, Object> execute(Map<String, Object> args) {
    int limit = (Integer) args.getOrDefault("limit", 5);
    String risk = String.valueOf(args.getOrDefault("riskLevel", "all"));
    List<HistoryItem> matched = reviews.history().stream()
        .filter(item -> "all".equals(risk) || risk.equals(item.riskLevel()))
        .toList();
    List<Map<String, Object>> rows = matched.stream().limit(limit).map(item -> {
      Map<String, Object> row = new LinkedHashMap<>();
      row.put("id", item.id());
      row.put("createdAt", item.createdAt());
      row.put("summary", item.summary());
      row.put("riskLevel", item.riskLevel());
      row.put("counts", item.counts());
      return row;
    }).toList();

    Map<String, Object> result = new LinkedHashMap<>();
    result.put("filteredTotal", matched.size());
    result.put("returned", rows.size());
    result.put("items", rows);
    return result;
  }
}