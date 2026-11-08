package com.example.ambiguity.agent.model;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.util.*;

/**
 * 千问 OpenAI 兼容接口实现：带 tools 调用，返回 assistant 消息（含 tool_calls）与 token 用量。
 * API Key 只从后端配置读取，不进入前端、响应或日志。
 */
@Component
public class QwenAgentModelClient implements AgentModelClient {
  private final RestClient client;
  private final String apiKey;
  private final String model;
  private final String url;

  public QwenAgentModelClient(
      @Value("${app.qwen-api-key:}") String apiKey,
      @Value("${app.qwen-model:qwen-plus}") String model,
      @Value("${app.qwen-url:https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions}") String url,
      @Value("${app.agent.model-timeout-ms:30000}") int timeoutMs) {
    this.apiKey = apiKey;
    this.model = model;
    this.url = url;
    SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
    factory.setConnectTimeout(10000);
    factory.setReadTimeout(timeoutMs);
    this.client = RestClient.builder().requestFactory(factory).build();
  }

  @Override
  public ChatResult complete(List<Map<String, Object>> messages, List<Map<String, Object>> tools) {
    if (apiKey == null || apiKey.isBlank()) {
      throw new IllegalStateException("Agent 需要配置千问 API Key（AI_MODE=qwen、DASHSCOPE_API_KEY）");
    }
    Map<String, Object> payload = new LinkedHashMap<>();
    payload.put("model", model);
    payload.put("temperature", 0.1);
    payload.put("messages", messages);
    if (tools != null && !tools.isEmpty()) {
      payload.put("tools", tools);
      payload.put("tool_choice", "auto");
      payload.put("parallel_tool_calls", false);
    }
    try {
      Map<?, ?> response = client.post().uri(url)
          .header("Authorization", "Bearer " + apiKey)
          .contentType(MediaType.APPLICATION_JSON)
          .body(payload)
          .retrieve()
          .body(Map.class);
      if (response == null || !(response.get("choices") instanceof List<?> choices) || choices.isEmpty()) {
        throw new IllegalStateException("模型返回中没有 choices");
      }
      Map<?, ?> choice = (Map<?, ?>) choices.get(0);
      Map<?, ?> message = (Map<?, ?>) choice.get("message");
      if (message == null) throw new IllegalStateException("模型返回中没有 message");
      Map<String, Object> normalized = new LinkedHashMap<>();
      message.forEach((key, value) -> normalized.put(String.valueOf(key), value));

      Map<?, ?> usage = response.get("usage") instanceof Map<?, ?> map ? map : Map.of();
      return new ChatResult(normalized, asInt(usage.get("prompt_tokens")), asInt(usage.get("completion_tokens")));
    } catch (IllegalStateException e) {
      throw e;
    } catch (Exception e) {
      throw new IllegalStateException("千问模型调用失败：" + e.getMessage());
    }
  }

  private static int asInt(Object value) {
    return value instanceof Number number ? number.intValue() : 0;
  }
}