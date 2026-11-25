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
import java.util.regex.Pattern;

/**
 * 端到端主链路：输入规范化 → 需求类型判定 → 模型调用 → 解析 → 程序检查 → 有限修复 → 返回。
 * revised 版本启用程序检查与修复；original 版本保留 v1 的单次调用行为，便于同测试集复现。
 *
 * <p>带 {@link AcceptanceContext} 的调用用于集成层：在每个阶段边界检查取消信号并回报阶段，
 * 取消后即使模型返回也丢弃结果（迟到结果不写入任务）。</p>
 */
@Service
public class AcceptanceService {
  private static final DateTimeFormatter ID_TIME = DateTimeFormatter.ofPattern("yyyyMMdd-HHmmss");
  private static final SecureRandom RANDOM = new SecureRandom();
  private static final Pattern OUT_OF_SCOPE = Pattern.compile("(采购|报价|供应商|付款|审批|股票|基金|菜谱|旅游|医疗诊断|诉讼)");

  private final AcceptanceModelClient modelClient;
  private final AcceptancePrompts prompts;
  private final AcceptanceProperties props;
  private final AcceptanceRunLogger logger;
  private final AcceptanceChecker checker;
  private final ObjectMapper mapper = new ObjectMapper();

  public AcceptanceService(AcceptanceModelClient modelClient, AcceptancePrompts prompts,
                           AcceptanceProperties props, AcceptanceRunLogger logger,
                           AcceptanceChecker checker) {
    this.modelClient = modelClient;
    this.prompts = prompts;
    this.props = props;
    this.logger = logger;
    this.checker = checker;
  }

  public String modelName() {
    return props.getModel();
  }

  public RunResponse run(RunRequest request) {
    return run(request, AcceptanceContext.none());
  }

  /** 带任务上下文的运行：允许在阶段边界检查取消并回报阶段。 */
  public RunResponse run(RunRequest request, AcceptanceContext ctx) {
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
        "model", modelName(rule),
        "inputChars", text.length(), "inputPreview", preview(text, 80),
        "taskId", ctx.taskId() == null ? "" : ctx.taskId()
    ));

    if (ctx.isCancelled()) {
      logger.event(runId, 0, "cancel", Map.of("status", "CANCELLED", "stage", "before-start"));
      return cancelled(runId, version, rule, 0, started, 0, 0);
    }

    if (rule) {
      ctx.reportPhase("规则流程");
      Report report = RuleBaseline.build(text);
      long duration = System.currentTimeMillis() - started;
      logger.event(runId, 0, "finish", Map.of("status", "SUCCESS", "durationMs", duration,
          "criteria", report.acceptanceCriteria().size()));
      logger.artifact(runId, artifact(runId, version, "rule", text, List.of(), report, null, 1, duration, 0, 0));
      return new RunResponse(runId, "SUCCESS", version, "rule-baseline", duration,
          new Usage(0, 0, 0), report, null, 1, null, null);
    }

    if ("original".equals(version)) return singleCall(runId, text, version, started, ctx);
    return revisedRun(runId, text, version, started, ctx);
  }

  /** v1 行为：单次模型调用、只解析 JSON，不做程序检查与修复。 */
  private RunResponse singleCall(String runId, String text, String version, long started, AcceptanceContext ctx) {
    String system = prompts.load(version);
    List<Map<String, String>> messages = new ArrayList<>();
    messages.add(Map.of("role", "system", "content", system));
    messages.add(Map.of("role", "user", "content", "需求原文：\n" + text));
    logger.event(runId, 1, "model", Map.of("status", "start", "promptVersion", version));
    ctx.reportPhase("调用模型");

    AcceptanceModelClient.ChatResult result;
    try {
      result = modelClient.chat(messages);
    } catch (Exception e) {
      return failed(runId, text, version, started, 1, modelFailureMessage(e),
          errorCodeOf(e), List.of());
    }
    if (ctx.isCancelled()) {
      logger.event(runId, 1, "cancel", Map.of("status", "CANCELLED", "stage", "after-model", "lateResult", true));
      return cancelled(runId, version, false, 1, started, result.promptTokens(), result.completionTokens());
    }
    Report report;
    try {
      report = parseReport(result.content());
    } catch (Exception e) {
      String message = "输出不是合法 JSON：" + rootMessage(e);
      logger.event(runId, 1, "parse", Map.of("status", "error", "errorType", "PARSE_ERROR", "message", preview(message, 200)));
      return failed(runId, text, version, started, 1, message, "OUTPUT_INVALID",
          List.of(new Attempt(1, result.content(), null)));
    }
    long duration = result.durationMs() > 0 ? result.durationMs() : System.currentTimeMillis() - started;
    logger.event(runId, 1, "parse", Map.of("status", "ok",
        "criteria", report.acceptanceCriteria().size(), "testSamples", report.testSamples().size()));
    logger.event(runId, 1, "finish", Map.of("status", "SUCCESS", "durationMs", duration));
    logger.artifact(runId, artifact(runId, version, "model", text,
        List.of(new Attempt(1, result.content(), null)), report, null, 1, duration,
        result.promptTokens(), result.completionTokens()));
    return new RunResponse(runId, "SUCCESS", version, props.getModel(), duration,
        new Usage(result.promptTokens(), result.completionTokens(),
            result.promptTokens() + result.completionTokens()), report, null, 1, null, null);
  }

  /** v2 修订版：范围预检 + 模型调用 + 程序检查 + 有限修复。 */
  private RunResponse revisedRun(String runId, String text, String version, long started, AcceptanceContext ctx) {
    ctx.reportPhase("范围预检");
    if (OUT_OF_SCOPE.matcher(text).find()) {
      Report report = new Report("out_of_scope",
          "当前输入不是软件需求，已拒绝生成验收标准。",
          List.of(), List.of(),
          List.of("请提交软件功能需求原文（角色、输入、输出、边界与验收口径）。",
              "如需审查采购、付款、股票等非软件事项，请使用对应业务系统或人工流程。"),
          List.of("程序在调用模型前按范围规则拒绝，未产生费用。"));
      Checks checks = new Checks(true, true, true, true, List.of("程序判定为超出范围，未调用模型"));
      long duration = System.currentTimeMillis() - started;
      logger.event(runId, 0, "check", Map.of("status", "ok", "result", "OUT_OF_SCOPE"));
      logger.event(runId, 0, "finish", Map.of("status", "REFUSED", "durationMs", duration));
      logger.artifact(runId, artifact(runId, version, "model", text, List.of(), report, checks, 0, duration, 0, 0));
      return new RunResponse(runId, "REFUSED", version, props.getModel(), duration,
          new Usage(0, 0, 0), report, checks, 0, null, "SCOPE_REJECTED");
    }

    String system = prompts.load(version);
    List<Map<String, String>> messages = new ArrayList<>();
    messages.add(Map.of("role", "system", "content", system));
    messages.add(Map.of("role", "user", "content", "需求原文：\n" + text));

    List<Attempt> attempts = new ArrayList<>();
    int promptTokens = 0;
    int completionTokens = 0;
    long totalMs = 0;
    Report report = null;
    Checks checks = null;
    String lastError = null;
    String errorCode = null;

    for (int attempt = 1; attempt <= props.getMaxAttempts(); attempt++) {
      if (ctx.isCancelled()) {
        logger.event(runId, attempt, "cancel", Map.of("status", "CANCELLED", "stage", "before-attempt"));
        return cancelled(runId, version, false, attempt - 1, started, promptTokens, completionTokens);
      }
      logger.event(runId, attempt, "model", Map.of("status", "start", "promptVersion", version,
          "messages", messages.size()));
      ctx.reportPhase("调用模型（第 " + attempt + " 次）");
      AcceptanceModelClient.ChatResult result;
      try {
        result = modelClient.chat(messages);
      } catch (Exception e) {
        lastError = modelFailureMessage(e);
        errorCode = errorCodeOf(e);
        logger.event(runId, attempt, "model", Map.of("status", "error",
            "errorType", "MODEL_ERROR", "errorCode", errorCode, "message", preview(lastError, 200)));
        return failedWith(runId, text, version, started, attempt, attempts, lastError, errorCode,
            promptTokens, completionTokens, totalMs);
      }
      if (ctx.isCancelled()) {
        logger.event(runId, attempt, "cancel", Map.of("status", "CANCELLED",
            "stage", "after-model", "lateResult", true, "durationMs", result.durationMs()));
        return cancelled(runId, version, false, attempt, started,
            promptTokens + result.promptTokens(), completionTokens + result.completionTokens());
      }
      promptTokens += result.promptTokens();
      completionTokens += result.completionTokens();
      totalMs += result.durationMs();
      logger.event(runId, attempt, "model", Map.of("status", "ok",
          "durationMs", result.durationMs(), "promptTokens", result.promptTokens(),
          "completionTokens", result.completionTokens()));

      try {
        report = parseReport(result.content());
      } catch (Exception e) {
        lastError = "输出不是合法 JSON：" + rootMessage(e);
        errorCode = "OUTPUT_INVALID";
        attempts.add(new Attempt(attempt, result.content(), null));
        logger.event(runId, attempt, "parse", Map.of("status", "error",
            "errorType", "PARSE_ERROR", "message", preview(lastError, 160)));
        if (attempt < props.getMaxAttempts()) {
          messages.add(Map.of("role", "assistant", "content", truncate(result.content(), 6000)));
          messages.add(Map.of("role", "user", "content",
              "上一版输出无法解析为 JSON：" + rootMessage(e)
                  + "。请只输出一个合法的 JSON 对象，字段与结构必须完全符合系统要求。"));
          logger.event(runId, attempt, "repair", Map.of("status", "start", "reason", "PARSE_ERROR"));
          continue;
        }
        return failedWith(runId, text, version, started, attempt, attempts, lastError, errorCode,
            promptTokens, completionTokens, totalMs);
      }

      ctx.reportPhase("程序检查（第 " + attempt + " 次）");
      checks = checker.check(text, report);
      attempts.add(new Attempt(attempt, result.content(), checks));
      logger.event(runId, attempt, "check", Map.of("status", checks.acceptable() ? "ok" : "error",
          "schemaOk", checks.schemaOk(), "groundingOk", checks.groundingOk(),
          "structureOk", checks.structureOk(), "coverageOk", checks.coverageOk(),
          "messages", String.join("；", checks.messages())));

      if (ctx.isCancelled()) {
        logger.event(runId, attempt, "cancel", Map.of("status", "CANCELLED", "stage", "after-check"));
        return cancelled(runId, version, false, attempt, started, promptTokens, completionTokens);
      }

      if (checks.acceptable()) {
        long duration = totalMs > 0 ? totalMs : System.currentTimeMillis() - started;
        logger.event(runId, attempt, "finish", Map.of("status", "SUCCESS", "durationMs", duration));
        logger.artifact(runId, artifact(runId, version, "model", text, attempts, report, checks,
            attempt, duration, promptTokens, completionTokens));
        return new RunResponse(runId, "SUCCESS", version, props.getModel(), duration,
            new Usage(promptTokens, completionTokens, promptTokens + completionTokens),
            report, checks, attempt, null, null);
      }

      if (attempt < props.getMaxAttempts()) {
        messages.add(Map.of("role", "assistant", "content", truncate(result.content(), 6000)));
        messages.add(Map.of("role", "user", "content", repairInstruction(checks.messages())));
        logger.event(runId, attempt, "repair", Map.of("status", "start",
            "reason", preview(String.join("；", checks.messages()), 200)));
        lastError = String.join("；", checks.messages());
        errorCode = "CHECK_FAILED";
      }
    }

    long duration = totalMs > 0 ? totalMs : System.currentTimeMillis() - started;
    logger.event(runId, props.getMaxAttempts(), "finish", Map.of("status", "CHECK_FAILED", "durationMs", duration));
    logger.artifact(runId, artifact(runId, version, "model", text, attempts, report, checks,
        props.getMaxAttempts(), duration, promptTokens, completionTokens));
    return new RunResponse(runId, "CHECK_FAILED", version, props.getModel(), duration,
        new Usage(promptTokens, completionTokens, promptTokens + completionTokens),
        report, checks, props.getMaxAttempts(),
        "结果未通过程序检查：" + (lastError == null ? "未知原因" : lastError), "CHECK_FAILED");
  }

  private RunResponse cancelled(String runId, String version, boolean rule, int attempts, long started,
                                int promptTokens, int completionTokens) {
    long duration = System.currentTimeMillis() - started;
    logger.event(runId, attempts, "finish", Map.of("status", "CANCELLED", "durationMs", duration));
    return new RunResponse(runId, "CANCELLED", version, modelName(rule), duration,
        new Usage(promptTokens, completionTokens, promptTokens + completionTokens),
        null, null, attempts, "任务已取消，返回结果已丢弃", "CANCELLED");
  }

  private String modelName(boolean rule) {
    return rule ? "rule-baseline" : props.getModel();
  }

  private String repairInstruction(List<String> messages) {
    return "上一版输出未通过程序检查：" + String.join("；", messages)
        + "。请重写完整 JSON，逐条修正上述问题：requirementKind 必须正确；引用必须逐字来自原文；"
        + "正常需求的每条验收标准必须包含 Given/When/Then；测试样例必须同时覆盖 normal、boundary、exception；"
        + "信息不足或超出范围时不要生成验收标准。只输出 JSON。";
  }

  private RunResponse failed(String runId, String text, String version, long started,
                             int attempts, String message, String errorCode, List<Attempt> attemptList) {
    long duration = System.currentTimeMillis() - started;
    logger.event(runId, attempts, "finish", Map.of("status", "FAILED", "durationMs", duration,
        "errorCode", errorCode == null ? "" : errorCode));
    logger.artifact(runId, artifact(runId, version, "model", text, attemptList, null, null,
        attempts, duration, 0, 0));
    return new RunResponse(runId, "FAILED", version, props.getModel(), duration,
        new Usage(0, 0, 0), null, null, attempts, message, errorCode);
  }

  private RunResponse failedWith(String runId, String text, String version, long started, int attempts,
                                 List<Attempt> attemptList, String message, String errorCode,
                                 int promptTokens, int completionTokens, long totalMs) {
    long duration = totalMs > 0 ? totalMs : System.currentTimeMillis() - started;
    logger.event(runId, attempts, "finish", Map.of("status", "FAILED", "durationMs", duration,
        "errorCode", errorCode == null ? "" : errorCode));
    logger.artifact(runId, artifact(runId, version, "model", text, attemptList, null, null,
        attempts, duration, promptTokens, completionTokens));
    return new RunResponse(runId, "FAILED", version, props.getModel(), duration,
        new Usage(promptTokens, completionTokens, promptTokens + completionTokens),
        null, null, attempts, message, errorCode);
  }

  /** 模型通道已经把“模型调用失败”写进消息，这里避免重复前缀。 */
  private String modelFailureMessage(Throwable e) {
    String message = rootMessage(e);
    return message.startsWith("模型调用失败") ? message : "模型调用失败：" + message;
  }

  /** 把模型通道异常归一到有限错误码，供前端给出不同提示与可选操作。 */
  private String errorCodeOf(Throwable e) {
    String message = rootMessage(e).toLowerCase(Locale.ROOT);
    Throwable cause = e.getCause();
    String causeMessage = cause == null ? "" : String.valueOf(cause.getMessage()).toLowerCase(Locale.ROOT);
    String merged = message + " " + causeMessage;
    if (merged.contains("timed out") || merged.contains("timeout") || merged.contains("超时")) {
      return "MODEL_TIMEOUT";
    }
    if (merged.contains("未配置") || merged.contains("api key") || merged.contains("unauthorized")
        || merged.contains("401")) {
      return "MODEL_UNAVAILABLE";
    }
    return "MODEL_ERROR";
  }

  private Map<String, Object> artifact(String runId, String version, String mode, String text,
                                       List<Attempt> attempts, Report report, Checks checks,
                                       int attemptCount, long durationMs, int promptTokens, int completionTokens) {
    Map<String, Object> data = new LinkedHashMap<>();
    data.put("runId", runId);
    data.put("promptVersion", version);
    data.put("mode", mode);
    data.put("model", props.getModel());
    data.put("durationMs", durationMs);
    data.put("promptTokens", promptTokens);
    data.put("completionTokens", completionTokens);
    data.put("attempts", attemptCount);
    data.put("inputChars", text.length());
    data.put("input", text);
    data.put("report", report);
    data.put("checks", checks);
    List<Map<String, Object>> rawAttempts = new ArrayList<>();
    for (Attempt attempt : attempts) {
      Map<String, Object> row = new LinkedHashMap<>();
      row.put("attempt", attempt.number());
      row.put("rawOutput", preview(attempt.raw(), 8000));
      row.put("checks", attempt.checks());
      rawAttempts.add(row);
    }
    data.put("rawAttempts", rawAttempts);
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
    List<String> limits = new ArrayList<>();
    for (JsonNode node : array(root, "limits")) limits.add(node.asText(""));
    return new Report(text(root, "requirementKind"), text(root, "summary"),
        criteria, samples, questions, limits);
  }

  private List<JsonNode> array(JsonNode root, String field) {
    JsonNode node = root.path(field);
    List<JsonNode> list = new ArrayList<>();
    if (node.isArray()) node.forEach(list::add);
    return list;
  }

  private String text(JsonNode node, String field) {
    JsonNode value = node.path(field);
    if (value.isMissingNode() || value.isNull()) return "";
    if (value.isContainerNode()) return value.toString();
    return value.asText("");
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

  private String rootMessage(Throwable e) {
    String message = e.getMessage();
    if (message == null || message.isBlank()) return e.getClass().getSimpleName();
    return message.length() > 300 ? message.substring(0, 300) : message;
  }

  private String preview(String value, int limit) {
    if (value == null) return "";
    String flat = value.replaceAll("\\s+", " ").trim();
    return flat.length() <= limit ? flat : flat.substring(0, limit) + "…";
  }

  private String truncate(String value, int limit) {
    if (value == null) return "";
    return value.length() <= limit ? value : value.substring(0, limit);
  }

  private String hex(int length) {
    StringBuilder sb = new StringBuilder();
    for (int i = 0; i < length; i++) sb.append("0123456789abcdef".charAt(RANDOM.nextInt(16)));
    return sb.toString();
  }

  private record Attempt(int number, String raw, Checks checks) {}
}