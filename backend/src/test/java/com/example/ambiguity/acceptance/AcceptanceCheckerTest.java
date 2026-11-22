package com.example.ambiguity.acceptance;

import com.example.ambiguity.acceptance.dto.AcceptanceDtos.Checks;
import com.example.ambiguity.acceptance.dto.AcceptanceDtos.Criterion;
import com.example.ambiguity.acceptance.dto.AcceptanceDtos.Report;
import com.example.ambiguity.acceptance.dto.AcceptanceDtos.TestSample;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class AcceptanceCheckerTest {
  private final AcceptanceChecker checker = new AcceptanceChecker();
  private final String input = "用户可以上传 DOCX 或 PDF 格式的需求文档，单个文件不超过 10MB。"
      + "上传后系统解析正文，解析时间不超过 60 秒。文件超过 10MB 时提示原因并拒绝上传。";

  @Test
  void normalReportWithGroundingAndCoveragePasses() {
    Report report = new Report("normal", "ok",
        List.of(new Criterion("AC-1", "大小校验", "系统已就绪", "上传 11MB 文件",
            "提示超过 10MB 并拒绝上传", "文件超过 10MB 时提示原因并拒绝上传", "must")),
        List.of(new TestSample("TS-1", "normal", "上传 5MB PDF", "解析成功",
                "用户可以上传 DOCX 或 PDF 格式的需求文档"),
            new TestSample("TS-2", "boundary", "上传 10MB 文件", "解析成功",
                "单个文件不超过 10MB"),
            new TestSample("TS-3", "exception", "上传 11MB 文件", "提示并拒绝",
                "文件超过 10MB 时提示原因并拒绝上传")),
        List.of(), List.of());

    Checks checks = checker.check(input, report);
    assertTrue(checks.acceptable());
    assertTrue(checks.messages().isEmpty());
  }

  @Test
  void fabricatedQuoteFailsGrounding() {
    Report report = new Report("normal", "ok",
        List.of(new Criterion("AC-1", "大小校验", "系统已就绪", "上传 11MB 文件",
            "提示超过 10MB 并拒绝上传", "原文没有这句话", "must")),
        List.of(new TestSample("TS-1", "normal", "上传 5MB PDF", "解析成功",
                "用户可以上传 DOCX 或 PDF 格式的需求文档"),
            new TestSample("TS-2", "boundary", "上传 10MB 文件", "解析成功",
                "单个文件不超过 10MB"),
            new TestSample("TS-3", "exception", "上传 11MB 文件", "提示并拒绝",
                "文件超过 10MB 时提示原因并拒绝上传")),
        List.of(), List.of());

    Checks checks = checker.check(input, report);
    assertFalse(checks.groundingOk());
    assertFalse(checks.acceptable());
  }

  @Test
  void missingTestKindsFailsCoverage() {
    Report report = new Report("normal", "ok",
        List.of(new Criterion("AC-1", "大小校验", "系统已就绪", "上传 11MB 文件",
            "提示超过 10MB 并拒绝上传", "文件超过 10MB 时提示原因并拒绝上传", "must")),
        List.of(new TestSample("TS-1", "normal", "上传 5MB PDF", "解析成功",
            "用户可以上传 DOCX 或 PDF 格式的需求文档")),
        List.of(), List.of());

    Checks checks = checker.check(input, report);
    assertFalse(checks.coverageOk());
    assertFalse(checks.acceptable());
  }

  @Test
  void insufficientKindNeedsThreeQuestionsAndNoCriteria() {
    Report report = new Report("insufficient", "信息不足",
        List.of(), List.of(),
        List.of("角色是谁？", "输入是什么？", "如何验收？"), List.of());
    Checks checks = checker.check("系统要快一点。", report);
    assertTrue(checks.acceptable());
  }

  @Test
  void outOfScopeMustNotProduceCriteria() {
    Report report = new Report("out_of_scope", "超出范围", List.of(), List.of(),
        List.of("请提交软件需求"), List.of());
    Checks checks = checker.check("帮我采购服务器。", report);
    assertTrue(checks.acceptable());
  }
}