package com.example.ambiguity.service;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import java.util.*;

@Service
public class AiReviewService {
  private final ObjectMapper mapper = new ObjectMapper();
  private final RestClient client = RestClient.create();
  @Value("${app.ai-mode:mock}") private String mode;
  @Value("${app.qwen-api-key:}") private String apiKey;
  @Value("${app.qwen-model:qwen-plus}") private String model;
  @Value("${app.qwen-url:https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions}") private String url;

  public Map<String,Object> review(String text, String requestedMode) {
    if (text == null || text.isBlank()) throw new IllegalArgumentException("需求文本不能为空");
    if ("qwen".equalsIgnoreCase(mode) && apiKey != null && !apiKey.isBlank()) return callQwen(text, requestedMode);
    return mock(text);
  }

  private Map<String,Object> callQwen(String text, String reviewMode) {
    String system = "你是需求质量审查器，同时从产品经理、开发、测试、安全审查员角度工作。不要修改原文，不确定就标记需要确认。只输出合法 JSON，不要 markdown。固定结构：{summary:string,riskLevel:high|medium|low,counts:{high:number,medium:number,low:number},issues:[{id,type,severity,quote,location,explanation,missingConditions:string[],questions:string[],acceptanceCriteria:string[],relatedRoles:string[],reworkRisk:string}]}。type只能是 ambiguous_term,missing_boundary,conflict,permission,testability,security,operational；没有问题返回空数组。";
    Map<String,Object> payload = Map.of("model", model, "temperature", 0.2, "messages", List.of(Map.of("role","system","content",system), Map.of("role","user","content","审查模式："+reviewMode+"\n需求：\n"+text)));
    try {
      Map<?,?> result = client.post().uri(url).header("Authorization","Bearer "+apiKey).contentType(MediaType.APPLICATION_JSON).body(payload).retrieve().body(Map.class);
      Object content = ((Map<?,?>)((List<?>)result.get("choices")).get(0)).get("message");
      String raw = String.valueOf(((Map<?,?>)content).get("content")).replaceAll("^```json\\s*|\\s*```$", "").trim();
      return validate(mapper.readValue(raw, new TypeReference<Map<String,Object>>(){}));
    } catch (Exception e) { throw new IllegalStateException("千问 API 调用失败或返回格式不正确：" + e.getMessage()); }
  }

  private Map<String,Object> validate(Map<String,Object> report) {
    if (report == null || !(report.get("issues") instanceof List<?> rawIssues)) throw new IllegalStateException("AI 返回缺少 issues 数组");
    List<Map<String,Object>> normalized = new ArrayList<>();
    int index = 1;
    for (Object raw : rawIssues) {
      if (!(raw instanceof Map<?,?> source)) continue;
      Map<String,Object> issue = new LinkedHashMap<>();
      source.forEach((key, value) -> issue.put(String.valueOf(key), value));
      issue.putIfAbsent("id", "AI-" + index++);
      issue.putIfAbsent("type", "testability"); issue.putIfAbsent("severity", "medium");
      issue.putIfAbsent("quote", "未提供原文引用"); issue.putIfAbsent("location", "未标注位置");
      issue.putIfAbsent("explanation", "AI 未提供详细解释"); issue.putIfAbsent("reworkRisk", "需要确认");
      for (String field : List.of("missingConditions", "questions", "acceptanceCriteria", "relatedRoles")) {
        if (!(issue.get(field) instanceof List<?>)) issue.put(field, new ArrayList<>());
      }
      normalized.add(issue);
    }
    report.put("issues", normalized);
    report.putIfAbsent("summary", "审查完成，请关注以下问题");
    report.putIfAbsent("riskLevel", normalized.isEmpty() ? "low" : "medium");
    report.putIfAbsent("counts", Map.of("high",0,"medium",0,"low",0));
    return report;
  }

  private Map<String,Object> mock(String text) {
    List<Map<String,Object>> issues = new ArrayList<>();
    String quote = text.length() > 70 ? text.substring(0,70) + "…" : text;
    if (text.matches(".*(尽快|适当|合理|简单|方便|等|等等|高性能|友好).*")) issues.add(issue("AMB-001","ambiguous_term","medium",quote,"第 1 段","存在可有多种解释的模糊表达，团队可能按不同标准实现。",List.of("明确量化阈值、时间范围或完成定义"),List.of("这里的具体阈值和截止时间是什么？"),List.of("给定明确输入时，系统在约定时间内返回可观测结果"),List.of("产品经理","开发","测试"),"中：容易引发反复沟通和返工。"));
    if (!text.matches(".*(登录|用户|权限|管理员|角色).*")) issues.add(issue("PER-001","permission","high",quote,"全文","需求没有说明用户身份、角色和数据访问边界，权限实现无法验收。",List.of("角色清单、登录状态、资源归属、读写权限"),List.of("谁可以查看、编辑和删除数据？未登录用户如何处理？"),List.of("不同角色访问受限资源时返回明确的 401/403，并有覆盖测试"),List.of("产品经理","开发","安全审查员"),"高：后期补权限通常需要修改数据模型和接口。"));
    if (!text.matches(".*(失败|异常|超时|错误|为空|不存在).*")) issues.add(issue("OPR-001","operational","medium",quote,"全文","没有定义异常、空数据和外部服务失败时的行为。",List.of("失败提示、重试策略、超时、空状态、数据恢复"),List.of("网络超时或服务不可用时用户看到什么？"),List.of("模拟超时后展示可理解错误，且不会产生重复记录"),List.of("开发","测试","运营"),"中：异常流程通常在联调阶段暴露。"));
    if (text.length() < 120) issues.add(issue("TST-001","testability","low",quote,"全文","需求较短，缺乏可验证的输入、输出和验收口径。",List.of("输入样例、预期输出、性能和边界指标"),List.of("如何判断功能已经完成？"),List.of("至少提供 3 个正常样例和 3 个边界样例，逐项核对预期结果"),List.of("测试","产品经理"),"低：可能导致验收争议。"));
    long high=issues.stream().filter(i->"high".equals(i.get("severity"))).count(), medium=issues.stream().filter(i->"medium".equals(i.get("severity"))).count();
    Map<String,Object> result = new LinkedHashMap<>(); result.put("summary", issues.isEmpty()?"暂未发现明显风险，请继续补充可验证的业务规则。":"发现 "+issues.size()+" 个可能影响实现、测试或验收的风险点，建议先确认高风险项。"); result.put("riskLevel", high>0?"high":medium>0?"medium":"low"); result.put("counts", Map.of("high",high,"medium",medium,"low",issues.size()-high-medium)); result.put("issues",issues); return result;
  }
  private Map<String,Object> issue(String id,String type,String sev,String quote,String loc,String exp,List<String> miss,List<String> qs,List<String> ac,List<String> roles,String risk){ Map<String,Object> m=new LinkedHashMap<>(); m.put("id",id);m.put("type",type);m.put("severity",sev);m.put("quote",quote);m.put("location",loc);m.put("explanation",exp);m.put("missingConditions",miss);m.put("questions",qs);m.put("acceptanceCriteria",ac);m.put("relatedRoles",roles);m.put("reworkRisk",risk);return m; }
}
