package com.example.ambiguity.service;

import com.example.ambiguity.dto.ReviewDtos.ReviewResponse;
import org.apache.pdfbox.Loader;
import org.apache.pdfbox.text.PDFTextStripper;
import org.junit.jupiter.api.*;
import org.springframework.test.util.ReflectionTestUtils;
import java.nio.file.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class ReportPdfServiceTest {
  @Test void exportsChineseAndEveryIssueAcrossPages() throws Exception {
    var service=new ReportPdfService();
    String configured=System.getenv("PDF_FONT_PATH");
    if(configured!=null) ReflectionTestUtils.setField(service,"fontPath",configured);
    List<Map<String,Object>> issues=new ArrayList<>();
    for(int i=1;i<=12;i++){
      Map<String,Object> issue=new LinkedHashMap<>();
      issue.put("id","FINDING-"+i);issue.put("type","testability");issue.put("severity","medium");
      issue.put("explanation","用户预约后的状态和异常处理需要明确，确保需求可测试。");
      issue.put("quote","用户提交预约后应尽快收到通知。");issue.put("location","第1节");
      issue.put("missingConditions",List.of("明确响应时间和异常分支"));issue.put("questions",List.of("超时后是否允许重试？"));
      issue.put("acceptanceCriteria",List.of("提交后3秒内返回状态；模拟超时返回明确提示。"));
      issue.put("relatedRoles",List.of("用户","管理员"));issue.put("reworkRisk","需在开发前确认");issues.add(issue);
    }
    Map<String,Object> report=new LinkedHashMap<>();report.put("issues",issues);report.put("summary","发现十二项需要确认的需求。");
    report.put("riskLevel","medium");report.put("counts",Map.of("high",0,"medium",12,"low",0));
    report.put("document",Map.of("fileName","需求规格说明书.docx","recognizedVisuals",1,"visualCount",2,"visualKind","image","warnings",List.of("图片2未识别，需人工确认")));
    var review=new ReviewResponse(UUID.randomUUID().toString(),"用户提交预约后收到通知。\n[视觉识别：Word 图片 1] 类图中用户关联预约。","全面审查","2026-10-27T00:00:00Z",report,List.of());
    byte[] bytes=service.export(review);
    try(var pdf=Loader.loadPDF(bytes)){
      assertTrue(pdf.getNumberOfPages()>2);String text=new PDFTextStripper().getText(pdf);
      assertTrue(text.contains("需求质量审查报告"));assertTrue(text.contains("FINDING-12"));
      assertTrue(text.contains("图片2未识别"));assertTrue(text.contains("验收标准"));assertTrue(text.contains("类图中用户关联预约"));
    }
    Path artifact=Path.of("target/test-artifacts/report.pdf");Files.createDirectories(artifact.getParent());Files.write(artifact,bytes);
  }
  @Test void explainsMissingFontConfiguration(){
    var service=new ReportPdfService();ReflectionTestUtils.setField(service,"fontPath","missing-font.ttf");
    var review=new ReviewResponse("id","text","mode","date",Map.of(),List.of());
    var error=assertThrows(IllegalStateException.class,()->service.export(review));assertTrue(error.getMessage().contains("PDF_FONT_PATH"));
  }
}
