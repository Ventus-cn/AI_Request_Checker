package com.example.ambiguity.agent;

import com.example.ambiguity.agent.dto.AgentDtos.StepView;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * 一次 Agent 运行的状态：上下文消息、步数、预算、已执行的工具轨迹。
 * 确认挂起时该对象会被暂存，用户同意后从断点继续。
 */
public class AgentRun {
  public final String taskId;
  public final String question;
  public final List<Map<String, Object>> messages = new ArrayList<>();
  public final List<StepView> steps = new ArrayList<>();
  public final long startedAt = System.currentTimeMillis();
  public long deadline;
  public int step;
  public int answerRetries;
  public int toolCallsThisStep;
  public Map<String, Object> lastStats;
  public int lastKnowledgeCount;
  public boolean deleteExecuted;
  public String pendingTool;
  public String pendingArgs;

  public AgentRun(String taskId, String question, long deadline) {
    this.taskId = taskId;
    this.question = question;
    this.deadline = deadline;
  }

  public void addMessage(String role, String content) {
    Map<String, Object> message = new LinkedHashMap<>();
    message.put("role", role);
    message.put("content", content);
    messages.add(message);
  }

  public boolean expired() {
    return System.currentTimeMillis() > deadline;
  }
}