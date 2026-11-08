package com.example.ambiguity.controller;

import com.example.ambiguity.service.RagService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api/rag")
public class RagController {
  private final RagService rag;

  public RagController(RagService rag) { this.rag = rag; }

  @GetMapping("/search")
  public Map<String, Object> search(@RequestParam String q, @RequestParam(defaultValue = "3") int k) {
    if (q == null || q.isBlank()) throw new IllegalArgumentException("检索问题不能为空");
    return rag.retrieve(q, k).metadata();
  }
}
