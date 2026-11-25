package com.example.ambiguity.integration;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/** 集成层的线程池、任务保留期与清理间隔，集中在 application.yml 的 app.integration 段。 */
@Component
@ConfigurationProperties(prefix = "app.integration")
public class IntegrationProperties {
  private boolean enabled = true;
  private int executorCore = 2;
  private int executorMax = 4;
  private int queueCapacity = 20;
  private int retentionDays = 30;
  private long cleanupIntervalMs = 3_600_000;

  public boolean isEnabled() { return enabled; }
  public void setEnabled(boolean enabled) { this.enabled = enabled; }
  public int getExecutorCore() { return executorCore; }
  public void setExecutorCore(int executorCore) { this.executorCore = executorCore; }
  public int getExecutorMax() { return executorMax; }
  public void setExecutorMax(int executorMax) { this.executorMax = executorMax; }
  public int getQueueCapacity() { return queueCapacity; }
  public void setQueueCapacity(int queueCapacity) { this.queueCapacity = queueCapacity; }
  public int getRetentionDays() { return retentionDays; }
  public void setRetentionDays(int retentionDays) { this.retentionDays = retentionDays; }
  public long getCleanupIntervalMs() { return cleanupIntervalMs; }
  public void setCleanupIntervalMs(long cleanupIntervalMs) { this.cleanupIntervalMs = cleanupIntervalMs; }
}