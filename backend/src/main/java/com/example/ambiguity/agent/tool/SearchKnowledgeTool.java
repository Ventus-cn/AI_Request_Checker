package com.example.ambiguity.agent.tool;

import com.example.ambiguity.service.RagService;
import org.springframework.stereotype.Component;

import java.util.*;

/**
 * 只读工具：检索内置知识库（关键词匹配，top-k ≤ 5），返回带编号的片段供回答引用。
 */
@Component
public class SearchKnowledgeTool implements Tool {
  private final RagService rag;

  public SearchKnowledgeTool(RagService rag) {
    this.rag = rag;
  }

  @Override
  public ToolSpec spec() {
    Map<String, Object> properties = new LinkedHashMap<>();
    properties.put("q", Map.of("type", "string", "minLength", 2, "maxLength", 100,
        "description", "检索问题或关键词"));
    properties.put("k", Map.of("type", "integer", "minimum", 1, "maximum", 5, "default", 3,
        "description", "返回片段数，1-5"));
    Map<String, Object> schema = new LinkedHashMap<>();
    schema.put("type", "object");
    schema.put("properties", properties);
    schema.put("required", List.of("q"));
    schema.put("additionalProperties", false);
    return new ToolSpec("search_knowledge", "检索项目知识库中的规则片段（如文件上传限制、报告结构、安全要求），回答时引用片段编号。", schema);
  }

  @Override
  public Map<String, Object> execute(Map<String, Object> args) {
    String query = String.valueOf(args.get("q"));
    int k = (Integer) args.getOrDefault("k", 3);
    List<Map<String, Object>> chunks = new ArrayList<>();
    for (Map<String, Object> chunk : rag.search(query, k)) {
      Map<String, Object> row = new LinkedHashMap<>();
      row.put("id", chunk.get("id"));
      row.put("source", chunk.get("source"));
      row.put("title", chunk.get("title"));
      row.put("score", chunk.get("score"));
      row.put("text", truncate(chunk.get("text"), 300));
      chunks.add(row);
    }
    Map<String, Object> result = new LinkedHashMap<>();
    result.put("query", query);
    result.put("resultCount", chunks.size());
    result.put("chunks", chunks);
    if (chunks.isEmpty()) {
      result.put("hint", "资料不足，需人工确认；不得编造知识库内容。");
    }
    return result;
  }

  private static String truncate(Object value, int max) {
    String text = value == null ? "" : String.valueOf(value);
    return text.length() <= max ? text : text.substring(0, max) + "…";
  }
}