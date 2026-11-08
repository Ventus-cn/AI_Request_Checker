package com.example.ambiguity.agent.tool;

import com.example.ambiguity.model.Review;
import com.example.ambiguity.repository.ReviewRepository;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Component;

import java.time.Instant;
import java.util.*;

/**
 * 只读工具：统计审查档案的高/中/低风险数量与问题类型分布。
 * 统计结果由后端聚合，模型只能引用，不能自行编造数字。
 */
@Component
public class ComputeRiskStatsTool implements Tool {
  private final ReviewRepository repository;
  private final ObjectMapper mapper = new ObjectMapper();

  public ComputeRiskStatsTool(ReviewRepository repository) {
    this.repository = repository;
  }

  @Override
  public ToolSpec spec() {
    Map<String, Object> properties = new LinkedHashMap<>();
    properties.put("mode", Map.of("type", "string",
        "enum", List.of("all", "全面审查", "可测试性", "安全与权限"),
        "default", "all", "description", "按审查视角过滤，all 表示全部"));
    Map<String, Object> schema = new LinkedHashMap<>();
    schema.put("type", "object");
    schema.put("properties", properties);
    schema.put("required", List.of());
    schema.put("additionalProperties", false);
    return new ToolSpec("compute_risk_stats", "统计审查档案的总数、高/中/低风险数量与问题类型分布，是回答统计类问题的唯一数据来源。", schema);
  }

  @Override
  public Map<String, Object> execute(Map<String, Object> args) {
    String mode = String.valueOf(args.getOrDefault("mode", "all"));
    List<Review> all = repository.findAll();
    List<Review> selected = "all".equals(mode) ? all
        : all.stream().filter(review -> mode.equals(review.getMode())).toList();

    int high = 0, medium = 0, low = 0, issueTotal = 0;
    Map<String, Integer> byType = new TreeMap<>();
    Instant latest = null;
    for (Review review : selected) {
      try {
        Map<String, Object> report = mapper.readValue(review.getReportJson(),
            new TypeReference<Map<String, Object>>() {});
        String risk = String.valueOf(report.getOrDefault("riskLevel", "low"));
        switch (risk) {
          case "high" -> high++;
          case "medium" -> medium++;
          default -> low++;
        }
        if (report.get("issues") instanceof List<?> issues) {
          for (Object value : issues) {
            if (value instanceof Map<?, ?> issue) {
              issueTotal++;
              Object type = issue.get("type");
              byType.merge(type == null ? "unknown" : String.valueOf(type), 1, Integer::sum);
            }
          }
        }
        if (latest == null || review.getCreatedAt().isAfter(latest)) latest = review.getCreatedAt();
      } catch (Exception e) {
        throw new ToolException(ToolException.TOOL_EXCEPTION,
            "档案 " + review.getId() + " 的报告无法解析");
      }
    }

    List<Map<String, Object>> typeRows = byType.entrySet().stream()
        .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
        .map(entry -> {
          Map<String, Object> row = new LinkedHashMap<String, Object>();
          row.put("type", entry.getKey());
          row.put("count", entry.getValue());
          return row;
        })
        .toList();

    Map<String, Object> result = new LinkedHashMap<>();
    result.put("mode", mode);
    result.put("total", selected.size());
    result.put("high", high);
    result.put("medium", medium);
    result.put("low", low);
    result.put("issueTotal", issueTotal);
    result.put("byType", typeRows);
    result.put("latestAt", latest == null ? "" : latest.toString());
    return result;
  }
}