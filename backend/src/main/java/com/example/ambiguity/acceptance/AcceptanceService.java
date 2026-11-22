package com.example.ambiguity.acceptance;

import com.example.ambiguity.acceptance.dto.AcceptanceDtos.*;
import com.example.ambiguity.acceptance.model.AcceptanceModelClient;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Service;

import java.security.SecureRandom;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

/** 端到端主链路：输入规范化 → 模型调用 → JSON 解析 → 结果返回。 */
@Service
public class AcceptanceService {
  private static final DateTimeFormatter ID_TIME = DateTimeFormatter.ofPattern("yyyyMMdd-HHmmss");
  private static final SecureRandom RANDOM = new SecureRandom();

  private final AcceptanceModelClient modelClient;
  private final AcceptancePrompts prompts;
  private final AcceptanceProperties props;
  private final AcceptanceRunLogger logger;
  private final ObjectMapper mapper = new ObjectMapper();

  public AcceptanceService(AcceptanceModelClient modelClient, AcceptancePrompts prompts,
                           AcceptanceProperties props, AcceptanceRunLogger logger) {
    this.modelClient = modelClient;
    this.prompts = prompts;
    this.props = props;
    this.logger = logger;
  }

  public RunResponse run(RunRequest request) {
    String text = normalize(request == null ? null : request.text());
    if (text.isBlank()) throw new IllegalArgumentException("需求文本不能为空");
    if (text.length() > props.getMaxInputChars()) {
      throw new IllegalArgumentException("需求文本不能超过 " + props.getMaxInputChars() + " 个字符，当前 " + text.length());
    }
    String version = "original".equalsIgnoreCase(request.promptVersion()) ? "original" : "revised";
    boolean rule = "rule".equalsIgnoreCase(request.mode());
    String runId = LocalDateTime.now().format(ID_TIME) + "-" + hex(6);
    long started = System.currentTimeMillis();

    logger.event(runId, 0, "context", Map.of(
        "version", version, "mode", rule ? "rule" : "model",
        "model", rule ? "none" : props.getModel(),
        "inputChars", text.length(), "inputPreview", preview(text, 80)));

    if (rule) {
      Report report = RuleBaseline.build(text);
      long duration = System.currentTimeMillis() - started;
      logger.event(runId, 0, "finish", Map.of("status", "SUCCESS", "durationMs", duration, "criteria", report.acceptanceCriteria().size()));
      logger.artifact(runId, artifact(runId, version, "rule", text, null, report, duration, 0, 0));
      return new RunResponse(runId, "SUCCESS", version, "rule-baseline", duration,
          new Usage(0, 0, 0), report, null);
    }

    String system = prompts.load(version);
    String user = "需求原文：\n" + text;
    logger.event(runId, 1, "model", Map.of("status", "start", "promptVersion", version));

    String raw;
    AcceptanceModelClient.ChatResult result;
    try {
      result = modelClient.chat(system, user);
    } catch (Exception e) {
      long duration = System.currentTimeMillis() - started;
      String message = rootMessage(e);
      logger.event(runId, 1, "model", Map.of("status", "error", "errorType", "MODEL_ERROR", "message", preview(message, 200)));
      logger.event(runId, 1, "finish", Map.of("status", "FAILED", "durationMs", duration));
      logger.artifact(runId, artifact(runId, version, "model", text, null, null, duration, 0, 0));
      return new RunResponse(runId, "FAILED", version, props.getModel(), duration,
          new Usage(0, 0, 0), null, "模型调用失败：" + message);
    }

    raw = result.content();
    long duration = result.durationMs() > 0 ? result.durationMs() : System.currentTimeMillis() - started;
    logger.event(runId, 1, "model", Map.of("status", "ok", "durationMs", duration,
        "promptTokens", result.promptTokens(), "completionTokens", result.completionTokens()));

    Report report;
    try {
      report = parseReport(raw);
    } catch (Exception e) {
      String message = "输出不是合法 JSON：" + rootMessage(e);
      logger.event(runId, 1, "parse", Map.of("status", "error", "errorType", "PARSE_ERROR", "message", preview(message, 200)));
      logger.event(runId, 1, "finish", Map.of("status", "FAILED", "durationMs", duration));
      logger.artifact(runId, artifact(runId, version, "model", text, raw, null, duration,
          result.promptTokens(), result.completionTokens()));
      return new RunResponse(runId, "FAILED", version, props.getModel(), duration,
          new Usage(result.promptTokens(), result.completionTokens(),
              result.promptTokens() + result.completionTokens()), null, message);
    }

    logger.event(runId, 1, "parse", Map.of("status", "ok",
        "criteria", report.acceptanceCriteria().size(), "testSamples", report.testSamples().size()));
    logger.event(runId, 1, "finish", Map.of("status", "SUCCESS", "durationMs", duration));
    logger.artifact(runId, artifact(runId, version, "model", text, raw, report, duration,
        result.promptTokens(), result.completionTokens()));

    return new RunResponse(runId, "SUCCESS", version, props.getModel(), duration,
        new Usage(result.promptTokens(), result.completionTokens(),
            result.promptTokens() + result.completionTokens()), report, null);
  }

  private Map<String, Object> artifact(String runId, String version, String mode, String text, String raw,
                                       Report report, long durationMs, int promptTokens, int completionTokens) {
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("runId", runId);
    data.put("promptVersion", version);
    data.put("mode", mode);
    data.put("model", props.getModel());
    data.put("durationMs", durationMs);
    data.put("promptTokens", promptTokens);
    data.put("completionTokens", completionTokens);
    data.put("inputChars", text.length());
    data.put("input", text);
    data.put("rawOutput", raw == null ? null : preview(raw, 8000));
    data.put("report", report);
    return data;
  }

  private Report parseReport(String raw) throws Exception {
    String json = extractJson(raw);
    JsonNode root = mapper.readTree(json);
    List<Criterion> criteria = new ArrayList<>();
    for (JsonNode node : array(root, "acceptanceCriteria")) {
      criteria.add(new Criterion(text(node, "id"), text(node, "title"), text(node, "given"),
          text(node, "when"), text(node, "then"), text(node, "sourceQuote"), text(node, "priority")));
    }
    List<TestSample> samples = new ArrayList<>();
    for (JsonNode node : array(root, "testSamples")) {
      samples.add(new TestSample(text(node, "id"), text(node, "kind"), text(node, "input"),
          text(node, "expected"), text(node, "sourceQuote")));
    }
    List<String> questions = new ArrayList<>();
    for (JsonNode node : array(root, "openQuestions")) questions.add(node.asText(""));
    return new Report(text(root, "summary"), criteria, samples, questions);
  }

  private List<JsonNode> array(JsonNode root, String field) {
    JsonNode node = root.path(field);
    List<JsonNode> list = new ArrayList<>();
    if (node.isArray()) node.forEach(list::add);
    return list;
  }

  private String text(JsonNode node, String field) {
    JsonNode value = node.path(field);
    return value.isMissingNode() || value.isNull() ? "" : value.asText("");
  }

  private String extractJson(String raw) {
    if (raw == null) throw new IllegalArgumentException("模型返回为空");
    String cleaned = raw.replaceAll("(?s)^\\s*```(?:json)?", "").replaceAll("(?s)```\\s*$", "").trim();
    int start = cleaned.indexOf('{');
    int end = cleaned.lastIndexOf('}');
    if (start < 0 || end <= start) throw new IllegalArgumentException("未找到 JSON 对象");
    return cleaned.substring(start, end + 1);
  }

  private String normalize(String text) {
    if (text == null) return "";
    return text.replace("\r\n", "\n").replace('\r', '\n')
        .replaceAll("\n{3,}", "\n\n").trim();
  }

  private String rootMessage(Exception e) {
    String message = e.getMessage();
    if (message == null || message.isBlank()) return e.getClass().getSimpleName();
    return message.length() > 300 ? message.substring(0, 300) : message;
  }

  private String preview(String value, int limit) {
    if (value == null) return "";
    String flat = value.replaceAll("\\s+", " ").trim();
    return flat.length() <= limit ? flat : flat.substring(0, limit) + "…";
  }

  private String hex(int length) {
    StringBuilder sb = new StringBuilder();
    for (int i = 0; i < length; i++) sb.append("0123456789abcdef".charAt(RANDOM.nextInt(16)));
    return sb.toString();
  }
}