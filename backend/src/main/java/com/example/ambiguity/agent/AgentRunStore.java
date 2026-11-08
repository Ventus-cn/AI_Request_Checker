package com.example.ambiguity.agent;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.NoSuchElementException;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 等待人工确认的运行暂存区（单机原型，内存实现）。
 * 用户拒绝或超过 TTL 未响应时任务失效，不执行任何写操作。
 */
@Component
public class AgentRunStore {
  private final Map<String, Pending> pending = new ConcurrentHashMap<>();
  @Value("${app.agent.confirm-ttl-ms:300000}")
  private long ttlMs;

  public record Pending(AgentRun run, String tool, String args, String callId, long createdAt) {
  }

  public void put(AgentRun run, String tool, String args, String callId) {
    pending.put(run.taskId, new Pending(run, tool, args, callId, System.currentTimeMillis()));
  }

  public Pending take(String taskId) {
    Pending item = pending.remove(taskId);
    if (item == null) throw new NoSuchElementException("任务不存在或确认已过期，请重新发起分析");
    if (System.currentTimeMillis() - item.createdAt() > ttlMs) {
      throw new NoSuchElementException("确认已过期，请重新发起分析");
    }
    return item;
  }
}