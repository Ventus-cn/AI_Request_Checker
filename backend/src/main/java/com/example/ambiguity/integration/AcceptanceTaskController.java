package com.example.ambiguity.integration;

import com.example.ambiguity.integration.TaskDtos.ApplyResponse;
import com.example.ambiguity.integration.TaskDtos.EditRequest;
import com.example.ambiguity.integration.TaskDtos.SubmitRequest;
import com.example.ambiguity.integration.TaskDtos.TaskView;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;

/**
 * 集成层任务接口。所有响应使用 TaskView；错误统一为 {code,error,status,retryable,actions}，
 * 界面据此决定显示哪条提示、给出哪些按钮，而不是各自拼字符串。
 */
@RestController
@RequestMapping("/api/acceptance/tasks")
public class AcceptanceTaskController {
  private final AcceptanceTaskService service;

  public AcceptanceTaskController(AcceptanceTaskService service) {
    this.service = service;
  }

  @PostMapping
  public ResponseEntity<TaskView> submit(@RequestBody SubmitRequest request) {
    TaskView view = service.submit(request);
    return ResponseEntity.status(view.duplicate() ? HttpStatus.OK : HttpStatus.ACCEPTED).body(view);
  }

  @GetMapping("/{taskId}")
  public TaskView get(@PathVariable String taskId) {
    return service.get(taskId);
  }

  @GetMapping
  public List<TaskView> list(@RequestParam("reviewId") String reviewId) {
    return service.listByReview(reviewId);
  }

  @PostMapping("/{taskId}/cancel")
  public ResponseEntity<TaskView> cancel(@PathVariable String taskId) {
    return ResponseEntity.accepted().body(service.cancel(taskId));
  }

  @PostMapping("/{taskId}/retry")
  public ResponseEntity<TaskView> retry(@PathVariable String taskId) {
    return ResponseEntity.accepted().body(service.retry(taskId));
  }

  @PostMapping("/{taskId}/fallback")
  public TaskView fallback(@PathVariable String taskId) {
    return service.fallback(taskId);
  }

  @PostMapping("/{taskId}/handoff")
  public ResponseEntity<TaskView> handoff(@PathVariable String taskId) {
    return ResponseEntity.status(HttpStatus.CREATED).body(service.handoff(taskId));
  }

  @PutMapping("/{taskId}/result")
  public TaskView edit(@PathVariable String taskId, @RequestBody EditRequest request) {
    return service.edit(taskId, request);
  }

  @PostMapping("/{taskId}/apply")
  public ApplyResponse apply(@PathVariable String taskId) {
    return service.apply(taskId);
  }

  @PostMapping("/{taskId}/discard")
  public TaskView discard(@PathVariable String taskId) {
    return service.discard(taskId);
  }

  @ExceptionHandler(ApiException.class)
  public ResponseEntity<Map<String, Object>> apiError(ApiException e) {
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("code", e.getCode());
    body.put("error", e.getMessage());
    body.put("status", e.getStatus());
    body.put("retryable", e.isRetryable());
    body.put("actions", e.getActions());
    return ResponseEntity.status(e.getStatus()).contentType(MediaType.APPLICATION_JSON).body(body);
  }

  @ExceptionHandler(NoSuchElementException.class)
  public ResponseEntity<Map<String, Object>> notFound(NoSuchElementException e) {
    return error(HttpStatus.NOT_FOUND, "REVIEW_NOT_FOUND",
        e.getMessage() == null ? "审查记录不存在" : e.getMessage(), false, List.of("返回档案列表"));
  }

  @ExceptionHandler(IllegalArgumentException.class)
  public ResponseEntity<Map<String, Object>> badRequest(IllegalArgumentException e) {
    return error(HttpStatus.BAD_REQUEST, "INPUT_INVALID",
        e.getMessage() == null ? "请求参数不合法" : e.getMessage(), false, List.of("检查输入"));
  }

  private ResponseEntity<Map<String, Object>> error(HttpStatus status, String code, String message,
                                                    boolean retryable, List<String> actions) {
    Map<String, Object> body = new LinkedHashMap<>();
    body.put("code", code);
    body.put("error", message);
    body.put("status", status.value());
    body.put("retryable", retryable);
    body.put("actions", actions);
    return ResponseEntity.status(status).contentType(MediaType.APPLICATION_JSON).body(body);
  }
}