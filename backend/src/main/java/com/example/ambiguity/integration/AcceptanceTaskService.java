package com.example.ambiguity.integration;

import com.example.ambiguity.acceptance.AcceptanceChecker;
import com.example.ambiguity.acceptance.AcceptanceContext;
import com.example.ambiguity.acceptance.AcceptanceProperties;
import com.example.ambiguity.acceptance.AcceptanceService;
import com.example.ambiguity.acceptance.dto.AcceptanceDtos.*;
import com.example.ambiguity.integration.TaskDtos.*;
import com.example.ambiguity.model.Review;
import com.example.ambiguity.service.ReviewService;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.nio.file.Files;
import java.nio.file.Path;
import java.security.SecureRandom;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.Executor;
import java.util.concurrent.RejectedExecutionException;
import java.util.stream.Stream;

/**
 * 验收标准生成任务的状态机与持久化。
 *
 * <p>状态：QUEUED → RUNNING → SUCCEEDED / FAILED / CHECK_FAILED / REFUSED / CANCELLED。
 * 终态只读；重新生成、规则降级、转人工都会创建新任务并记录 retryOf，保证每次输出可追溯。</p>
 *
 * <p>取消是协作式的：排队任务立即取消；运行中的任务置 cancelRequested，后台线程在阶段边界停止，
 * 已在途的模型调用无法中断，但其返回结果会被丢弃（迟到结果不覆盖终态）。</p>
 */
@Service
public class AcceptanceTaskService {
  private static final Logger log = LoggerFactory.getLogger(AcceptanceTaskService.class);
  private static final DateTimeFormatter ID_TIME = DateTimeFormatter.ofPattern("yyyyMMdd-HHmmss");
  private static final DateTimeFormatter DISPLAY = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")
      .withZone(ZoneId.systemDefault());
  private static final SecureRandom RANDOM = new SecureRandom();
  private static final Set<String> MODES = Set.of("model", "rule", "manual");
  private static final Set<String> PRIORITIES = Set.of("must", "should", "could");
  private static final Set<String> TEST_KINDS = Set.of("normal", "boundary", "exception");
  private static final Set<String> KINDS = Set.of("normal", "insufficient", "out_of_scope");

  private final AcceptanceTaskRepository repo;
  private final AcceptanceService acceptance;
  private final AcceptanceChecker checker;
  private final ReviewService reviews;
  private final AcceptanceProperties acceptanceProps;
  private final IntegrationProperties props;
  private final Executor executor;
  private final ObjectMapper mapper = new ObjectMapper();
  /** 单实例应用内串行化状态迁移，避免“取消”与“完成”互相覆盖。 */
  private final Object lock = new Object();

  @Value("${app.acceptance.log-dir:./logs/acceptance-runs}")
  private String logDir;

  public AcceptanceTaskService(AcceptanceTaskRepository repo,
                               AcceptanceService acceptance,
                               AcceptanceChecker checker,
                               ReviewService reviews,
                               AcceptanceProperties acceptanceProps,
                               IntegrationProperties props,
                               @Qualifier("acceptanceTaskExecutor") Executor executor) {
    this.repo = repo;
    this.acceptance = acceptance;
    this.checker = checker;
    this.reviews = reviews;
    this.acceptanceProps = acceptanceProps;
    this.props = props;
    this.executor = executor;
  }

  // ============================ 提交与执行 ============================

  public TaskView submit(SubmitRequest request) {
    String promptVersion = "original".equalsIgnoreCase(request == null ? null : request.promptVersion())
        ? "original" : "revised";
    String mode = normalizeMode(request == null ? null : request.mode());
    String reviewId = blank(request == null ? null : request.reviewId()) ? null : request.reviewId().trim();
    String text;
    String sourcesJson = "[]";
    if (reviewId != null) {
      Review review;
      try {
        review = reviews.find(UUID.fromString(reviewId));
      } catch (IllegalArgumentException e) {
        throw new ApiException(400, "INPUT_INVALID", "reviewId 格式不正确", false, List.of());
      }
      text = review.getText();
      sourcesJson = sourcesFrom(review.getReportJson());
    } else {
      text = request == null ? null : request.text();
    }
    validateInput(text, mode);
    String dedupeKey = dedupeKey(reviewId, text, promptVersion, mode);
    synchronized (lock) {
      Optional<AcceptanceTask> active = repo
          .findFirstByDedupeKeyAndStatusInOrderByCreatedAtDesc(dedupeKey, List.of(TaskStatus.QUEUED, TaskStatus.RUNNING));
      if (active.isPresent()) {
        log.info("acceptance.task.duplicate key={} existing={} status={}", dedupeKey,
            active.get().getId(), active.get().getStatus());
        return view(active.get()).withDuplicate(true);
      }
    }
    return enqueue(reviewId, text, promptVersion, mode, null, sourcesJson, false);
  }

  public TaskView retry(String taskId) {
    AcceptanceTask origin = require(taskId);
    if (!TaskStatus.terminal(origin.getStatus())) {
      throw new ApiException(409, "TASK_ACTIVE", "任务仍在处理中，请先取消或等待完成", true,
          List.of("取消任务", "等待完成"));
    }
    String mode = "rule".equals(origin.getMode()) ? "rule" : "model";
    return enqueue(origin.getReviewId(), origin.getInputText(), origin.getPromptVersion(), mode,
        origin.getId(), origin.getSourcesJson(), false);
  }

  /** 规则降级：不调用模型，用规则流程给出可编辑的占位结果，并在任务上明确标注 degraded。 */
  public TaskView fallback(String taskId) {
    AcceptanceTask origin = require(taskId);
    if (!TaskStatus.terminal(origin.getStatus())) {
      throw new ApiException(409, "TASK_ACTIVE", "任务仍在处理中，请先取消或等待完成", true,
          List.of("取消任务", "等待完成"));
    }
    TaskView view = enqueue(origin.getReviewId(), origin.getInputText(), origin.getPromptVersion(),
        "rule", origin.getId(), origin.getSourcesJson(), true);
    synchronized (lock) {
      AcceptanceTask task = require(view.taskId());
      task.setDegraded(true);
      task.setDegradeReason("模型不可用，改用规则流程生成（非 AI 结果，需人工补全）");
      task.setPhase("规则降级完成");
      repo.save(task);
      return view(task);
    }
  }

  /** 转人工：创建 manual 任务，结果为空模板，用户可直接编辑后保存。 */
  public TaskView handoff(String taskId) {
    AcceptanceTask origin = require(taskId);
    if (!TaskStatus.terminal(origin.getStatus())) {
      throw new ApiException(409, "TASK_ACTIVE", "任务仍在处理中，请先取消或等待完成", true,
          List.of("取消任务", "等待完成"));
    }
    AcceptanceTask manual = new AcceptanceTask(nextId(), origin.getReviewId(), origin.getInputText(),
        origin.getPromptVersion(), "manual", "manual", "manual:" + nextId(), origin.getId());
    manual.setSourcesJson(origin.getSourcesJson());
    manual.setStatus(TaskStatus.SUCCEEDED);
    manual.setPhase("等待人工填写");
    manual.setDegraded(true);
    manual.setDegradeReason("已转人工处理：AI 结果仅供参考，最终由人填写并确认");
    manual.setResultJson(json(new Report("normal", "人工填写验收标准：请根据原文补齐 Given/When/Then 与测试样例。",
        List.of(), List.of(), List.of(), List.of("人工填写，未经模型生成，不参与自动检查。"))));
    manual.setFinishedAt(Instant.now());
    synchronized (lock) {
      repo.save(manual);
      origin.setDecision("MANUAL");
      repo.save(origin);
    }
    log.info("acceptance.task.handoff origin={} manual={}", taskId, manual.getId());
    return view(manual);
  }

  private TaskView enqueue(String reviewId, String text, String promptVersion, String mode,
                           String retryOf, String sourcesJson, boolean synchronous) {
    AcceptanceTask task = new AcceptanceTask(nextId(), reviewId, text, promptVersion, mode,
        "rule".equals(mode) ? "rule-baseline" : ("manual".equals(mode) ? "manual" : acceptance.modelName()),
        dedupeKey(reviewId, text, promptVersion, mode), retryOf);
    task.setSourcesJson(sourcesJson == null ? "[]" : sourcesJson);
    synchronized (lock) {
      repo.save(task);
    }
    log.info("acceptance.task.created id={} review={} mode={} version={} retryOf={}",
        task.getId(), reviewId, mode, promptVersion, retryOf);
    if ("manual".equals(mode)) return view(task);
    if (synchronous) {
      execute(task.getId());
    } else {
      try {
        executor.execute(() -> execute(task.getId()));
      } catch (RejectedExecutionException e) {
        synchronized (lock) {
          AcceptanceTask failed = require(task.getId());
          failed.setStatus(TaskStatus.FAILED);
          failed.setPhase("未开始");
          failed.setErrorCode("QUEUE_FULL");
          failed.setErrorMessage("排队任务过多，本次未执行");
          failed.setFinishedAt(Instant.now());
          repo.save(failed);
        }
        throw new ApiException(503, "QUEUE_FULL", "排队任务过多，请稍后重试", true,
            List.of("稍后重试", "改用规则流程"));
      }
    }
    return view(require(task.getId()));
  }

  private void execute(String taskId) {
    try {
      AcceptanceTask task;
      synchronized (lock) {
        task = repo.findById(taskId).orElse(null);
        if (task == null) return;
        if (task.isCancelRequested() || TaskStatus.CANCELLED.equals(task.getStatus())) {
          cancelNow(task, "任务在排队阶段被取消");
          return;
        }
        task.setStatus(TaskStatus.RUNNING);
        task.setStartedAt(Instant.now());
        task.setPhase("调用模型");
        task = repo.save(task);
      }
      long started = System.currentTimeMillis();
      RunResponse response;
      try {
        response = acceptance.run(new RunRequest(task.getInputText(), task.getPromptVersion(), task.getMode()),
            new AcceptanceContext(taskId, () -> isCancelRequested(taskId), phase -> updatePhase(taskId, phase)));
      } catch (Exception e) {
        log.error("acceptance.task.failed id={}", taskId, e);
        finishWithFailure(taskId, e, System.currentTimeMillis() - started);
        return;
      }
      finish(taskId, response, System.currentTimeMillis() - started);
    } catch (Exception e) {
      // 后台线程的最后一个兜底：任何意外都要把任务置为终态，避免前端一直“处理中”。
      log.error("acceptance.task.unexpected id={}", taskId, e);
      finishWithFailure(taskId, e, 0);
    }
  }

  private void finish(String taskId, RunResponse response, long elapsedMs) {
    synchronized (lock) {
      AcceptanceTask task = repo.findById(taskId).orElse(null);
      if (task == null) return;
      boolean cancelled = task.isCancelRequested() || TaskStatus.CANCELLED.equals(task.getStatus())
          || (response != null && "CANCELLED".equals(response.status()));
      if (cancelled) {
        task.setStatus(TaskStatus.CANCELLED);
        task.setPhase("已取消");
        task.setFinishedAt(Instant.now());
        task.setDurationMs(elapsedMs);
        task.setResultJson(null);
        task.setChecksJson(null);
        task.setErrorCode("CANCELLED");
        task.setErrorMessage("任务已取消，返回结果已丢弃");
        repo.save(task);
        log.info("acceptance.task.late_result_discarded id={} lateStatus={} hadReport={}",
            taskId, response == null ? null : response.status(),
            response != null && response.report() != null);
        return;
      }
      if (response == null) {
        task.setStatus(TaskStatus.FAILED);
        task.setErrorCode("MODEL_ERROR");
        task.setErrorMessage("生成失败：未获得模型结果");
        task.setPhase("生成失败");
        task.setFinishedAt(Instant.now());
        repo.save(task);
        return;
      }
      task.setStatus(switch (response.status()) {
        case "SUCCESS" -> TaskStatus.SUCCEEDED;
        case "REFUSED" -> TaskStatus.REFUSED;
        case "CHECK_FAILED" -> TaskStatus.CHECK_FAILED;
        default -> TaskStatus.FAILED;
      });
      task.setModel(response.model());
      task.setAttempts(response.attempts());
      task.setDurationMs(response.durationMs() > 0 ? response.durationMs() : elapsedMs);
      task.setPromptTokens(response.usage() == null ? 0 : response.usage().promptTokens());
      task.setCompletionTokens(response.usage() == null ? 0 : response.usage().completionTokens());
      task.setResultJson(response.report() == null ? null : json(response.report()));
      task.setChecksJson(response.checks() == null ? null : json(response.checks()));
      task.setErrorCode(response.errorCode());
      task.setErrorMessage(response.error());
      task.setPhase(switch (task.getStatus()) {
        case TaskStatus.SUCCEEDED -> "生成完成";
        case TaskStatus.REFUSED -> "已拒绝";
        case TaskStatus.CHECK_FAILED -> "校验未通过";
        default -> "生成失败";
      });
      task.setFinishedAt(Instant.now());
      repo.save(task);
      log.info("acceptance.task.finished id={} status={} attempts={} durationMs={}",
          taskId, task.getStatus(), task.getAttempts(), task.getDurationMs());
    }
  }

  private void finishWithFailure(String taskId, Exception e, long elapsedMs) {
    synchronized (lock) {
      AcceptanceTask task = repo.findById(taskId).orElse(null);
      if (task == null) return;
      if (TaskStatus.CANCELLED.equals(task.getStatus()) || task.isCancelRequested()) {
        cancelNow(task, "任务已取消");
        return;
      }
      String message = e.getMessage() == null ? e.getClass().getSimpleName() : e.getMessage();
      task.setStatus(TaskStatus.FAILED);
      task.setPhase("生成失败");
      task.setErrorCode(message.toLowerCase(Locale.ROOT).contains("超时") ? "MODEL_TIMEOUT" : "MODEL_ERROR");
      task.setErrorMessage(message.length() > 300 ? message.substring(0, 300) : message);
      task.setDurationMs(elapsedMs);
      task.setFinishedAt(Instant.now());
      repo.save(task);
    }
  }

  private boolean isCancelRequested(String taskId) {
    return repo.findById(taskId).map(AcceptanceTask::isCancelRequested).orElse(true);
  }

  private void updatePhase(String taskId, String phase) {
    synchronized (lock) {
      AcceptanceTask task = repo.findById(taskId).orElse(null);
      // 已请求取消时保留“正在取消”提示，避免后续阶段把用户可见状态覆盖掉。
      if (task == null || !TaskStatus.RUNNING.equals(task.getStatus()) || task.isCancelRequested()) return;
      task.setPhase(phase);
      repo.save(task);
    }
  }

  // ============================ 取消 / 编辑 / 保存 ============================

  public TaskView cancel(String taskId) {
    synchronized (lock) {
      AcceptanceTask task = require(taskId);
      if (TaskStatus.terminal(task.getStatus())) {
        throw new ApiException(409, "TASK_FINISHED",
            "任务已结束（" + TaskStatus.label(task.getStatus()) + "），无法取消", false,
            List.of("查看结果", "重新发起"));
      }
      task.setCancelRequested(true);
      if (TaskStatus.QUEUED.equals(task.getStatus())) {
        cancelNow(task, "任务在排队阶段被取消");
      } else {
        task.setPhase("正在取消（等待当前调用返回）");
        repo.save(task);
        log.info("acceptance.task.cancel_requested id={}", taskId);
      }
      return view(task);
    }
  }

  private void cancelNow(AcceptanceTask task, String reason) {
    task.setStatus(TaskStatus.CANCELLED);
    task.setPhase("已取消");
    task.setFinishedAt(Instant.now());
    task.setResultJson(null);
    task.setChecksJson(null);
    task.setErrorCode("CANCELLED");
    task.setErrorMessage(reason + "，未产生可用结果");
    repo.save(task);
    log.info("acceptance.task.cancelled id={} reason={}", task.getId(), reason);
  }

  /** 人工修改结果：重新做程序检查并保留修改痕迹，状态不因人工编辑而被“洗白”。 */
  public TaskView edit(String taskId, EditRequest request) {
    Report report = normalizeReport(request == null ? null : request.report());
    synchronized (lock) {
      AcceptanceTask task = require(taskId);
      if (!TaskStatus.SUCCEEDED.equals(task.getStatus()) && !TaskStatus.CHECK_FAILED.equals(task.getStatus())) {
        throw new ApiException(409, "TASK_NOT_EDITABLE",
            "当前状态（" + TaskStatus.label(task.getStatus()) + "）不能编辑", false,
            List.of("重新生成", "转人工"));
      }
      Checks checks = checker.check(task.getInputText(), report);
      task.setResultJson(json(report));
      task.setChecksJson(json(checks));
      task.setEdited(true);
      task.setPhase("已人工修改");
      if (TaskStatus.CHECK_FAILED.equals(task.getStatus()) && checks.acceptable()) {
        task.setStatus(TaskStatus.SUCCEEDED);
        task.setErrorCode(null);
        task.setErrorMessage(null);
        task.setPhase("人工修改后通过检查");
      }
      repo.save(task);
      log.info("acceptance.task.edited id={} acceptable={}", taskId, checks.acceptable());
      return view(task);
    }
  }

  /** 保存到审查档案：幂等，重复保存返回同一结果，不重复写入。 */
  public ApplyResponse apply(String taskId) {
    synchronized (lock) {
      AcceptanceTask task = require(taskId);
      if (task.isSaved()) {
        return new ApplyResponse(view(task), task.getReviewId(), taskId);
      }
      if (!TaskStatus.SUCCEEDED.equals(task.getStatus())) {
        throw new ApiException(409, "TASK_NOT_READY",
            "只有“已生成”的结果才能保存到档案，当前为" + TaskStatus.label(task.getStatus()), false,
            List.of("重试", "转人工"));
      }
      if (blank(task.getReviewId())) {
        throw new ApiException(400, "NO_REVIEW", "该任务不是从审查档案发起的，无法保存到档案", false,
            List.of("在档案页重新发起"));
      }
      Map<String, Object> acceptance = new LinkedHashMap<>();
      acceptance.put("taskId", taskId);
      acceptance.put("model", task.getModel());
      acceptance.put("mode", task.getMode());
      acceptance.put("degraded", task.isDegraded());
      acceptance.put("edited", task.isEdited());
      acceptance.put("attempts", task.getAttempts());
      acceptance.put("durationMs", task.getDurationMs());
      acceptance.put("report", read(task.getResultJson(), Map.class));
      acceptance.put("checks", read(task.getChecksJson(), Map.class));
      Map<String, Object> payload = new LinkedHashMap<>();
      payload.put("saved", true);
      payload.put("savedAt", DISPLAY.format(Instant.now()));
      payload.put("acceptance", acceptance);
      reviews.saveAcceptance(UUID.fromString(task.getReviewId()), json(payload));
      task.setAppliedAt(Instant.now());
      task.setDecision("ACCEPTED");
      repo.save(task);
      log.info("acceptance.task.applied id={} review={}", taskId, task.getReviewId());
      return new ApplyResponse(view(task), task.getReviewId(), taskId);
    }
  }

  public TaskView discard(String taskId) {
    synchronized (lock) {
      AcceptanceTask task = require(taskId);
      if (task.isSaved()) {
        throw new ApiException(409, "ALREADY_SAVED", "结果已保存到档案，需先在档案中清除后再放弃", false,
            List.of("查看档案"));
      }
      task.setDecision("DISCARDED");
      task.setPhase("已放弃结果");
      repo.save(task);
      return view(task);
    }
  }

  // ============================ 查询与清理 ============================

  public TaskView get(String taskId) {
    return view(require(taskId));
  }

  public List<TaskView> listByReview(String reviewId) {
    if (blank(reviewId)) {
      throw new ApiException(400, "INPUT_INVALID", "reviewId 不能为空", false, List.of());
    }
    return repo.findTop20ByReviewIdOrderByCreatedAtDesc(reviewId).stream().map(this::view).toList();
  }

  /** 已完成的旧任务按保留期清理；进行中的任务不删除。 */
  @Scheduled(fixedDelayString = "${app.integration.cleanup-interval-ms:3600000}")
  public void cleanup() {
    try {
      Instant before = Instant.now().minusSeconds(props.getRetentionDays() * 86_400L);
      List<AcceptanceTask> stale = repo.findByCreatedAtBeforeAndStatusIn(before,
          List.of(TaskStatus.SUCCEEDED, TaskStatus.FAILED, TaskStatus.CHECK_FAILED,
              TaskStatus.REFUSED, TaskStatus.CANCELLED));
      if (!stale.isEmpty()) {
        repo.deleteAll(stale);
        log.info("acceptance.task.cleanup removed={} before={}", stale.size(), before);
      }
      cleanLogDir(before);
    } catch (Exception e) {
      log.warn("acceptance.task.cleanup_failed", e);
    }
  }

  private void cleanLogDir(Instant before) {
    Path dir = Path.of(logDir);
    if (!Files.isDirectory(dir)) return;
    try (Stream<Path> files = Files.list(dir)) {
      files.filter(Files::isRegularFile).forEach(path -> {
        try {
          if (Files.getLastModifiedTime(path).toInstant().isBefore(before)) Files.delete(path);
        } catch (Exception ignored) {
        }
      });
    } catch (Exception ignored) {
    }
  }

  // ============================ 视图与工具 ============================

  private TaskView view(AcceptanceTask task) {
    Report report = read(task.getResultJson(), Report.class);
    Checks checks = read(task.getChecksJson(), Checks.class);
    List<SourceRef> sources = readList(task.getSourcesJson());
    String errorCode = task.getErrorCode();
    return new TaskView(
        task.getId(), task.getReviewId(), task.getStatus(), TaskStatus.label(task.getStatus()),
        task.getPhase(), task.getPromptVersion(), task.getMode(), task.getModel(),
        task.isDegraded(), task.getDegradeReason(), errorCode, task.getErrorMessage(),
        retryable(task), false, task.getAttempts(), task.getDurationMs(),
        task.getPromptTokens(), task.getCompletionTokens(),
        format(task.getCreatedAt()), format(task.getStartedAt()), format(task.getFinishedAt()),
        task.isCancelRequested(), task.getDecision(), task.isEdited(), task.isSaved(),
        format(task.getAppliedAt()), task.getRetryOf(), report, checks, sources,
        actions(task));
  }

  private boolean retryable(AcceptanceTask task) {
    if (TaskStatus.FAILED.equals(task.getStatus())) {
      return !"MODEL_UNAVAILABLE".equals(task.getErrorCode());
    }
    return TaskStatus.CHECK_FAILED.equals(task.getStatus()) || TaskStatus.CANCELLED.equals(task.getStatus());
  }

  private List<String> actions(AcceptanceTask task) {
    return switch (task.getStatus()) {
      case TaskStatus.QUEUED, TaskStatus.RUNNING -> List.of("cancel");
      case TaskStatus.SUCCEEDED -> List.of("edit", "apply", "discard", "retry", "handoff");
      case TaskStatus.CHECK_FAILED -> List.of("edit", "retry", "fallback", "handoff");
      case TaskStatus.FAILED -> "MODEL_UNAVAILABLE".equals(task.getErrorCode())
          ? List.of("fallback", "handoff") : List.of("retry", "fallback", "handoff");
      case TaskStatus.REFUSED -> List.of("handoff", "retry");
      case TaskStatus.CANCELLED -> List.of("retry", "fallback", "handoff");
      default -> List.of();
    };
  }

  private String sourcesFrom(String reportJson) {
    Map<String, Object> report = read(reportJson, Map.class);
    if (report == null) return "[]";
    Object rag = report.get("rag");
    if (!(rag instanceof Map<?, ?> ragMap)) return "[]";
    Object chunks = ragMap.get("chunks");
    if (!(chunks instanceof List<?> list)) return "[]";
    List<SourceRef> refs = new ArrayList<>();
    for (Object item : list) {
      if (!(item instanceof Map<?, ?> chunk)) continue;
      refs.add(new SourceRef(
          string(chunk.get("id")),
          string(chunk.get("source")),
          string(chunk.get("title")),
          chunk.get("score") instanceof Number number ? number.doubleValue() : 0d,
          string(chunk.get("text"))));
    }
    return json(refs);
  }

  private String string(Object value) {
    return value == null ? "" : String.valueOf(value);
  }

  private void validateInput(String text, String mode) {
    if ("manual".equals(mode)) {
      if (blank(text)) throw new ApiException(400, "INPUT_INVALID", "需求文本不能为空", false, List.of());
      return;
    }
    if (blank(text)) {
      throw new ApiException(400, "INPUT_INVALID", "需求文本不能为空", false, List.of("输入需求原文"));
    }
    int max = acceptanceProps.getMaxInputChars();
    if (text.length() > max) {
      throw new ApiException(400, "INPUT_INVALID",
          "需求文本不能超过 " + max + " 个字符，当前 " + text.length() + " 个字符", false,
          List.of("缩短需求后重试"));
    }
  }

  private Report normalizeReport(Report report) {
    if (report == null) {
      throw new ApiException(400, "INPUT_INVALID", "缺少 report 字段", false, List.of());
    }
    String kind = KINDS.contains(report.requirementKind()) ? report.requirementKind() : "normal";
    String summary = blank(report.summary()) ? "人工填写验收标准" : report.summary();
    List<Criterion> criteria = report.acceptanceCriteria() == null ? List.of() : report.acceptanceCriteria();
    List<TestSample> samples = report.testSamples() == null ? List.of() : report.testSamples();
    List<String> questions = report.openQuestions() == null ? List.of() : report.openQuestions();
    List<String> limits = report.limits() == null ? List.of() : report.limits();
    if (criteria.size() > 20 || samples.size() > 30 || questions.size() > 20) {
      throw new ApiException(400, "INPUT_INVALID", "验收标准最多 20 条、测试样例 30 条、待确认问题 20 条", false, List.of());
    }
    for (Criterion ac : criteria) {
      if (blank(ac.id()) || blank(ac.title()) || blank(ac.given()) || blank(ac.when()) || blank(ac.then())) {
        throw new ApiException(400, "INPUT_INVALID", "每条验收标准都要有编号、标题、Given、When、Then", false, List.of());
      }
      if (!PRIORITIES.contains(ac.priority())) {
        throw new ApiException(400, "INPUT_INVALID", "priority 只能是 must/should/could", false, List.of());
      }
      if (tooLong(ac.title()) || tooLong(ac.given()) || tooLong(ac.when()) || tooLong(ac.then())
          || tooLong(ac.sourceQuote())) {
        throw new ApiException(400, "INPUT_INVALID", "单个字段不能超过 1000 个字符", false, List.of());
      }
    }
    for (TestSample ts : samples) {
      if (blank(ts.id()) || blank(ts.input()) || blank(ts.expected()) || !TEST_KINDS.contains(ts.kind())) {
        throw new ApiException(400, "INPUT_INVALID", "测试样例需要编号、类型（normal/boundary/exception）、输入和预期结果", false, List.of());
      }
    }
    return new Report(kind, summary, criteria, samples, questions, limits);
  }

  private boolean tooLong(String value) {
    return value != null && value.length() > 1000;
  }

  private String normalizeMode(String mode) {
    if (blank(mode)) return "model";
    String value = mode.trim().toLowerCase(Locale.ROOT);
    if (!MODES.contains(value)) {
      throw new ApiException(400, "INPUT_INVALID", "mode 只能是 model/rule/manual", false, List.of());
    }
    return value;
  }

  private AcceptanceTask require(String taskId) {
    if (blank(taskId)) throw new ApiException(400, "INPUT_INVALID", "taskId 不能为空", false, List.of());
    return repo.findById(taskId).orElseThrow(() -> new ApiException(404, "TASK_NOT_FOUND",
        "任务不存在或已过保留期（保留 " + props.getRetentionDays() + " 天），请重新发起", false,
        List.of("重新发起")));
  }

  private String dedupeKey(String reviewId, String text, String promptVersion, String mode) {
    String source = reviewId != null ? "review:" + reviewId : "text:" + Integer.toHexString(Objects.hashCode(text));
    return source + "#" + promptVersion + "#" + mode;
  }

  private String nextId() {
    return "AC" + Instant.now().atZone(ZoneId.systemDefault()).format(ID_TIME).replace("-", "") + "-" + hex(4);
  }

  private String hex(int length) {
    StringBuilder sb = new StringBuilder();
    for (int i = 0; i < length; i++) sb.append("0123456789abcdef".charAt(RANDOM.nextInt(16)));
    return sb.toString();
  }

  private String format(Instant instant) {
    return instant == null ? null : DISPLAY.format(instant);
  }

  private boolean blank(String value) {
    return value == null || value.isBlank();
  }

  private String json(Object value) {
    try {
      return mapper.writeValueAsString(value);
    } catch (Exception e) {
      throw new IllegalStateException("结果序列化失败", e);
    }
  }

  private <T> T read(String value, Class<T> type) {
    if (blank(value)) return null;
    try {
      return mapper.readValue(value, type);
    } catch (Exception e) {
      log.warn("acceptance.task.parse_failed type={}", type.getSimpleName());
      return null;
    }
  }

  private List<SourceRef> readList(String value) {
    if (blank(value)) return List.of();
    try {
      return mapper.readValue(value, new TypeReference<List<SourceRef>>() { });
    } catch (Exception e) {
      return List.of();
    }
  }
}