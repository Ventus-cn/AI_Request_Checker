package com.example.ambiguity.service;

import com.example.ambiguity.dto.ReviewDtos.*;
import com.example.ambiguity.model.Review;
import com.example.ambiguity.repository.ReviewRepository;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Service;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class ReviewService {
  private final ReviewRepository repo; private final AiReviewService ai; private final ObjectMapper mapper = new ObjectMapper();
  public ReviewService(ReviewRepository repo, AiReviewService ai){this.repo=repo;this.ai=ai;}
  public ReviewResponse create(ReviewRequest req){ String mode=req.mode()==null?"全面审查":req.mode(); Map<String,Object> report=ai.review(req.text(),mode); return save(req.text(),mode,report); }
  private ReviewResponse save(String text,String mode,Map<String,Object> report){ try {Review r=new Review(text,mode,mapper.writeValueAsString(report)); return response(repo.save(r));} catch(Exception e){throw new IllegalStateException("保存审查记录失败");} }
  public ReviewResponse follow(UUID id,String q){ Review r=repo.findById(id).orElseThrow(()->new NoSuchElementException("审查记录不存在")); Map<String,Object> report=ai.review(r.getText()+"\n\n用户追问："+q,r.getMode()); try {List<Map<String,Object>> versions=mapper.readValue(r.getVersionsJson(),new TypeReference<>(){}); versions.add(mapper.readValue(r.getReportJson(),new TypeReference<>(){})); r.setVersionsJson(mapper.writeValueAsString(versions)); r.setReportJson(mapper.writeValueAsString(report)); return response(repo.save(r));}catch(Exception e){throw new IllegalStateException("保存追问版本失败");}}
  public List<HistoryItem> history(){ return repo.findAll().stream().sorted(Comparator.comparing(Review::getCreatedAt).reversed()).map(r->{try{Map<String,Object> p=mapper.readValue(r.getReportJson(),new TypeReference<>(){});return new HistoryItem(r.getId().toString(),r.getCreatedAt().toString(),r.getText().replaceAll("\\s+"," ").substring(0,Math.min(90,r.getText().replaceAll("\\s+"," ").length())),String.valueOf(p.getOrDefault("riskLevel","low")),(Map<String,Object>)p.getOrDefault("counts",Map.of()));}catch(Exception e){return new HistoryItem(r.getId().toString(),r.getCreatedAt().toString(),r.getText(),"unknown",Map.of());}}).collect(Collectors.toList()); }
  public ReviewResponse get(UUID id){return response(repo.findById(id).orElseThrow(()->new NoSuchElementException("审查记录不存在")));}
  public void delete(UUID id){repo.deleteById(id);}
  private ReviewResponse response(Review r){try{return new ReviewResponse(r.getId().toString(),r.getText(),r.getMode(),r.getCreatedAt().toString(),mapper.readValue(r.getReportJson(),new TypeReference<>(){}),mapper.readValue(r.getVersionsJson(),new TypeReference<>(){}));}catch(Exception e){throw new IllegalStateException("审查报告解析失败");}}
}
