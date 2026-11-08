package com.example.ambiguity.agent;

import com.example.ambiguity.agent.dto.AgentDtos.RunResponse;
import org.springframework.stereotype.Service;

/**
 * 对外的 Agent 任务编排入口：启动运行、恢复确认。
 */
@Service
public class AgentService {
  private final AgentHarness harness;

  public AgentService(AgentHarness harness) {
    this.harness = harness;
  }

  public RunResponse start(String question) {
    return harness.start(question);
  }

  public RunResponse confirm(String taskId, boolean approved) {
    return harness.confirm(taskId, approved);
  }
}