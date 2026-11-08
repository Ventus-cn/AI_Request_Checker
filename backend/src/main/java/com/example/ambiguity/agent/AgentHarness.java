package com.example.ambiguity.agent;

import com.example.ambiguity.agent.dto.AgentDtos.ConfirmView;
import com.example.ambiguity.agent.dto.AgentDtos.RunResponse;
import com.example.ambiguity.agent.dto.AgentDtos.StepView;
import com.example.ambiguity.agent.model.AgentModelClient;
import com.example.ambiguity.agent.tool.ArgumentValidator;
import com.example.ambiguity.agent.tool.Tool;
import com.example.ambiguity.agent.tool.ToolException;
import com.example.ambiguity.agent.tool.ToolRegistry;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.*;
import java.util.concurrent.*;

/**
 * 运行时 Harness：负责上下文组装、模型调用、工具分发、参数与权限检查、
 * 结果回传、人工确认、步数与时间控制以及运行日志。
 *
 * 关键限制全部由程序执行：模型无法跳过白名单、参数校验、步数上限或确认流程。
 */
@Service
public class AgentHarness {
  private static final String SYSTEM_PROMPT = """
      你是“审查档案分析助手”，服务于 AI 需求歧义审查器。
      必须遵守：
      1. 只依据工具返回的数据回答，禁止编造档案数量、风险等级、问题内容或知识库规则。
      2. 统计类问题（例如“有多少份档案、风险分布如何”）必须先调用 compute_risk_stats，
         回答中写出总数和高/中/低风险数量，且必须与工具结果一致。
      3. 引用知识库内容时必须标注片段编号，例如 [KB-003]。
      4. 只能调用给定的工具；不要尝试执行命令、SQL、脚本或访问文件系统。
      5. delete_review 是写操作。用户明确要求删除某条档案时，直接调用 delete_review
         （程序会自动弹出确认，由用户决定是否执行），不要先反问用户要 ID。
      6. 工具返回错误（ARG_INVALID、NOT_FOUND、TIMEOUT 等）时，按错误信息调整参数或换用其他工具；
         无法完成时明确说明原因，不要假装完成。
      7. 用中文回答，先给结论再给依据，控制在 300 字以内。
      """;

  private final ToolRegistry registry;
  private final AgentModelClient model;
  private final AgentRunLogger logger;
  private final AnswerChecker checker;
  private final AgentRunStore store;
  private final ObjectMapper mapper = new ObjectMapper();
  private final ExecutorService executor = Executors.newFixedThreadPool(4, runnable -> {
    Thread thread = new Thread(runnable, "agent-tool");
    thread.setDaemon(true);
    return thread;
  });

  @Value("${app.agent.max-steps:6}")
  private int maxSteps = 6;
  @Value("${app.agent.max-tool-calls-per-step:3}")
  private int maxToolCallsPerStep = 3;
  @Value("${app.agent.total-timeout-ms:60000}")
  private long totalTimeoutMs = 60000;
  @Value("${app.agent.tool-timeout-ms:5000}")
  private long toolTimeoutMs = 5000;
  @Value("${app.agent.max-answer-retries:2}")
  private int maxAnswerRetries = 2;

  public AgentHarness(ToolRegistry registry, AgentModelClient model, AgentRunLogger logger,
                      AnswerChecker checker, AgentRunStore store) {
    this.registry = registry;
    this.model = model;
    this.logger = logger;
    this.checker = checker;
    this.store = store;
  }

  public RunResponse start(String question) {
    String taskId = logger.newTaskId();
    AgentRun run = new AgentRun(taskId, question, System.currentTimeMillis() + totalTimeoutMs);
    run.addMessage("system", SYSTEM_PROMPT);
    run.addMessage("user", question);
    logger.write(taskId, 0, "context", "ok",
        Map.of("questionChars", question.length(), "tools", String.join(",", registry.names())));
    return loop(run);
  }

  public RunResponse confirm(String taskId, boolean approved) {
    AgentRunStore.Pending pending = store.take(taskId);
    AgentRun run = pending.run();
    if (run.expired()) {
      return finish(run, "TIMEOUT", "确认前已超过运行总时限，未执行任何写操作。");
    }
    Tool tool = registry.require(pending.tool());
    if (!approved) {
      appendTool(run, pending.callId(), pending.tool(), "用户拒绝执行，工具未执行。");
      logger.write(run.taskId, run.step, "confirm", "rejected", Map.of("tool", pending.tool()));
      return finish(run, "DENIED", "已取消，未删除任何档案。");
    }
    Map<String, Object> args;
    try {
      args = mapper.readValue(pending.args(), new TypeReference<Map<String, Object>>() {});
    } catch (Exception e) {
      return finish(run, "FAILED", "确认数据损坏，未执行删除。");
    }
    logger.write(run.taskId, run.step, "confirm", "approved", Map.of("tool", pending.tool()));
    executeTool(run, pending.callId(), pending.tool(), tool, args);
    return loop(run);
  }

  private RunResponse loop(AgentRun run) {
    while (true) {
      if (run.step >= maxSteps) {
        return finish(run, "STEP_LIMIT", "已达到最大执行步数（" + maxSteps + "），本次分析未完成。已完成 "
            + run.steps.size() + " 次工具调用，请缩小问题范围后重试。");
      }
      if (run.expired()) {
        return finish(run, "TIMEOUT", "已超过本次运行总时限（" + (totalTimeoutMs / 1000)
            + " 秒），已停止等待。工具可能仍在后台执行，状态未知，请刷新页面核对。");
      }
      run.step++;
      run.toolCallsThisStep = 0;
      long started = System.currentTimeMillis();
      AgentModelClient.ChatResult result;
      try {
        result = model.complete(run.messages, registry.schemas());
      } catch (Exception e) {
        logger.write(run.taskId, run.step, "model", "error",
            Map.of("errorType", "TOOL_EXCEPTION", "result", AgentRunLogger.brief(e.getMessage(), 200)));
        return finish(run, "FAILED", "模型调用失败，请稍后重试：" + e.getMessage());
      }
      Map<String, Object> message = result.message();
      run.messages.add(message);
      logger.write(run.taskId, run.step, "model", "ok", Map.of(
          "durationMs", System.currentTimeMillis() - started,
          "promptTokens", result.promptTokens(),
          "completionTokens", result.completionTokens()));

      List<Map<String, Object>> calls = toolCalls(message);
      if (calls.isEmpty()) {
        String answer = String.valueOf(message.getOrDefault("content", "")).trim();
        AnswerChecker.Result check = checker.check(run, answer);
        logger.write(run.taskId, run.step, "check", check.ok() ? "ok" : "error", Map.of("result", check.reason()));
        if (check.ok()) return finish(run, "SUCCESS", answer);
        if (run.answerRetries >= maxAnswerRetries) {
          return finish(run, "CHECK_FAILED", answer + "\n\n（程序校验未通过：" + check.reason() + "）");
        }
        run.answerRetries++;
        run.addMessage("system", check.repairMessage());
        continue;
      }

      for (Map<String, Object> call : calls) {
        if (run.toolCallsThisStep >= maxToolCallsPerStep) {
          appendTool(run, toolCallId(call), toolName(call),
              "REJECTED：单步工具调用超过 " + maxToolCallsPerStep + " 个，本次调用未执行。");
          continue;
        }
        run.toolCallsThisStep++;
        RunResponse confirmation = handleCall(run, call);
        if (confirmation != null) return confirmation;
      }
    }
  }

  /** 返回非 null 表示运行被挂起，等待人工确认。 */
  private RunResponse handleCall(AgentRun run, Map<String, Object> call) {
    String callId = toolCallId(call);
    String name = toolName(call);
    Map<String, Object> rawArgs = new LinkedHashMap<>();
    Object rawArguments = function(call).get("arguments");
    if (rawArguments instanceof Map<?, ?> map) {
      Map<String, Object> converted = new LinkedHashMap<>();
      map.forEach((key, value) -> converted.put(String.valueOf(key), value));
      rawArgs = converted;
    } else {
      String json = rawArguments == null ? "{}" : String.valueOf(rawArguments);
      try {
        Map<String, Object> parsed = json.isBlank() ? new LinkedHashMap<>()
            : mapper.readValue(json, new TypeReference<Map<String, Object>>() {});
        rawArgs = parsed;
      } catch (Exception e) {
        failTool(run, callId, name, ToolException.ARG_INVALID, "参数不是合法 JSON：" + AgentRunLogger.brief(json, 120));
        return null;
      }
    }

    Tool tool;
    Map<String, Object> args;
    try {
      tool = registry.require(name);
      args = ArgumentValidator.validate(tool.spec(), rawArgs);
    } catch (ToolException e) {
      failTool(run, callId, name, e.errorType(), e.getMessage());
      return null;
    }

    if (tool.requiresConfirmation()) {
      String argsJson = writeJson(args);
      run.pendingTool = name;
      run.pendingArgs = argsJson;
      store.put(run, name, argsJson, callId);
      logger.write(run.taskId, run.step, "confirm", "pending",
          Map.of("tool", name, "args", AgentRunLogger.brief(argsJson, 120)));
      return new RunResponse(run.taskId, "NEED_CONFIRM",
          "该操作会修改数据，需要你确认后才会执行。",
          List.copyOf(run.steps), new ConfirmView(name, tool.describeImpact(args)), null);
    }
    executeTool(run, callId, name, tool, args);
    return null;
  }

  private void executeTool(AgentRun run, String callId, String name, Tool tool, Map<String, Object> args) {
    long started = System.currentTimeMillis();
    String argsText = writeJson(args);
    Future<Map<String, Object>> future = null;
    try {
      future = executor.submit(() -> tool.execute(args));
      Map<String, Object> output = future.get(toolTimeoutMs, TimeUnit.MILLISECONDS);
      String json = writeJson(output);
      appendTool(run, callId, name, json);
      applyState(run, name, output);
      long elapsed = System.currentTimeMillis() - started;
      run.steps.add(new StepView(run.step, name, AgentRunLogger.brief(argsText, 120),
          AgentRunLogger.brief(json, 160), "ok", elapsed));
      logger.write(run.taskId, run.step, "tool", "ok", Map.of(
          "tool", name, "args", AgentRunLogger.brief(argsText, 120),
          "result", AgentRunLogger.brief(json, 200), "durationMs", elapsed));
    } catch (TimeoutException e) {
      if (future != null) future.cancel(true);
      failTool(run, callId, name, ToolException.TIMEOUT,
          "工具执行超过 " + toolTimeoutMs + "ms，已停止等待（后台可能仍在执行，状态未知）");
    } catch (ExecutionException e) {
      Throwable cause = e.getCause();
      if (cause instanceof ToolException toolError) {
        failTool(run, callId, name, toolError.errorType(), toolError.getMessage());
      } else {
        String errorType = tool.requiresConfirmation() ? ToolException.STATE_UNKNOWN : ToolException.TOOL_EXCEPTION;
        failTool(run, callId, name, errorType,
            "工具执行异常：" + (cause == null ? e.getMessage() : cause.getMessage()));
      }
    } catch (InterruptedException e) {
      Thread.currentThread().interrupt();
      failTool(run, callId, name, ToolException.TOOL_EXCEPTION, "工具执行被中断");
    }
  }

  private void applyState(AgentRun run, String name, Map<String, Object> output) {
    if ("compute_risk_stats".equals(name)) {
      run.lastStats = output;
    } else if ("search_knowledge".equals(name)) {
      Object count = output.get("resultCount");
      run.lastKnowledgeCount = count instanceof Number number ? number.intValue() : 0;
    } else if ("delete_review".equals(name)) {
      run.deleteExecuted = Boolean.TRUE.equals(output.get("deleted"));
    }
  }

  private void failTool(AgentRun run, String callId, String name, String errorType, String message) {
    String content = errorType + "：" + message;
    appendTool(run, callId, name, content);
    run.steps.add(new StepView(run.step, name, "—", AgentRunLogger.brief(content, 160), "error", 0));
    logger.write(run.taskId, run.step, "tool", "error",
        Map.of("tool", name, "errorType", errorType, "result", AgentRunLogger.brief(message, 200)));
  }

  private void appendTool(AgentRun run, String callId, String name, String content) {
    Map<String, Object> message = new LinkedHashMap<>();
    message.put("role", "tool");
    message.put("tool_call_id", callId);
    message.put("name", name);
    message.put("content", content.length() > 2000 ? content.substring(0, 2000) + "…" : content);
    run.messages.add(message);
  }

  private RunResponse finish(AgentRun run, String status, String answer) {
    logger.write(run.taskId, run.step, "finish", "ok", Map.of(
        "finalStatus", status, "steps", run.steps.size(),
        "durationMs", System.currentTimeMillis() - run.startedAt));
    return new RunResponse(run.taskId, status, answer, List.copyOf(run.steps), null, null);
  }

  private List<Map<String, Object>> toolCalls(Map<String, Object> message) {
    if (!(message.get("tool_calls") instanceof List<?> list)) return List.of();
    List<Map<String, Object>> calls = new ArrayList<>();
    for (Object item : list) {
      if (item instanceof Map<?, ?> map) {
        Map<String, Object> copy = new LinkedHashMap<>();
        map.forEach((key, value) -> copy.put(String.valueOf(key), value));
        calls.add(copy);
      }
    }
    return calls;
  }

  private Map<?, ?> function(Map<String, Object> call) {
    return call.get("function") instanceof Map<?, ?> map ? map : Map.of();
  }

  private String toolCallId(Map<String, Object> call) {
    Object id = call.get("id");
    return id == null ? "call_" + Math.abs(call.hashCode()) : String.valueOf(id);
  }

  private String toolName(Map<String, Object> call) {
    Object name = function(call).get("name");
    return name == null ? "unknown" : String.valueOf(name);
  }

  private String writeJson(Object value) {
    try {
      return mapper.writeValueAsString(value);
    } catch (Exception e) {
      return "{}";
    }
  }
}