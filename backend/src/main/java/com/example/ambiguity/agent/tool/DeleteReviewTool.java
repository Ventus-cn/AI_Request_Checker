package com.example.ambiguity.agent.tool;

import com.example.ambiguity.service.ReviewService;
import org.springframework.stereotype.Component;

import java.util.*;

/**
 * 写操作工具：删除一条审查档案。
 * 属于修改数据的调用，必须由 Harness 暂停并取得用户确认后才能执行。
 */
@Component
public class DeleteReviewTool implements Tool {
  private final ReviewService reviews;

  public DeleteReviewTool(ReviewService reviews) {
    this.reviews = reviews;
  }

  @Override
  public ToolSpec spec() {
    Map<String, Object> properties = new LinkedHashMap<>();
    properties.put("id", Map.of("type", "string", "pattern", "^[0-9a-fA-F-]{36}$",
        "description", "要删除的档案 UUID"));
    Map<String, Object> schema = new LinkedHashMap<>();
    schema.put("type", "object");
    schema.put("properties", properties);
    schema.put("required", List.of("id"));
    schema.put("additionalProperties", false);
    return new ToolSpec("delete_review", "删除一条审查档案（写操作）。执行前必须由用户确认，确认前不得调用。", schema);
  }

  @Override
  public boolean requiresConfirmation() {
    return true;
  }

  @Override
  public String describeImpact(Map<String, Object> args) {
    String id = String.valueOf(args.get("id"));
    try {
      var review = reviews.get(UUID.fromString(id));
      String summary = String.valueOf(review.report().getOrDefault("summary", ""));
      if (summary.length() > 60) summary = summary.substring(0, 60) + "…";
      return "将永久删除档案 " + id.substring(0, 8) + "（创建于 " + review.createdAt() + "，摘要：" + summary + "），删除后不可恢复。";
    } catch (Exception e) {
      return "将永久删除档案 " + id + "，删除后不可恢复。";
    }
  }

  @Override
  public Map<String, Object> execute(Map<String, Object> args) {
    UUID id;
    try {
      id = UUID.fromString(String.valueOf(args.get("id")));
    } catch (IllegalArgumentException e) {
      throw new ToolException(ToolException.ARG_INVALID, "id 必须是 UUID：" + args.get("id"));
    }
    try {
      reviews.delete(id);
    } catch (NoSuchElementException e) {
      throw new ToolException(ToolException.NOT_FOUND, "审查记录不存在：" + id);
    }
    Map<String, Object> result = new LinkedHashMap<>();
    result.put("deleted", true);
    result.put("id", id.toString());
    return result;
  }
}