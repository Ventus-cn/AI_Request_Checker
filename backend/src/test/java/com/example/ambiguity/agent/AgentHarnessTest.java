package com.example.ambiguity.agent;

import com.example.ambiguity.agent.dto.AgentDtos.RunResponse;
import com.example.ambiguity.agent.tool.Tool;
import com.example.ambiguity.agent.tool.ToolSpec;
import com.example.ambiguity.model.Review;
import com.example.ambiguity.repository.ReviewRepository;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Primary;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Agent/Harness 的自动化测试（模型使用桩，不消耗真实额度）：
 * 正常完成、参数错误、未知工具、工具异常、工具超时、步数上限、总时限、
 * 人工确认同意/拒绝、结果校验失败。
 */
@SpringBootTest(properties = {
    "spring.datasource.url=jdbc:h2:mem:agent_harness_test;DB_CLOSE_DELAY=-1",
    "spring.jpa.hibernate.ddl-auto=create-drop",
    "app.agent.log-dir=target/test-logs",
    "app.qwen-api-key="
})
class AgentHarnessTest {
  @TestConfiguration
  static class StubConfig {
    @Bean
    @Primary
    StubAgentModelClient stubAgentModelClient() {
      return new StubAgentModelClient();
    }

    @Bean
    Tool slowTool() {
      return new Tool() {
        @Override
        public ToolSpec spec() {
          return new ToolSpec("slow_tool", "测试用慢工具", Map.of("type", "object",
              "properties", Map.of(), "required", List.of(), "additionalProperties", false));
        }

        @Override
        public Map<String, Object> execute(Map<String, Object> args) {
          try {
            Thread.sleep(2000);
          } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
          }
          return Map.of("ok", true);
        }
      };
    }
  }

  @Autowired
  AgentHarness harness;
  @Autowired
  StubAgentModelClient model;
  @Autowired
  ReviewRepository repository;

  private final ObjectMapper mapper = new ObjectMapper();

  @BeforeEach
  void setUp() {
    model.reset();
    repository.deleteAll();
    // 部分用例会临时调小预算，这里恢复默认值，避免单例字段影响后续用例。
    ReflectionTestUtils.setField(harness, "maxSteps", 6);
    ReflectionTestUtils.setField(harness, "totalTimeoutMs", 60000L);
    ReflectionTestUtils.setField(harness, "toolTimeoutMs", 5000L);
    ReflectionTestUtils.setField(harness, "maxAnswerRetries", 2);
  }

  @Test
  void completesWhenAnswerNumbersMatchToolResult() {
    seed("high");
    model.then(messages -> StubAgentModelClient.toolCall("call_1", "compute_risk_stats", "{\"mode\":\"all\"}"));
    model.then(messages -> {
      Map<String, Object> stats = parse(StubAgentModelClient.lastToolResult(messages, "compute_risk_stats"));
      return StubAgentModelClient.text("当前共有 " + stats.get("total") + " 份档案，高风险 " + stats.get("high")
          + " 份、中风险 " + stats.get("medium") + " 份、低风险 " + stats.get("low") + " 份。");
    });

    RunResponse response = harness.start("现在有多少份档案，风险分布如何？");

    assertEquals("SUCCESS", response.status());
    assertEquals(1, response.steps().size());
    assertEquals("compute_risk_stats", response.steps().get(0).tool());
    assertEquals("ok", response.steps().get(0).status());
    assertTrue(response.answer().contains("1 份档案"));
  }

  @Test
  void rejectsInvalidArgumentAndFeedsErrorBackToModel() {
    model.then(messages -> StubAgentModelClient.toolCall("call_1", "list_reviews", "{\"limit\":999}"));
    model.then(messages -> StubAgentModelClient.text("参数不合法，无法完成查询。"));

    RunResponse response = harness.start("列出最近的档案");

    assertEquals("SUCCESS", response.status());
    assertEquals("error", response.steps().get(0).status());
    assertTrue(response.steps().get(0).resultPreview().contains("ARG_INVALID"));
  }

  @Test
  void rejectsUnknownToolName() {
    model.then(messages -> StubAgentModelClient.toolCall("call_1", "delete_all", "{}"));
    model.then(messages -> StubAgentModelClient.text("该操作不在允许范围内。"));

    RunResponse response = harness.start("删除所有档案");

    assertEquals("error", response.steps().get(0).status());
    assertTrue(response.steps().get(0).resultPreview().contains("未知工具"));
  }

  @Test
  void reportsNotFoundForMissingReview() {
    model.then(messages -> StubAgentModelClient.toolCall("call_1", "get_review_detail",
        "{\"id\":\"" + UUID.randomUUID() + "\"}"));
    model.then(messages -> StubAgentModelClient.text("查不到这条档案。"));

    RunResponse response = harness.start("看一下那条档案");

    assertEquals("error", response.steps().get(0).status());
    assertTrue(response.steps().get(0).resultPreview().contains("NOT_FOUND"));
  }

  @Test
  void reportsToolTimeoutAndKeepsRunning() {
    ReflectionTestUtils.setField(harness, "toolTimeoutMs", 50L);
    model.then(messages -> StubAgentModelClient.toolCall("call_1", "slow_tool", "{}"));
    model.then(messages -> StubAgentModelClient.text("工具超时，已停止等待。"));

    RunResponse response = harness.start("测试工具超时");

    assertEquals("error", response.steps().get(0).status());
    assertTrue(response.steps().get(0).resultPreview().contains("TIMEOUT"));
  }

  @Test
  void stopsWhenMaxStepsReached() {
    ReflectionTestUtils.setField(harness, "maxSteps", 1);
    model.then(messages -> StubAgentModelClient.toolCall("call_1", "list_reviews", "{\"limit\":1}"));

    RunResponse response = harness.start("完成一个需要很多步的任务");

    assertEquals("STEP_LIMIT", response.status());
    assertTrue(response.answer().contains("最大执行步数"));
  }

  @Test
  void stopsWhenTotalDeadlineExceeded() {
    // 负预算等价于“期限已过”，用于稳定复现总时限终止路径。
    ReflectionTestUtils.setField(harness, "totalTimeoutMs", -1L);

    RunResponse response = harness.start("任意问题");

    assertEquals("TIMEOUT", response.status());
    assertTrue(response.answer().contains("总时限"));
  }

  @Test
  void asksForConfirmationBeforeDeletingAndDeletesWhenApproved() {
    Review review = seed("medium");
    model.then(messages -> StubAgentModelClient.toolCall("call_1", "delete_review",
        "{\"id\":\"" + review.getId() + "\"}"));
    model.then(messages -> StubAgentModelClient.text("已删除该档案。"));

    RunResponse pending = harness.start("删掉那条测试档案");

    assertEquals("NEED_CONFIRM", pending.status());
    assertNotNull(pending.confirm());
    assertEquals("delete_review", pending.confirm().tool());
    assertTrue(repository.existsById(review.getId()));

    RunResponse done = harness.confirm(pending.taskId(), true);

    assertEquals("SUCCESS", done.status());
    assertFalse(repository.existsById(review.getId()));
  }

  @Test
  void doesNotDeleteWhenUserRejects() {
    Review review = seed("medium");
    model.then(messages -> StubAgentModelClient.toolCall("call_1", "delete_review",
        "{\"id\":\"" + review.getId() + "\"}"));

    RunResponse pending = harness.start("删掉那条测试档案");
    assertEquals("NEED_CONFIRM", pending.status());

    RunResponse denied = harness.confirm(pending.taskId(), false);

    assertEquals("DENIED", denied.status());
    assertTrue(denied.answer().contains("未删除"));
    assertTrue(repository.existsById(review.getId()));
  }

  @Test
  void failsCheckWhenAnswerContradictsToolNumbers() {
    seed("high");
    model.then(messages -> StubAgentModelClient.toolCall("call_1", "compute_risk_stats", "{}"));
    model.then(messages -> StubAgentModelClient.text("共有 0 份档案。"));

    RunResponse response = harness.start("现在有多少份档案？");

    assertEquals("CHECK_FAILED", response.status());
    assertTrue(response.answer().contains("程序校验未通过"));
  }

  @Test
  void repairsAnswerThatCitesKnowledgeWithoutRetrieval() {
    seed("high");
    model.then(messages -> StubAgentModelClient.toolCall("call_1", "compute_risk_stats", "{}"));
    model.then(messages -> StubAgentModelClient.text("共有 1 份档案，高风险 1 份、中风险 0 份、低风险 0 份，详见 [KB-003]。"));
    model.then(messages -> StubAgentModelClient.text("共有 1 份档案，高风险 1 份、中风险 0 份、低风险 0 份。"));

    RunResponse response = harness.start("现在有多少份档案？");

    assertEquals("SUCCESS", response.status());
    assertFalse(response.answer().contains("KB-"));
  }

  private Review seed(String riskLevel) {
    String report = "{\"summary\":\"测试档案\",\"riskLevel\":\"" + riskLevel
        + "\",\"counts\":{\"high\":1,\"medium\":0,\"low\":0},"
        + "\"issues\":[{\"id\":\"PER-001\",\"type\":\"permission\",\"severity\":\"high\"}]}";
    return repository.save(new Review("用户登录后提交预约，管理员只能查看本部门数据。", "全面审查", report));
  }

  private Map<String, Object> parse(String json) {
    try {
      return mapper.readValue(json, new TypeReference<Map<String, Object>>() {});
    } catch (Exception e) {
      return Map.of();
    }
  }
}