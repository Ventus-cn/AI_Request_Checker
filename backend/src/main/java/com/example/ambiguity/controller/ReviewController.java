package com.example.ambiguity.controller;

import com.example.ambiguity.dto.ReviewDtos.*;
import com.example.ambiguity.service.*;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import java.util.*;

@RestController @RequestMapping("/api/reviews")
public class ReviewController {
  private final ReviewService reviews; private final DocumentService docs; private final ReportPdfService pdf;
  public ReviewController(ReviewService reviews,DocumentService docs,ReportPdfService pdf){this.reviews=reviews;this.docs=docs;this.pdf=pdf;}
  @PostMapping public ReviewResponse create(@RequestBody ReviewRequest req){return reviews.create(req);}
  @PostMapping("/upload") public ParseResponse upload(@RequestParam("file") MultipartFile file) throws Exception {
    if (file == null || file.isEmpty()) throw new IllegalArgumentException("上传文件不能为空");
    if (file.getSize() > 10L * 1024 * 1024) throw new IllegalArgumentException("文件不能超过 10 MB");
    return docs.extract(file);
  }
  @PostMapping("/{id}/follow-up") public ReviewResponse follow(@PathVariable UUID id,@RequestBody FollowUpRequest req){if(req==null||req.question()==null||req.question().isBlank())throw new IllegalArgumentException("追问内容不能为空");return reviews.follow(id,req.question());}
  @GetMapping public List<HistoryItem> history(){return reviews.history();}
  @GetMapping("/{id}") public ReviewResponse get(@PathVariable UUID id){return reviews.get(id);}
  @GetMapping(value="/{id}/report.pdf", produces=MediaType.APPLICATION_PDF_VALUE)
  public ResponseEntity<byte[]> export(@PathVariable UUID id) throws Exception {
    byte[] bytes = pdf.export(reviews.get(id));
    return ResponseEntity.ok().contentType(MediaType.APPLICATION_PDF)
        .header(HttpHeaders.CONTENT_DISPOSITION, ContentDisposition.attachment().filename("review-"+id+".pdf").build().toString())
        .cacheControl(CacheControl.noStore()).body(bytes);
  }
  @DeleteMapping("/{id}") @ResponseStatus(HttpStatus.NO_CONTENT) public void delete(@PathVariable UUID id){reviews.delete(id);}
  @ExceptionHandler(NoSuchElementException.class) ResponseEntity<Map<String,String>> notFound(Exception e){return ResponseEntity.status(HttpStatus.NOT_FOUND).contentType(MediaType.APPLICATION_JSON).body(Map.of("error",e.getMessage()));}
  @ExceptionHandler(Exception.class) ResponseEntity<Map<String,String>> error(Exception e){return ResponseEntity.badRequest().contentType(MediaType.APPLICATION_JSON).body(Map.of("error",e.getMessage()==null?"请求处理失败":e.getMessage()));}
}
