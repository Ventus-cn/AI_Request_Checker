package com.example.ambiguity.acceptance;

import java.util.function.BooleanSupplier;
import java.util.function.Consumer;

/**
 * 一次运行的上下文：任务编号、取消信号与阶段回报。
 * 同步接口使用 {@link #none()}，集成任务由后台线程传入真实实现。
 */
public record AcceptanceContext(String taskId, BooleanSupplier cancelled, Consumer<String> phase) {

  public static AcceptanceContext none() {
    return new AcceptanceContext(null, () -> false, value -> { });
  }

  public boolean isCancelled() {
    return cancelled != null && cancelled.getAsBoolean();
  }

  public void reportPhase(String value) {
    if (phase != null && value != null) phase.accept(value);
  }
}