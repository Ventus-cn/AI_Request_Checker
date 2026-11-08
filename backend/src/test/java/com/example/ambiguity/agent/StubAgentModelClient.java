package com.example.ambiguity.agent;

import com.example.ambiguity.agent.model.AgentModelClient;

import java.util.*;
import java.util.function.Function;

/**
 * 测试用模型桩：按脚本依次返回预设响应，用于离线模拟参数错误、工具异常、
 * 步数上限、确认流程和结果校验失败，不消耗真实模型额度。
 */
class StubAgentModelClient implements AgentModelClient {
  private final Deque<Function<List<Map<String, Object>>, ChatResult>> scripts = new ArrayDeque<>();

  void then(Function<List<Map<String, Object>>, ChatResult> step) {
    scripts.add(step);
  }

  void reset() {
    scripts.clear();
  }

  @Override
  public ChatResult complete(List<Map<String, Object>> messages, List<Map<String, Object>> tools) {
    Function<List<Map<String, Object>>, ChatResult> step = scripts.poll();
    if (step == null) return text("（模型桩没有更多预设响应）");
    return step.apply(messages);
  }

  static ChatResult text(String content) {
    Map<String, Object> message = new LinkedHashMap<>();
    message.put("role", "assistant");
    message.put("content", content);
    return new ChatResult(message, 10, 5);
  }

  static ChatResult toolCall(String id, String name, String argumentsJson) {
    Map<String, Object> function = new LinkedHashMap<>();
    function.put("name", name);
    function.put("arguments", argumentsJson);
    Map<String, Object> call = new LinkedHashMap<>();
    call.put("id", id);
    call.put("type", "function");
    call.put("function", function);
    Map<String, Object> message = new LinkedHashMap<>();
    message.put("role", "assistant");
    message.put("content", "");
    message.put("tool_calls", List.of(call));
    return new ChatResult(message, 12, 8);
  }

  /** 读取最近一次指定工具的结果 JSON，模拟“模型依据工具结果作答”。 */
  static String lastToolResult(List<Map<String, Object>> messages, String tool) {
    for (int i = messages.size() - 1; i >= 0; i--) {
      Map<String, Object> message = messages.get(i);
      if ("tool".equals(message.get("role")) && tool.equals(message.get("name"))) {
        return String.valueOf(message.get("content"));
      }
    }
    return "{}";
  }
}