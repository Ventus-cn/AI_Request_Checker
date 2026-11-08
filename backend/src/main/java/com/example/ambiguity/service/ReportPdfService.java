package com.example.ambiguity.service;

import com.example.ambiguity.dto.ReviewDtos.ReviewResponse;
import org.apache.pdfbox.pdmodel.*;
import org.apache.pdfbox.pdmodel.common.PDRectangle;
import org.apache.pdfbox.pdmodel.font.PDType0Font;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import java.io.*;
import java.nio.file.*;
import java.util.*;
import java.util.List;

@Service
public class ReportPdfService {
  @Value("${app.pdf-font-path:}") private String fontPath;
  private static final Map<String,String> TYPES = Map.of("ambiguous_term","模糊表达","missing_boundary","边界缺口","conflict","需求冲突","permission","角色权限","testability","可测试性","security","安全风险","operational","运营异常","out_of_scope","超出任务范围");

  public byte[] export(ReviewResponse review) throws IOException {
    try (PDDocument pdf = new PDDocument(); InputStream fontInput = Files.newInputStream(findFont())) {
      PDType0Font font = PDType0Font.load(pdf, fontInput);
      pdf.getDocumentInformation().setTitle("需求质量审查报告");
      pdf.getDocumentInformation().setAuthor("AI 需求歧义审查器");
      try (Layout layout = new Layout(pdf, font)) {
        Map<String,Object> report = review.report();
        layout.heading("需求质量审查报告", 21);
        layout.line("档案编号：" + review.id());
        layout.line("创建时间（UTC）：" + review.createdAt());
        layout.line("审查视角：" + review.mode() + "    当前版本：" + (review.versions().size() + 1));
        layout.line("Prompt：" + report.getOrDefault("promptLabel", "修改后Prompt"));
        layout.line("本文件导出该档案当前完整报告，包含全部发现项。");
        if (report.get("document") instanceof Map<?,?> source) {
          layout.heading("来源文档与识别范围", 14);
          layout.line("文件：" + source.get("fileName"));
          layout.line("视觉识别：" + source.get("recognizedVisuals") + " / " + source.get("visualCount")
              + ("page".equals(source.get("visualKind")) ? " 页" : " 张图片"));
          layout.list("解析提示", source.get("warnings"));
        }
        layout.heading("执行摘要", 15);
        layout.line("总体风险：" + risk(report.get("riskLevel")));
        if (report.get("counts") instanceof Map<?,?> counts)
          layout.line("高风险：" + counts.get("high") + "    中风险：" + counts.get("medium") + "    低风险：" + counts.get("low"));
        layout.line(report.get("summary"));
        layout.heading("发现项与行动建议", 15);
        if (report.get("issues") instanceof List<?> issues) {
          if (issues.isEmpty()) layout.line("暂未发现明显问题。");
          for (Object value : issues) {
            if (!(value instanceof Map<?,?> issue)) continue;
            layout.heading(String.valueOf(issue.get("id")) + " | " + TYPES.getOrDefault(String.valueOf(issue.get("type")), String.valueOf(issue.get("type"))) + " | " + risk(issue.get("severity")), 13);
            layout.line(issue.get("explanation"));
            layout.line("原文位置：" + issue.get("location"));
            layout.line("原文证据：" + issue.get("quote"));
            layout.list("缺失条件", issue.get("missingConditions"));
            layout.list("待确认问题", issue.get("questions"));
            layout.list("验收标准", issue.get("acceptanceCriteria"));
            layout.list("相关角色", issue.get("relatedRoles"));
            layout.line("返工风险：" + issue.get("reworkRisk"));
          }
        }
        if (report.get("rag") instanceof Map<?,?> rag) {
          layout.heading("检索依据与来源", 15);
          layout.line(report.get("ragAnswer"));
          layout.line("检索方法：" + rag.get("method") + "    Top-k：" + rag.get("topK"));
          if (rag.get("chunks") instanceof List<?> chunks) for (Object value : chunks) {
            if (value instanceof Map<?,?> chunk) {
              layout.line("[" + chunk.get("id") + "] " + chunk.get("source") + " / " + chunk.get("title"));
              layout.line(chunk.get("text"));
            }
          }
        }
        layout.heading("审查输入（正文与图像转录）", 15);
        layout.line(review.text());
      }
      int total = pdf.getNumberOfPages();
      for (int i = 0; i < total; i++) {
        try (var stream = new PDPageContentStream(pdf, pdf.getPage(i), PDPageContentStream.AppendMode.APPEND, true)) {
          stream.beginText(); stream.setFont(font, 9); stream.setNonStrokingColor(new java.awt.Color(100,110,125));
          stream.newLineAtOffset(48, 28); stream.showText("SPEC LENS    |    " + (i + 1) + " / " + total); stream.endText();
        }
      }
      ByteArrayOutputStream output = new ByteArrayOutputStream(); pdf.save(output); return output.toByteArray();
    }
  }

  private Path findFont() {
    if (fontPath != null && !fontPath.isBlank()) {
      Path configured = Path.of(fontPath);
      if (Files.isRegularFile(configured)) return configured;
      throw new IllegalStateException("PDF_FONT_PATH 指向的字体文件不存在，请配置支持中文的 TTF 字体");
    }
    for (String candidate : List.of("C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/simfang.ttf",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttf", "/usr/share/fonts/truetype/arphic/ukai.ttf"))
      if (Files.isRegularFile(Path.of(candidate))) return Path.of(candidate);
    throw new IllegalStateException("未找到中文字体，请通过 PDF_FONT_PATH 配置支持中文的 TTF 字体后重启后端");
  }
  private static String risk(Object value) { return "high".equals(value) ? "高风险" : "medium".equals(value) ? "中风险" : "low".equals(value) ? "低风险" : String.valueOf(value); }

  private static class Layout implements AutoCloseable {
    private final PDDocument document; private final PDType0Font font;
    private PDPageContentStream stream; private float y;
    Layout(PDDocument document, PDType0Font font) throws IOException { this.document=document; this.font=font; page(); }
    void page() throws IOException {
      if (stream != null) stream.close();
      PDPage page = new PDPage(PDRectangle.A4); document.addPage(page);
      stream = new PDPageContentStream(document, page); y = 790;
    }
    void heading(String value, float size) throws IOException {
      if (y < 130) page();
      y -= 12; write(value, size, true); y -= 6;
    }
    void line(Object value) throws IOException { write(value == null ? "未提供" : String.valueOf(value), 10.5f, false); }
    void list(String label, Object value) throws IOException {
      line(label + "：");
      if (value instanceof List<?> items && !items.isEmpty()) for (Object item : items) line("  - " + item);
      else line("  未提供");
    }
    void write(String value, float size, boolean title) throws IOException {
      StringBuilder buffer = new StringBuilder(); float width = 0;
      for (int cp : value.codePoints().toArray()) {
        if (cp == '\r') continue;
        if (cp == '\n') { draw(buffer.toString(), size, title); buffer.setLength(0); width=0; continue; }
        String glyph = cp == '\t' ? "    " : new String(Character.toChars(cp));
        float glyphWidth;
        try { glyphWidth=font.getStringWidth(glyph) / 1000 * size; }
        catch (IllegalArgumentException e) { glyph="?"; glyphWidth=font.getStringWidth(glyph) / 1000 * size; }
        if (width + glyphWidth > 498 && buffer.length() > 0) { draw(buffer.toString(),size,title); buffer.setLength(0); width=0; }
        buffer.append(glyph); width+=glyphWidth;
      }
      if (!buffer.isEmpty()) draw(buffer.toString(), size, title);
    }
    void draw(String value, float size, boolean title) throws IOException {
      if (y < 58) page();
      stream.beginText(); stream.setFont(font,size);
      if(title) stream.setNonStrokingColor(new java.awt.Color(36,60,99)); else stream.setNonStrokingColor(new java.awt.Color(40,48,60));
      stream.newLineAtOffset(48,y); stream.showText(value); stream.endText(); y-=size*1.65f;
    }
    public void close() throws IOException { if(stream!=null) stream.close(); }
  }
}
