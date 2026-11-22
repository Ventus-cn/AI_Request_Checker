package com.example.ambiguity.acceptance;

import com.example.ambiguity.acceptance.dto.AcceptanceDtos.RunRequest;
import com.example.ambiguity.acceptance.dto.AcceptanceDtos.RunResponse;
import com.example.ambiguity.acceptance.model.AcceptanceModelClient;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.mockito.ArgumentMatchers.anyList;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class AcceptanceServiceTest {
  private static final String INPUT = "用户可以上传 DOCX 或 PDF 格式的需求文档，单个文件不超过 10MB。"
      + "文件超过 10MB 时提示原因并拒绝上传。上传后解析时间不超过 60 秒。";

  private static final String BAD_JSON = """
      {"requirementKind":"normal","summary":"ok",
       "acceptanceCriteria":[{"id":"AC-1","title":"大小","given":"已登录","when":"上传 11MB",
       "then":"拒绝","sourceQuote":"原文没有这句话","priority":"must"}],
       "testSamples":[{"id":"TS-1","kind":"normal","input":"5MB","expected":"成功",
       "sourceQuote":"用户可以上传 DOCX 或 PDF 格式的需求文档"}],
       "openQuestions":[],"limits":[]}
      """;

  private static final String GOOD_JSON = """
      {"requirementKind":"normal","summary":"已生成",
       "acceptanceCriteria":[{"id":"AC-1","title":"大小校验","given":"系统已就绪","when":"上传 11MB 文件",
       "then":"拒绝并提示原因","sourceQuote":"文件超过 10MB 时提示原因并拒绝上传","priority":"must"}],
       "testSamples":[
         {"id":"TS-1","kind":"normal","input":"上传 5MB PDF","expected":"解析成功",
          "sourceQuote":"用户可以上传 DOCX 或 PDF 格式的需求文档"},
         {"id":"TS-2","kind":"boundary","input":"上传 10MB 文件","expected":"解析成功",
          "sourceQuote":"单个文件不超过 10MB"},
         {"id":"TS-3","kind":"exception","input":"上传 11MB 文件","expected":"拒绝并提示",
          "sourceQuote":"文件超过 10MB 时提示原因并拒绝上传"}],
       "openQuestions":[],"limits":[]}
      """;

  private AcceptanceService service(AcceptanceModelClient client, int maxAttempts) {
    AcceptanceProperties props = new AcceptanceProperties();
    props.setMaxAttempts(maxAttempts);
    return new AcceptanceService(client, new AcceptancePrompts(), props,
        mock(AcceptanceRunLogger.class), new AcceptanceChecker());
  }

  @Test
  void repairsAfterUngroundedQuoteAndSucceeds() {
    AcceptanceModelClient client = mock(AcceptanceModelClient.class);
    when(client.chat(anyList()))
        .thenReturn(new AcceptanceModelClient.ChatResult(BAD_JSON, 100, 80, 1200))
        .thenReturn(new AcceptanceModelClient.ChatResult(GOOD_JSON, 100, 90, 1100));

    RunResponse response = service(client, 3).run(new RunRequest(INPUT, "revised", "model"));

    assertEquals("SUCCESS", response.status());
    assertEquals(2, response.attempts());
    assertNotNull(response.checks());
    assertEquals(true, response.checks().acceptable());
    verify(client, org.mockito.Mockito.times(2)).chat(anyList());
  }

  @Test
  void repairsAfterInvalidJsonAndSucceeds() {
    AcceptanceModelClient client = mock(AcceptanceModelClient.class);
    when(client.chat(anyList()))
        .thenReturn(new AcceptanceModelClient.ChatResult("这不是 JSON", 10, 5, 300))
        .thenReturn(new AcceptanceModelClient.ChatResult(GOOD_JSON, 100, 90, 1000));

    RunResponse response = service(client, 2).run(new RunRequest(INPUT, "revised", "model"));

    assertEquals("SUCCESS", response.status());
    assertEquals(2, response.attempts());
  }

  @Test
  void outOfScopeIsRefusedBeforeCallingModel() {
    AcceptanceModelClient client = mock(AcceptanceModelClient.class);
    RunResponse response = service(client, 3)
        .run(new RunRequest("帮我采购 20 台服务器，并完成付款审批。", "revised", "model"));

    assertEquals("REFUSED", response.status());
    assertEquals("out_of_scope", response.report().requirementKind());
    verify(client, never()).chat(anyList());
  }

  @Test
  void exhaustedRepairsReturnCheckFailed() {
    AcceptanceModelClient client = mock(AcceptanceModelClient.class);
    when(client.chat(anyList()))
        .thenReturn(new AcceptanceModelClient.ChatResult(BAD_JSON, 100, 80, 1000))
        .thenReturn(new AcceptanceModelClient.ChatResult(BAD_JSON, 100, 80, 1000));

    RunResponse response = service(client, 2).run(new RunRequest(INPUT, "revised", "model"));

    assertEquals("CHECK_FAILED", response.status());
    assertEquals(false, response.checks().acceptable());
  }

  @Test
  void originalVersionKeepsSingleCallWithoutChecks() {
    AcceptanceModelClient client = mock(AcceptanceModelClient.class);
    when(client.chat(anyList()))
        .thenReturn(new AcceptanceModelClient.ChatResult(GOOD_JSON, 10, 20, 500));

    RunResponse response = service(client, 3).run(new RunRequest(INPUT, "original", "model"));

    assertEquals("SUCCESS", response.status());
    assertEquals(1, response.attempts());
    assertEquals(null, response.checks());
    verify(client, org.mockito.Mockito.times(1)).chat(anyList());
  }

  @Test
  void ruleBaselineNeverCallsModel() {
    AcceptanceModelClient client = mock(AcceptanceModelClient.class);
    RunResponse response = service(client, 3).run(new RunRequest(INPUT, "revised", "rule"));

    assertEquals("SUCCESS", response.status());
    assertEquals("rule-baseline", response.model());
    assertEquals(1, response.report().testSamples().size());
    verify(client, never()).chat(anyList());
  }
}