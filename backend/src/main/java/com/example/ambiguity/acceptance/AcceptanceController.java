package com.example.ambiguity.acceptance;

import com.example.ambiguity.acceptance.dto.AcceptanceDtos.RunRequest;
import com.example.ambiguity.acceptance.dto.AcceptanceDtos.RunResponse;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/acceptance")
public class AcceptanceController {
  private final AcceptanceService service;

  public AcceptanceController(AcceptanceService service) {
    this.service = service;
  }

  @PostMapping("/runs")
  public RunResponse run(@RequestBody RunRequest request) {
    return service.run(request);
  }

  @ExceptionHandler(IllegalArgumentException.class)
  ResponseEntity<Map<String, String>> badRequest(IllegalArgumentException e) {
    return ResponseEntity.badRequest().contentType(MediaType.APPLICATION_JSON)
        .body(Map.of("error", e.getMessage() == null ? "请求参数不合法" : e.getMessage()));
  }

  @ExceptionHandler(Exception.class)
  ResponseEntity<Map<String, String>> serverError(Exception e) {
    return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).contentType(MediaType.APPLICATION_JSON)
        .body(Map.of("error", e.getMessage() == null ? "生成失败" : e.getMessage()));
  }
}