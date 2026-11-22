package com.example.ambiguity.acceptance;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

/** 验收标准生成的全部可调参数集中在这里，对应 application.yml 的 app.acceptance 段。 */
@Component
@ConfigurationProperties(prefix = "app.acceptance")
public class AcceptanceProperties {
  private boolean enabled = true;
  private String model = "qwen-plus";
  private double temperature = 0.2;
  private int maxTokens = 2000;
  private long timeoutMs = 60000;
  private int maxAttempts = 3;
  private int maxInputChars = 3000;
  private String logDir = "./logs/acceptance-runs";

  public boolean isEnabled() { return enabled; }
  public void setEnabled(boolean enabled) { this.enabled = enabled; }
  public String getModel() { return model; }
  public void setModel(String model) { this.model = model; }
  public double getTemperature() { return temperature; }
  public void setTemperature(double temperature) { this.temperature = temperature; }
  public int getMaxTokens() { return maxTokens; }
  public void setMaxTokens(int maxTokens) { this.maxTokens = maxTokens; }
  public long getTimeoutMs() { return timeoutMs; }
  public void setTimeoutMs(long timeoutMs) { this.timeoutMs = timeoutMs; }
  public int getMaxAttempts() { return maxAttempts; }
  public void setMaxAttempts(int maxAttempts) { this.maxAttempts = maxAttempts; }
  public int getMaxInputChars() { return maxInputChars; }
  public void setMaxInputChars(int maxInputChars) { this.maxInputChars = maxInputChars; }
  public String getLogDir() { return logDir; }
  public void setLogDir(String logDir) { this.logDir = logDir; }
}