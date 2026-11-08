package com.example.ambiguity.controller;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.apache.pdfbox.Loader;
import org.apache.pdfbox.text.PDFTextStripper;
import java.util.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;
import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest(properties={"app.ai-mode=mock","spring.datasource.url=jdbc:h2:mem:review_export_test;DB_CLOSE_DELAY=-1","spring.jpa.hibernate.ddl-auto=create-drop"})
@AutoConfigureMockMvc
class ReviewControllerTest {
  @Autowired MockMvc mvc;
  @Autowired ObjectMapper mapper;
  @Test void createArchiveFollowAndExportKeepDocumentCoverage() throws Exception {
    var source=Map.of("fileName","校园预约需求.docx","visualCount",2,"recognizedVisuals",1,"visualKind","image","warnings",List.of("图片2需要人工确认"));
    String input="用户登录后可以提交预约，管理员只能查看自己部门的数据。提交后系统返回预约状态和通知；失败返回错误提示。用户可以查看已有的预约记录及时间，预约时间不得超过两小时，异常时不得产生重复记录。管理员可以审核预约，并在页面返回结果。";
    String json=mapper.writeValueAsString(Map.of("text",input,"mode","全面审查","promptVersion","revised","document",source));
    String created=mvc.perform(post("/api/reviews").contentType(MediaType.APPLICATION_JSON).content(json))
        .andExpect(status().isOk()).andExpect(jsonPath("$.report.document.fileName").value("校园预约需求.docx"))
        .andReturn().getResponse().getContentAsString(java.nio.charset.StandardCharsets.UTF_8);
    String id=mapper.readTree(created).get("id").asText();
    mvc.perform(get("/api/reviews")).andExpect(status().isOk()).andExpect(jsonPath("$[0].id").value(id));
    mvc.perform(get("/api/reviews/"+id)).andExpect(status().isOk()).andExpect(jsonPath("$.report.document.recognizedVisuals").value(1));
    mvc.perform(post("/api/reviews/"+id+"/follow-up").contentType(MediaType.APPLICATION_JSON).content(mapper.writeValueAsString(Map.of("question","补充边界条件"))))
        .andExpect(status().isOk()).andExpect(jsonPath("$.versions.length()").value(1)).andExpect(jsonPath("$.report.document.fileName").value("校园预约需求.docx"));
    byte[] pdf=mvc.perform(get("/api/reviews/"+id+"/report.pdf")).andExpect(status().isOk())
        .andExpect(content().contentType(MediaType.APPLICATION_PDF)).andExpect(header().string("Content-Disposition","attachment; filename=\"review-"+id+".pdf\""))
        .andReturn().getResponse().getContentAsByteArray();
    try(var document=Loader.loadPDF(pdf)){
      String text=new PDFTextStripper().getText(document);assertTrue(text.contains("校园预约需求.docx"));
      assertTrue(text.contains("图片2需要人工确认"));assertTrue(text.contains("当前版本：2"));
    }
  }
  @Test void missingPdfReturnsReadableJson() throws Exception {
    mvc.perform(get("/api/reviews/"+UUID.randomUUID()+"/report.pdf").accept(MediaType.APPLICATION_PDF))
        .andExpect(status().isNotFound()).andExpect(content().contentType(MediaType.APPLICATION_JSON)).andExpect(jsonPath("$.error").value("审查记录不存在"));
  }
}
