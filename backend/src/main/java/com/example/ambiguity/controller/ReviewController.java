package com.example.ambiguity.controller;

import com.example.ambiguity.dto.ReviewDtos.*;
import com.example.ambiguity.service.*;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import java.util.*;

@RestController @RequestMapping("/api/reviews")
public class ReviewController {
  private final ReviewService reviews; private final DocumentService docs;
  public ReviewController(ReviewService reviews,DocumentService docs){this.reviews=reviews;this.docs=docs;}
  @PostMapping public ReviewResponse create(@RequestBody ReviewRequest req){return reviews.create(req);}
  @PostMapping("/upload") public ParseResponse upload(@RequestParam("file") MultipartFile file) throws Exception {String text=docs.extract(file);return new ParseResponse(file.getOriginalFilename(),text,text.length());}
  @PostMapping("/{id}/follow-up") public ReviewResponse follow(@PathVariable UUID id,@RequestBody FollowUpRequest req){if(req.question()==null||req.question().isBlank())throw new IllegalArgumentException("追问内容不能为空");return reviews.follow(id,req.question());}
  @GetMapping public List<HistoryItem> history(){return reviews.history();}
  @GetMapping("/{id}") public ReviewResponse get(@PathVariable UUID id){return reviews.get(id);}
  @DeleteMapping("/{id}") @ResponseStatus(HttpStatus.NO_CONTENT) public void delete(@PathVariable UUID id){reviews.delete(id);}
  @ExceptionHandler(Exception.class) ResponseEntity<Map<String,String>> error(Exception e){return ResponseEntity.badRequest().body(Map.of("error",e.getMessage()==null?"请求处理失败":e.getMessage()));}
}
