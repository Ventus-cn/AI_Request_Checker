package com.example.ambiguity.integration;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

import java.util.concurrent.Executor;
import java.util.concurrent.ThreadPoolExecutor;

/** 验收标准任务专用线程池：与 Web 请求线程隔离，队列满时返回可读错误而不是无限堆积。 */
@Configuration
public class AcceptanceTaskConfig {
  @Bean(name = "acceptanceTaskExecutor")
  public Executor acceptanceTaskExecutor(IntegrationProperties props) {
    ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
    executor.setCorePoolSize(props.getExecutorCore());
    executor.setMaxPoolSize(props.getExecutorMax());
    executor.setQueueCapacity(props.getQueueCapacity());
    executor.setThreadNamePrefix("acceptance-task-");
    executor.setRejectedExecutionHandler(new ThreadPoolExecutor.AbortPolicy());
    executor.initialize();
    return executor;
  }
}