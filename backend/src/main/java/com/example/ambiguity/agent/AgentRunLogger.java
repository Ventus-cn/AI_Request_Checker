package com.example.ambiguity.agent;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.time.OffsetDateTime;
import java.time.format.DateTimeFormatter;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.concurrent.ThreadLocalRandom;

/**
 * 运行时日志：每个任务一个 JSONL 文件，逐事件落盘。
 * 只记录工具名、参数摘要、结果摘要、错误类型、步数、耗时和最终状态；
 * 不记录 API Key、完整需求文本或完整外部响应。
 */
@Component
public class AgentRunLogger {
  private final ObjectMapper mapper = new ObjectMapper();
  @Value("${app.agent.log-dir:./logs/agent-runs}")
  private String directory;

  public String newTaskId() {
    String time = DateTimeFormatter.ofPattern("yyyyMMdd-HHmmss").format(java.time.LocalDateTime.now());
    return time + "-" + Integer.toHexString(ThreadLocalRandom.current().nextInt(0x100000, 0xFFFFFF));
  }

  public void write(String taskId, int step, String phase, String status, Map<String, Object> extra) {
    Map<String, Object> row = new LinkedHashMap<>();
    row.put("taskId", taskId);
    row.put("ts", OffsetDateTime.now().toString());
    row.put("step", step);
    row.put("phase", phase);
    row.put("status", status);
    if (extra != null) row.putAll(extra);
    try {
      Path dir = Path.of(directory);
      Files.createDirectories(dir);
      Files.writeString(dir.resolve(taskId + ".jsonl"), mapper.writeValueAsString(row) + System.lineSeparator(),
          StandardOpenOption.CREATE, StandardOpenOption.APPEND);
    } catch (Exception ignored) {
      // 日志失败不影响主流程；错误由服务端控制台兜底。
    }
  }

  public static String brief(Object value, int max) {
    String text = value == null ? "" : String.valueOf(value).replaceAll("\\s+", " ");
    return text.length() <= max ? text : text.substring(0, max) + "…";
  }

  public String logDir() {
    return directory;
  }
}