package com.example.ambiguity.acceptance;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.OffsetDateTime;
import java.util.LinkedHashMap;
import java.util.Map;

/** 逐事件写 JSONL（可追溯），另存一次运行的完整 JSON 产物（含原始输出与检查结果）。 */
@Component
public class AcceptanceRunLogger {
  private final ObjectMapper mapper = new ObjectMapper();

  @Value("${app.acceptance.log-dir:./logs/acceptance-runs}")
  private String logDir;

  public void event(String runId, int attempt, String phase, Map<String, Object> fields) {
    Map<String, Object> row = new LinkedHashMap<>();
    row.put("runId", runId);
    row.put("ts", OffsetDateTime.now().toString());
    row.put("attempt", attempt);
    row.put("phase", phase);
    row.putAll(fields);
    try {
      append(Path.of(logDir, runId + ".jsonl"), mapper.writeValueAsString(row) + System.lineSeparator());
    } catch (Exception ignored) {
      // 日志失败不影响主流程；运行结果仍通过接口返回。
    }
  }

  public void artifact(String runId, Map<String, Object> artifact) {
    try {
      Path dir = Path.of(logDir);
      Files.createDirectories(dir);
      Files.writeString(dir.resolve(runId + ".json"),
          mapper.writerWithDefaultPrettyPrinter().writeValueAsString(artifact),
          StandardCharsets.UTF_8, StandardOpenOption.CREATE, StandardOpenOption.TRUNCATE_EXISTING);
    } catch (Exception ignored) {
    }
  }

  private void append(Path file, String line) throws Exception {
    Files.createDirectories(file.getParent());
    Files.writeString(file, line, StandardCharsets.UTF_8,
        StandardOpenOption.CREATE, StandardOpenOption.APPEND);
  }
}