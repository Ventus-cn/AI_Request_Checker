package com.example.ambiguity.acceptance;

import com.example.ambiguity.acceptance.dto.AcceptanceDtos.Checks;
import com.example.ambiguity.acceptance.dto.AcceptanceDtos.Criterion;
import com.example.ambiguity.acceptance.dto.AcceptanceDtos.Report;
import com.example.ambiguity.acceptance.dto.AcceptanceDtos.TestSample;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.regex.Pattern;

/** 程序侧结果检查：结构、原文引用、GWT 与覆盖。不依赖模型自称“已完成”。 */
@Component
public class AcceptanceChecker {
  private static final Set<String> KINDS = Set.of("normal", "insufficient", "out_of_scope");
  private static final Set<String> TEST_KINDS = Set.of("normal", "boundary", "exception");
  private static final Set<String> PRIORITIES = Set.of("must", "should", "could");
  private static final Pattern SPACE = Pattern.compile("\\s+");

  public Checks check(String input, Report report) {
    List<String> messages = new ArrayList<>();
    String kind = report.requirementKind();
    boolean schema = true;

    if (kind == null || !KINDS.contains(kind)) {
      schema = false;
      messages.add("requirementKind 必须是 normal/insufficient/out_of_scope");
      kind = "normal";
    }
    if (blank(report.summary())) {
      schema = false;
      messages.add("缺少 summary");
    }
    if (report.acceptanceCriteria() == null || report.testSamples() == null || report.openQuestions() == null) {
      return new Checks(false, false, false, false, List.of("输出缺少必要数组字段"));
    }

    Set<String> ids = new HashSet<>();
    for (Criterion ac : report.acceptanceCriteria()) {
      if (blank(ac.id()) || blank(ac.title()) || blank(ac.given()) || blank(ac.when())
          || blank(ac.then()) || blank(ac.sourceQuote())) {
        schema = false;
        messages.add("验收标准缺少 id/title/given/when/then/sourceQuote");
      }
      if (!PRIORITIES.contains(ac.priority())) {
        schema = false;
        messages.add("priority 必须是 must/should/could");
      }
      if (!ids.add(String.valueOf(ac.id()))) {
        schema = false;
        messages.add("验收标准编号重复：" + ac.id());
      }
    }
    for (TestSample ts : report.testSamples()) {
      if (blank(ts.id()) || blank(ts.kind()) || blank(ts.input())
          || blank(ts.expected()) || blank(ts.sourceQuote())) {
        schema = false;
        messages.add("测试样例缺少 id/kind/input/expected/sourceQuote");
      }
      if (!TEST_KINDS.contains(ts.kind())) {
        schema = false;
        messages.add("测试样例 kind 必须是 normal/boundary/exception");
      }
    }

    boolean structure;
    boolean coverage;
    boolean grounding;
    if ("normal".equals(kind)) {
      structure = !report.acceptanceCriteria().isEmpty() && report.acceptanceCriteria().stream()
          .allMatch(ac -> !blank(ac.given()) && !blank(ac.when()) && !blank(ac.then()));
      if (!structure) messages.add("验收标准必须同时具备 Given/When/Then");

      if (report.acceptanceCriteria().size() < 1 || report.acceptanceCriteria().size() > 6) {
        coverage = false;
        messages.add("正常需求的验收标准数量应在 1-6 条");
      } else {
        Set<String> kinds = new HashSet<>();
        report.testSamples().forEach(ts -> kinds.add(ts.kind()));
        coverage = kinds.containsAll(TEST_KINDS);
        if (!coverage) messages.add("测试样例未同时覆盖 normal/boundary/exception");
      }

      List<String> quotes = new ArrayList<>();
      report.acceptanceCriteria().forEach(ac -> quotes.add(ac.sourceQuote()));
      report.testSamples().forEach(ts -> quotes.add(ts.sourceQuote()));
      grounding = !quotes.isEmpty();
      String compactInput = compact(input);
      for (String quote : quotes) {
        if (blank(quote) || compact(quote).length() < 6 || !compactInput.contains(compact(quote))) {
          grounding = false;
          messages.add("引用无法在原文中逐字核验：" + preview(quote));
        }
      }
    } else if ("insufficient".equals(kind)) {
      structure = true;
      grounding = true;
      coverage = report.acceptanceCriteria().isEmpty() && report.openQuestions().size() >= 3;
      if (!report.acceptanceCriteria().isEmpty()) messages.add("信息不足时不应生成验收标准");
      if (report.openQuestions().size() < 3) messages.add("信息不足时至少提出 3 个待确认问题");
    } else {
      structure = true;
      grounding = true;
      coverage = report.acceptanceCriteria().isEmpty();
      if (!report.acceptanceCriteria().isEmpty()) messages.add("超出范围时不应生成验收标准");
    }

    return new Checks(schema, grounding, structure, coverage, List.copyOf(messages));
  }

  private boolean blank(String value) {
    return value == null || value.isBlank();
  }

  private String compact(String value) {
    return SPACE.matcher(value == null ? "" : value).replaceAll("");
  }

  private String preview(String value) {
    String flat = (value == null ? "" : value).replaceAll("\\s+", " ").trim();
    return flat.length() <= 40 ? flat : flat.substring(0, 40) + "…";
  }
}