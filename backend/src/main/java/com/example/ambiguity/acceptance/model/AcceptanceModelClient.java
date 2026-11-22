package com.example.ambiguity.acceptance.model;

import com.example.ambiguity.acceptance.AcceptanceProperties;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;

import java.util.List;
import java.util.Map;

/** 千问 chat/completions 通道。超时、温度、Token 上限全部来自 AcceptanceProperties。 */
@Component
public class AcceptanceModelClient {
  private final ObjectMapper mapper = new ObjectMapper();
  private final RestClient client;
  private final AcceptanceProperties props;

  @Value("${app.qwen-api-key:}") private String apiKey;
  @Value("${app.qwen-url:https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions}") private String url;

  public AcceptanceModelClient(AcceptanceProperties props) {
    this.props = props;
    SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
    factory.setConnectTimeout(10_000);
    factory.setReadTimeout((int) Math.min(props.getTimeoutMs(), 120_000));
    this.client = RestClient.builder().requestFactory(factory).build();
  }

  public ChatResult chat(String system, String user) {
    if (apiKey == null || apiKey.isBlank()) throw new IllegalStateException("未配置 DASHSCOPE_API_KEY，无法调用模型");
    Map<String, Object> payload = Map.of(
        "model", props.getModel(),
        "temperature", props.getTemperature(),
        "max_tokens", props.getMaxTokens(),
        "messages", List.of(
            Map.of("role", "system", "content", system),
            Map.of("role", "user", "content", user)));
    long started = System.currentTimeMillis();
    try {
      String body = client.post().uri(url)
          .header("Authorization", "Bearer " + apiKey)
          .contentType(MediaType.APPLICATION_JSON)
          .body(payload)
          .retrieve()
          .body(String.class);
      JsonNode root = mapper.readTree(body);
      JsonNode message = root.path("choices").path(0).path("message");
      String content = message.path("content").asText("");
      JsonNode usage = root.path("usage");
      return new ChatResult(
          content,
          usage.path("prompt_tokens").asInt(0),
          usage.path("completion_tokens").asInt(0),
          System.currentTimeMillis() - started);
    } catch (Exception e) {
      throw new IllegalStateException("模型调用失败：" + rootMessage(e), e);
    }
  }

  private String rootMessage(Exception e) {
    String message = e.getMessage();
    if (message == null || message.isBlank()) return e.getClass().getSimpleName();
    return message.length() > 300 ? message.substring(0, 300) : message;
  }

  public record ChatResult(String content, int promptTokens, int completionTokens, long durationMs) {}
}