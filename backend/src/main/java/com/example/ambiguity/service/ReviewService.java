package com.example.ambiguity.service;

import com.example.ambiguity.dto.ReviewDtos.*;
import com.example.ambiguity.model.Review;
import com.example.ambiguity.repository.ReviewRepository;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Service;
import java.util.*;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Service
public class ReviewService {
  private static final Logger log = LoggerFactory.getLogger(ReviewService.class);
  private final ReviewRepository repo; private final AiReviewService ai; private final ObjectMapper mapper = new ObjectMapper();
  public ReviewService(ReviewRepository repo, AiReviewService ai){this.repo=repo;this.ai=ai;}
  private static final Set<String> MODES = Set.of("全面审查", "可测试性", "安全与权限");
  public ReviewResponse create(ReviewRequest req){
    if (req == null || req.text() == null || req.text().isBlank()) throw new IllegalArgumentException("需求文本不能为空");
    if (req.text().length() > 20000) throw new IllegalArgumentException("需求文本不能超过 20000 个字符");
    String mode=req.mode()==null||req.mode().isBlank()?"全面审查":req.mode();
    if (!MODES.contains(mode)) throw new IllegalArgumentException("不支持的审查模式");
    String promptVersion = normalizePromptVersion(req.promptVersion());
    log.info("review.create mode={} promptVersion={} chars={}", mode, promptVersion, req.text().length());
    Map<String,Object> report=ai.review(req.text(),mode,promptVersion);
    if(req.document()!=null) report.put("document", mapper.convertValue(req.document(), Map.class));
    return save(req.text(),mode,report);
  }
  private ReviewResponse save(String text,String mode,Map<String,Object> report){ try {Review r=new Review(text,mode,mapper.writeValueAsString(report)); Review saved=repo.save(r); log.info("review.saved id={}", saved.getId()); return response(saved);} catch(Exception e){log.error("review.save_failed",e); throw new IllegalStateException("保存审查记录失败");} }
  public ReviewResponse follow(UUID id,String q){
    if (q == null || q.isBlank()) throw new IllegalArgumentException("追问内容不能为空");
    if (q.length() > 2000) throw new IllegalArgumentException("追问不能超过 2000 个字符");
    Review r=repo.findById(id).orElseThrow(()->new NoSuchElementException("审查记录不存在"));
    Map<String,Object> previous = readReport(r.getReportJson());
    String promptVersion = normalizePromptVersion(String.valueOf(previous.getOrDefault("promptVersion", "revised")));
    Map<String,Object> report=ai.review(r.getText()+"\n\n用户追问："+q,r.getMode(),promptVersion);
    if(previous.containsKey("document")) report.put("document",previous.get("document"));
    try {List<Map<String,Object>> versions=mapper.readValue(r.getVersionsJson(),new TypeReference<>(){}); versions.add(mapper.readValue(r.getReportJson(),new TypeReference<>(){})); r.setVersionsJson(mapper.writeValueAsString(versions)); r.setReportJson(mapper.writeValueAsString(report)); Review saved=repo.save(r); log.info("review.follow_up id={} versions={}", id, versions.size()); return response(saved);}catch(Exception e){log.error("review.follow_up_failed id={}",id,e); throw new IllegalStateException("保存追问版本失败");}}
  public List<HistoryItem> history(){ return repo.findAll().stream().sorted(Comparator.comparing(Review::getCreatedAt).reversed()).map(r->{try{Map<String,Object> p=mapper.readValue(r.getReportJson(),new TypeReference<>(){});return new HistoryItem(r.getId().toString(),r.getCreatedAt().toString(),r.getText().replaceAll("\\s+"," ").substring(0,Math.min(90,r.getText().replaceAll("\\s+"," ").length())),String.valueOf(p.getOrDefault("riskLevel","low")),(Map<String,Object>)p.getOrDefault("counts",Map.of()));}catch(Exception e){return new HistoryItem(r.getId().toString(),r.getCreatedAt().toString(),r.getText(),"unknown",Map.of());}}).collect(Collectors.toList()); }
  public ReviewResponse get(UUID id){return response(repo.findById(id).orElseThrow(()->new NoSuchElementException("审查记录不存在")));}
  public void delete(UUID id){ if (!repo.existsById(id)) throw new NoSuchElementException("审查记录不存在"); repo.deleteById(id); log.info("review.deleted id={}",id); }
  private String normalizePromptVersion(String value){ if ("original".equalsIgnoreCase(value) || "原Prompt".equals(value)) return "original"; return "revised"; }
  private Map<String,Object> readReport(String json){ try{return mapper.readValue(json,new TypeReference<>(){});}catch(Exception e){throw new IllegalStateException("审查报告解析失败");} }
  private ReviewResponse response(Review r){try{return new ReviewResponse(r.getId().toString(),r.getText(),r.getMode(),r.getCreatedAt().toString(),mapper.readValue(r.getReportJson(),new TypeReference<>(){}),mapper.readValue(r.getVersionsJson(),new TypeReference<>(){}));}catch(Exception e){throw new IllegalStateException("审查报告解析失败");}}
}
