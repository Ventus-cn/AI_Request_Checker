package com.example.ambiguity.agent.tool;

import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 工具白名单与参数校验的单元测试：证明非法工具名、越界数值、缺失必填、
 * 多余字段和格式错误都会在执行前被程序拒绝。
 */
class ToolRegistryTest {
  private final ToolRegistry registry = new ToolRegistry(List.of(
      new FakeTool("list_reviews", Map.of(
          "type", "object",
          "properties", Map.of(
              "limit", Map.of("type", "integer", "minimum", 1, "maximum", 20, "default", 5),
              "riskLevel", Map.of("type", "string", "enum", List.of("all", "high"), "default", "all")),
          "required", List.of(),
          "additionalProperties", false)),
      new FakeTool("get_review_detail", Map.of(
          "type", "object",
          "properties", Map.of("id", Map.of("type", "string", "pattern", "^[0-9a-fA-F-]{36}$")),
          "required", List.of("id"),
          "additionalProperties", false))));

  @Test
  void rejectsUnknownToolName() {
    ToolException error = assertThrows(ToolException.class, () -> registry.require("drop_database"));
    assertEquals(ToolException.ARG_INVALID, error.errorType());
    assertTrue(error.getMessage().contains("list_reviews"));
  }

  @Test
  void appliesDefaultsAndAcceptsValidArguments() {
    Map<String, Object> args = ArgumentValidator.validate(registry.require("list_reviews").spec(), Map.of());
    assertEquals(5, args.get("limit"));
    assertEquals("all", args.get("riskLevel"));
  }

  @Test
  void rejectsOutOfRangeInteger() {
    ToolException error = assertThrows(ToolException.class,
        () -> ArgumentValidator.validate(registry.require("list_reviews").spec(), Map.of("limit", 999)));
    assertEquals(ToolException.ARG_INVALID, error.errorType());
    assertTrue(error.getMessage().contains("不能大于"));
    assertTrue(error.getMessage().contains("20"));
  }

  @Test
  void rejectsUnknownAndMissingArguments() {
    ToolException unknown = assertThrows(ToolException.class,
        () -> ArgumentValidator.validate(registry.require("get_review_detail").spec(), Map.of("id", "x", "verbose", true)));
    assertEquals(ToolException.ARG_INVALID, unknown.errorType());

    ToolException missing = assertThrows(ToolException.class,
        () -> ArgumentValidator.validate(registry.require("get_review_detail").spec(), Map.of()));
    assertTrue(missing.getMessage().contains("id"));
  }

  @Test
  void rejectsBadUuidFormat() {
    ToolException error = assertThrows(ToolException.class,
        () -> ArgumentValidator.validate(registry.require("get_review_detail").spec(), Map.of("id", "not-a-uuid")));
    assertEquals(ToolException.ARG_INVALID, error.errorType());
  }

  @Test
  void rejectsEnumMismatchAndNonInteger() {
    ToolException value = assertThrows(ToolException.class,
        () -> ArgumentValidator.validate(registry.require("list_reviews").spec(), Map.of("riskLevel", "critical")));
    assertEquals(ToolException.ARG_INVALID, value.errorType());

    ToolException type = assertThrows(ToolException.class,
        () -> ArgumentValidator.validate(registry.require("list_reviews").spec(), Map.of("limit", "five")));
    assertEquals(ToolException.ARG_INVALID, type.errorType());
  }

  private record FakeTool(String name, Map<String, Object> parameters) implements Tool {
    @Override
    public ToolSpec spec() {
      return new ToolSpec(name, "测试工具", parameters);
    }

    @Override
    public Map<String, Object> execute(Map<String, Object> args) {
      return Map.of("ok", true);
    }
  }
}