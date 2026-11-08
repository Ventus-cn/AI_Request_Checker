package com.example.ambiguity.agent.model;

import java.util.List;
import java.util.Map;

/**
 * 模型通道抽象。生产实现调用千问，测试用桩实现模拟 tool_calls 与错误，便于离线验证流程。
 */
public interface AgentModelClient {
  ChatResult complete(List<Map<String, Object>> messages, List<Map<String, Object>> tools);

  record ChatResult(Map<String, Object> message, int promptTokens, int completionTokens) {
  }
}