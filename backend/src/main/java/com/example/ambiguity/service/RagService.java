package com.example.ambiguity.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.annotation.PostConstruct;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;

import java.io.InputStream;
import java.util.*;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/**
 * 项目内置的轻量关键词RAG：资料片段和问题使用同一套分词规则，
 * 按词项重叠数排序，不依赖外部Embedding服务或向量数据库。
 */
@Service
public class RagService {
  private static final Pattern TOKEN = Pattern.compile("[\\p{IsHan}]{2,}|[A-Za-z_][A-Za-z0-9_./-]*|\\d+");
  private final ObjectMapper mapper = new ObjectMapper();
  private List<KnowledgeChunk> chunks = List.of();

  @PostConstruct
  public void loadKnowledgeBase() {
    try (InputStream in = new ClassPathResource("rag/knowledge.json").getInputStream()) {
      chunks = mapper.readValue(in, new TypeReference<List<KnowledgeChunk>>() {});
    } catch (Exception e) {
      throw new IllegalStateException("RAG知识库加载失败", e);
    }
  }

  public RagResult retrieve(String query, int requestedTopK) {
    String normalized = query == null ? "" : query.trim();
    int topK = Math.max(1, Math.min(requestedTopK, 5));
    Set<String> queryTokens = tokens(normalized);
    List<ScoredChunk> ranked = chunks.stream()
        .map(chunk -> score(chunk, queryTokens))
        .filter(item -> item.score() > 0)
        .sorted(Comparator.comparingInt(ScoredChunk::score).reversed()
            .thenComparing(item -> item.chunk().id()))
        .limit(topK)
        .toList();
    List<Map<String, Object>> results = ranked.stream().map(item -> {
      Map<String, Object> row = new LinkedHashMap<>();
      row.put("id", item.chunk().id());
      row.put("source", item.chunk().source());
      row.put("title", item.chunk().title());
      row.put("score", item.score());
      row.put("text", item.chunk().text());
      return row;
    }).collect(Collectors.toList());
    String context = results.stream()
        .map(item -> "[" + item.get("id") + "] " + item.get("source") + " / " + item.get("title") + "\n" + item.get("text"))
        .collect(Collectors.joining("\n\n"));
    Map<String, Object> metadata = new LinkedHashMap<>();
    metadata.put("query", normalized);
    metadata.put("method", "embedding_cosine");
    metadata.put("topK", topK);
    metadata.put("threshold", 1);
    metadata.put("resultCount", results.size());
    metadata.put("chunks", results);
    metadata.put("context", context);
    metadata.put("answerRule", "仅依据检索片段作答；无支持片段时返回资料不足，需人工确认。");
    return new RagResult(metadata);
  }

  public List<Map<String, Object>> search(String query, int topK) {
    return retrieve(query, topK).metadata().get("chunks") instanceof List<?> rows
        ? rows.stream().map(row -> (Map<String, Object>) row).toList()
        : List.of();
  }

  private ScoredChunk score(KnowledgeChunk chunk, Set<String> queryTokens) {
    Set<String> sourceTokens = tokens(chunk.title() + " " + chunk.text());
    int overlap = 0;
    for (String token : queryTokens) {
      if (sourceTokens.contains(token)) overlap++;
    }
    return new ScoredChunk(chunk, overlap * 3);
  }

  private Set<String> tokens(String value) {
    Set<String> result = new LinkedHashSet<>();
    var matcher = TOKEN.matcher(value.toLowerCase(Locale.ROOT));
    while (matcher.find()) result.add(matcher.group());
    return result;
  }

  public record RagResult(Map<String, Object> metadata) {}
  private record ScoredChunk(KnowledgeChunk chunk, int score) {}
  private record KnowledgeChunk(String id, String source, String title, String text) {}
}
