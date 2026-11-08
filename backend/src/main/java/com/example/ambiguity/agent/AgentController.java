package com.example.ambiguity.agent;

import com.example.ambiguity.agent.dto.AgentDtos.*;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.NoSuchElementException;

/**
 * 档案分析 Agent 的 REST 入口。
 * 错误响应统一为 {"error": "..."}，不暴露 API Key、堆栈或本机路径。
 */
@RestController
@RequestMapping("/api/agent")
public class AgentController {
  private final AgentService service;

  public AgentController(AgentService service) {
    this.service = service;
  }

  @PostMapping("/runs")
  public RunResponse run(@RequestBody(required = false) RunRequest request) {
    if (request == null || request.question() == null || request.question().isBlank()) {
      throw new IllegalArgumentException("问题不能为空");
    }
    String question = request.question().trim();
    if (question.length() > 500) {
      throw new IllegalArgumentException("问题不能超过 500 个字符");
    }
    return service.start(question);
  }

  @PostMapping("/runs/{taskId}/confirm")
  public RunResponse confirm(@PathVariable String taskId,
                             @RequestBody(required = false) ConfirmRequest request) {
    if (request == null || request.approved() == null) {
      throw new IllegalArgumentException("缺少 approved 字段");
    }
    return service.confirm(taskId, request.approved());
  }

  @ExceptionHandler(NoSuchElementException.class)
  public ResponseEntity<Map<String, String>> notFound(NoSuchElementException e) {
    return ResponseEntity.status(HttpStatus.NOT_FOUND).contentType(MediaType.APPLICATION_JSON)
        .body(Map.of("error", e.getMessage() == null ? "任务不存在" : e.getMessage()));
  }

  @ExceptionHandler(IllegalArgumentException.class)
  public ResponseEntity<Map<String, String>> badRequest(IllegalArgumentException e) {
    return ResponseEntity.status(HttpStatus.BAD_REQUEST).contentType(MediaType.APPLICATION_JSON)
        .body(Map.of("error", e.getMessage() == null ? "请求参数错误" : e.getMessage()));
  }
}