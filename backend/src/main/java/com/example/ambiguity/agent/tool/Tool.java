package com.example.ambiguity.agent.tool;

import java.util.Map;

/**
 * 可被 Agent 调用的工具。实现类必须注册为 Spring Bean，由 ToolRegistry 汇总成白名单。
 */
public interface Tool {
  ToolSpec spec();

  /** 是否属于会修改数据的写操作；为 true 时 Harness 必须暂停等待用户确认。 */
  default boolean requiresConfirmation() {
    return false;
  }

  /** 确认前展示给用户的影响说明。 */
  default String describeImpact(Map<String, Object> args) {
    return "将执行工具 " + spec().name();
  }

  Map<String, Object> execute(Map<String, Object> args) throws ToolException;
}