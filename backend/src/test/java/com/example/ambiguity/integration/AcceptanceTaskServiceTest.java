package com.example.ambiguity.integration;

import com.example.ambiguity.acceptance.AcceptanceContext;
import com.example.ambiguity.acceptance.AcceptanceService;
import com.example.ambiguity.acceptance.dto.AcceptanceDtos.*;
import com.example.ambiguity.integration.TaskDtos.TaskView;
import com.example.ambiguity.model.Review;
import com.example.ambiguity.repository.ReviewRepository;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * 集成层任务生命周期测试：状态迁移、重复提交、取消与迟到结果、重试、规则降级、
 * 人工编辑、保存幂等与两任务交错。模型用 Mock 替代，任务层逻辑走真实数据库与状态机。
 */
@SpringBootTest(properties = {
    "app.ai-mode=mock",
    "spring.datasource.url=jdbc:h2:mem:acceptance_task_test;DB_CLOSE_DELAY=-1",
    "spring.jpa.hibernate.ddl-auto=create-drop",
    "app.integration.cleanup-interval-ms=600000"
})
@AutoConfigureMockMvc
class AcceptanceTaskServiceTest {
  private static final String INPUT = "用户可以上传 DOCX 或 PDF 需求文档，单个文件不超过 10MB，解析时间不超过 60 秒。";

  @Autowired MockMvc mvc;
  @Autowired ObjectMapper mapper;
  @Autowired AcceptanceTaskService service;
  @Autowired AcceptanceTaskRepository tasks;
  @Autowired ReviewRepository reviews;
  @MockBean AcceptanceService acceptance;

  private static Report report(String summary) {
    return new Report("normal", summary,
        List.of(new Criterion("AC-1", "大小校验", "系统就绪", "上传 11MB 文件", "拒绝并提示",
            "文件不超过 10MB", "must")),
        List.of(new TestSample("TS-1", "normal", "上传 5MB", "成功", "单个文件不超过 10MB")),
        List.of(), List.of());
  }

  private static RunResponse success(String summary) {
    return new RunResponse("run-" + summary, "SUCCESS", "revised", "qwen-plus", 1200,
        new Usage(100, 80, 180), report(summary), new Checks(true, true, true, true, List.of()),
        1, null, null);
  }

  private static RunResponse failed(String code, String message) {
    return new RunResponse("run-fail", "FAILED", "revised", "qwen-plus", 900,
        new Usage(10, 0, 10), null, null, 1, message, code);
  }

  private TaskView await(String taskId, String expectedStatus, long timeoutMs) throws Exception {
    long deadline = System.currentTimeMillis() + timeoutMs;
    while (System.currentTimeMillis() < deadline) {
      TaskView view = service.get(taskId);
      if (expectedStatus.equals(view.status())) return view;
      Thread.sleep(50);
    }
    TaskView view = service.get(taskId);
    fail("任务未进入状态 " + expectedStatus + "，当前 " + view.status() + "：" + view.phase());
    return view;
  }

  @Test
  void submitRunsInBackgroundAndPersistsResult() throws Exception {
    when(acceptance.run(any(), any(AcceptanceContext.class))).thenReturn(success("已生成"));

    TaskView submitted = service.submit(new TaskDtos.SubmitRequest(null, INPUT, "revised", "model"));
    assertTrue(List.of(TaskStatus.QUEUED, TaskStatus.RUNNING).contains(submitted.status()));
    TaskView done = await(submitted.taskId(), TaskStatus.SUCCEEDED, 3000);

    assertEquals("已生成", done.report().summary());
    assertTrue(done.checks().acceptable());
    assertEquals("qwen-plus", done.model());
    assertFalse(done.saved());
    assertTrue(done.actions().contains("apply"));
    // 刷新恢复：按任务编号重新读取，结果与状态一致
    assertEquals(done.report().summary(), service.get(submitted.taskId()).report().summary());
  }

  @Test
  void duplicateSubmitReturnsSameActiveTask() throws Exception {
    when(acceptance.run(any(), any(AcceptanceContext.class))).thenAnswer(inv -> {
      Thread.sleep(400);
      return success("慢任务");
    });
    TaskView first = service.submit(new TaskDtos.SubmitRequest(null, INPUT, "revised", "model"));
    TaskView second = service.submit(new TaskDtos.SubmitRequest(null, INPUT, "revised", "model"));

    assertEquals(first.taskId(), second.taskId());
    assertTrue(second.duplicate());
    await(first.taskId(), TaskStatus.SUCCEEDED, 4000);
  }

  @Test
  void cancelRunningTaskDiscardsLateResult() throws Exception {
    when(acceptance.run(any(), any(AcceptanceContext.class))).thenAnswer(inv -> {
      AcceptanceContext ctx = inv.getArgument(1);
      for (int i = 0; i < 100 && !ctx.isCancelled(); i++) Thread.sleep(20);
      return success("迟到结果");
    });
    TaskView submitted = service.submit(new TaskDtos.SubmitRequest(null, INPUT, "revised", "model"));
    await(submitted.taskId(), TaskStatus.RUNNING, 3000);
    service.cancel(submitted.taskId());

    TaskView cancelled = await(submitted.taskId(), TaskStatus.CANCELLED, 5000);
    assertEquals("CANCELLED", cancelled.errorCode());
    assertNull(cancelled.report());
    assertNull(cancelled.checks());
    assertTrue(cancelled.actions().contains("retry"));
  }

  @Test
  void cancelFinishedTaskIsRejectedWithReadableCode() throws Exception {
    when(acceptance.run(any(), any(AcceptanceContext.class))).thenReturn(success("已完成"));
    TaskView done = service.submit(new TaskDtos.SubmitRequest(null, INPUT, "revised", "model"));
    await(done.taskId(), TaskStatus.SUCCEEDED, 3000);
    ApiException error = assertThrows(ApiException.class, () -> service.cancel(done.taskId()));
    assertEquals(409, error.getStatus());
    assertEquals("TASK_FINISHED", error.getCode());
    assertFalse(error.isRetryable());
  }

  @Test
  void retryCreatesNewTaskAndKeepsHistory() throws Exception {
    when(acceptance.run(any(), any(AcceptanceContext.class)))
        .thenReturn(failed("MODEL_TIMEOUT", "模型调用失败：Read timed out"))
        .thenReturn(success("重试成功"));
    TaskView origin = service.submit(new TaskDtos.SubmitRequest(null, INPUT, "revised", "model"));
    TaskView failedView = await(origin.taskId(), TaskStatus.FAILED, 3000);
    assertTrue(failedView.retryable());

    TaskView retried = service.retry(origin.taskId());
    assertNotEquals(origin.taskId(), retried.taskId());
    assertEquals(origin.taskId(), retried.retryOf());
    assertEquals(TaskStatus.SUCCEEDED, await(retried.taskId(), TaskStatus.SUCCEEDED, 3000).status());
    assertEquals(TaskStatus.FAILED, service.get(origin.taskId()).status());
  }

  @Test
  void fallbackProducesClearlyMarkedRuleResult() throws Exception {
    when(acceptance.run(any(), any(AcceptanceContext.class))).thenAnswer(inv -> {
      RunRequest request = inv.getArgument(0);
      if ("rule".equals(request.mode())) {
        return new RunResponse("run-rule", "SUCCESS", "revised", "rule-baseline", 4,
            new Usage(0, 0, 0), report("规则结果"), null, 1, null, null);
      }
      return failed("MODEL_TIMEOUT", "模型调用失败：Read timed out");
    });
    TaskView origin = service.submit(new TaskDtos.SubmitRequest(null, INPUT, "revised", "model"));
    await(origin.taskId(), TaskStatus.FAILED, 3000);

    TaskView fallback = service.fallback(origin.taskId());
    assertEquals(TaskStatus.SUCCEEDED, fallback.status());
    assertTrue(fallback.degraded());
    assertEquals("rule", fallback.mode());
    assertEquals("rule-baseline", fallback.model());
    assertNotNull(fallback.degradeReason());
    assertEquals(origin.taskId(), fallback.retryOf());
  }

  @Test
  void editRevalidatesQuotesAndKeepsHumanTrace() throws Exception {
    when(acceptance.run(any(), any(AcceptanceContext.class))).thenReturn(success("已生成"));
    TaskView done = service.submit(new TaskDtos.SubmitRequest(null, INPUT, "revised", "model"));
    await(done.taskId(), TaskStatus.SUCCEEDED, 3000);

    Report edited = new Report("normal", "人工补充",
        List.of(new Criterion("AC-1", "大小校验", "系统就绪", "上传 11MB", "拒绝",
            "这句话原文里没有", "must")),
        List.of(), List.of("需要确认最大并发"), List.of());
    TaskView view = service.edit(done.taskId(), new TaskDtos.EditRequest(edited));
    assertTrue(view.edited());
    assertFalse(view.checks().groundingOk());
    assertEquals("人工补充", view.report().summary());
  }

  @Test
  void applySavesAcceptanceToReviewIdempotently() throws Exception {
    Review review = reviews.save(new Review(INPUT, "全面审查", "{}"));
    when(acceptance.run(any(), any(AcceptanceContext.class))).thenReturn(success("可保存"));
    TaskView done = service.submit(new TaskDtos.SubmitRequest(review.getId().toString(), null, "revised", "model"));
    await(done.taskId(), TaskStatus.SUCCEEDED, 3000);

    TaskDtos.ApplyResponse first = service.apply(done.taskId());
    TaskDtos.ApplyResponse second = service.apply(done.taskId());
    assertTrue(first.task().saved());
    assertEquals(first.task().savedAt(), second.task().savedAt());

    Review saved = reviews.findById(review.getId()).orElseThrow();
    assertTrue(saved.getAcceptanceJson().contains(done.taskId()));
    assertEquals("可保存", mapper.readTree(saved.getAcceptanceJson())
        .path("acceptance").path("report").path("summary").asText());
  }

  @Test
  void interleavedTasksDoNotMixResults() throws Exception {
    when(acceptance.run(any(), any(AcceptanceContext.class))).thenAnswer(inv -> {
      RunRequest request = inv.getArgument(0);
      Thread.sleep(request.text().contains("慢") ? 350 : 60);
      return success(request.text().contains("慢") ? "任务A" : "任务B");
    });
    TaskView a = service.submit(new TaskDtos.SubmitRequest(null, INPUT + "（慢）", "revised", "model"));
    TaskView b = service.submit(new TaskDtos.SubmitRequest(null, INPUT + "（快）", "revised", "model"));
    TaskView doneB = await(b.taskId(), TaskStatus.SUCCEEDED, 3000);
    TaskView doneA = await(a.taskId(), TaskStatus.SUCCEEDED, 3000);

    assertEquals("任务B", doneB.report().summary());
    assertEquals("任务A", doneA.report().summary());
    assertNotEquals(doneA.taskId(), doneB.taskId());
  }

  @Test
  void invalidInputIsRejectedBeforeTaskCreation() throws Exception {
    mvc.perform(post("/api/acceptance/tasks").contentType(MediaType.APPLICATION_JSON)
            .content("{\"text\":\"   \",\"promptVersion\":\"revised\"}"))
        .andExpect(status().isBadRequest())
        .andExpect(jsonPath("$.code").value("INPUT_INVALID"))
        .andExpect(jsonPath("$.retryable").value(false));

    mvc.perform(post("/api/acceptance/tasks").contentType(MediaType.APPLICATION_JSON)
            .content(mapper.writeValueAsString(java.util.Map.of("text", "长".repeat(3001)))))
        .andExpect(status().isBadRequest())
        .andExpect(jsonPath("$.code").value("INPUT_INVALID"));
  }

  @Test
  void unknownTaskReturns404WithActions() throws Exception {
    mvc.perform(get("/api/acceptance/tasks/AC00000000000000-ffff"))
        .andExpect(status().isNotFound())
        .andExpect(jsonPath("$.code").value("TASK_NOT_FOUND"))
        .andExpect(jsonPath("$.actions[0]").value("重新发起"));
  }

  @Test
  void submitAcceptsWithTaskIdAndGetRecoversState() throws Exception {
    when(acceptance.run(any(), any(AcceptanceContext.class))).thenReturn(success("可恢复"));
    String body = mvc.perform(post("/api/acceptance/tasks").contentType(MediaType.APPLICATION_JSON)
            .content(mapper.writeValueAsString(java.util.Map.of("text", INPUT))))
        .andExpect(status().isAccepted())
        .andExpect(jsonPath("$.taskId").isNotEmpty())
        .andExpect(jsonPath("$.status").value("QUEUED"))
        .andReturn().getResponse().getContentAsString(java.nio.charset.StandardCharsets.UTF_8);
    String taskId = mapper.readTree(body).get("taskId").asText();

    for (int i = 0; i < 40; i++) {
      String current = mvc.perform(get("/api/acceptance/tasks/" + taskId))
          .andExpect(status().isOk()).andReturn().getResponse()
          .getContentAsString(java.nio.charset.StandardCharsets.UTF_8);
      if ("SUCCEEDED".equals(mapper.readTree(current).get("status").asText())) {
        assertTrue(mapper.readTree(current).get("report").get("summary").asText().equals("可恢复"));
        return;
      }
      Thread.sleep(50);
    }
    fail("任务未在 2 秒内完成");
  }
}