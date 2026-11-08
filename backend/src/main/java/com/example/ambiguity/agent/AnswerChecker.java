package com.example.ambiguity.agent;

import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Pattern;

/**
 * 结果检查：由程序核对最终回答是否与工具结果一致，不采信模型“已完成”的自述。
 */
@Component
public class AnswerChecker {
  public record Result(boolean ok, String reason, String repairMessage) {
  }

  public Result check(AgentRun run, String answer) {
    String text = answer == null ? "" : answer;
    if (run.lastStats != null) {
      List<String> missing = new ArrayList<>();
      for (String key : List.of("total", "high", "medium", "low")) {
        Object value = run.lastStats.get(key);
        if (value == null) continue;
        String number = String.valueOf(value);
        if (!containsNumber(text, number)) missing.add(label(key) + number);
      }
      if (!missing.isEmpty()) {
        return new Result(false, "回答缺少统计数字：" + String.join("、", missing),
            "你的回答缺少工具返回的统计数字（" + String.join("、", missing)
                + "），请补充并保证与 compute_risk_stats 的结果完全一致。");
      }
    }
    if (run.lastKnowledgeCount > 0 && !text.matches("(?s).*KB-\\d+.*")) {
      return new Result(false, "回答未引用知识库片段编号",
          "你使用了知识库检索结果但没有标注来源编号，请用 [KB-xxx] 标注引用。");
    }
    if (run.lastKnowledgeCount == 0 && text.matches("(?s).*KB-\\d+.*")) {
      return new Result(false, "回答引用了未检索的知识库编号",
          "你这次没有调用 search_knowledge，却引用了 KB 编号，属于无依据引用。请删除该编号，或先调用 search_knowledge 再引用。");
    }
    return new Result(true, "ok", "");
  }

  private static boolean containsNumber(String text, String number) {
    return Pattern.compile("(?<!\\d)" + Pattern.quote(number) + "(?!\\d)").matcher(text).find();
  }

  private static String label(String key) {
    return switch (key) {
      case "total" -> "总数";
      case "high" -> "高风险";
      case "medium" -> "中风险";
      default -> "低风险";
    };
  }
}