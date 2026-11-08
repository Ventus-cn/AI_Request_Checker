package com.example.ambiguity.service;

import org.junit.jupiter.api.*;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.util.ReflectionTestUtils;
import org.apache.poi.xwpf.usermodel.*;
import org.apache.poi.util.Units;
import org.apache.pdfbox.pdmodel.*;
import org.apache.pdfbox.pdmodel.graphics.image.LosslessFactory;
import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class DocumentServiceTest {
  private VisionService vision; private DocumentService service;
  @BeforeEach void setup() {
    vision=mock(VisionService.class); service=new DocumentService(vision);
    ReflectionTestUtils.setField(service,"maxUnits",30);
  }
  private byte[] image() throws Exception {
    var output=new ByteArrayOutputStream();
    ImageIO.write(new BufferedImage(100,60,BufferedImage.TYPE_INT_RGB),"png",output); return output.toByteArray();
  }
  private MockMultipartFile word(boolean picture, String content) throws Exception {
    try(var doc=new XWPFDocument();var out=new ByteArrayOutputStream()) {
      doc.createParagraph().createRun().setText(content);
      var table=doc.createTable(1,2); table.getRow(0).getCell(0).setText("管理员只能查看所属部门的预约");
      table.getRow(0).getCell(1).setText("异常时返回错误提示");
      if(picture) doc.createParagraph().createRun().addPicture(new ByteArrayInputStream(image()),Document.PICTURE_TYPE_PNG,"uml.png",Units.toEMU(100),Units.toEMU(60));
      doc.write(out);return new MockMultipartFile("file","需求.docx","application/octet-stream",out.toByteArray());
    }
  }
  private MockMultipartFile scan(boolean includeText) throws Exception {
    try(var pdf=new PDDocument();var out=new ByteArrayOutputStream()) {
      var page=new PDPage();pdf.addPage(page);
      try(var stream=new PDPageContentStream(pdf,page)) {
        if(includeText){stream.beginText();stream.setFont(new org.apache.pdfbox.pdmodel.font.PDType1Font(org.apache.pdfbox.pdmodel.font.Standard14Fonts.FontName.HELVETICA),12);stream.newLineAtOffset(20,100);stream.showText("User submits a reservation");stream.endText();}
        stream.drawImage(LosslessFactory.createFromImage(pdf,new BufferedImage(100,60,BufferedImage.TYPE_INT_RGB)),20,20);
      }
      pdf.save(out);return new MockMultipartFile("file","扫描.pdf","application/pdf",out.toByteArray());
    }
  }
  @Test void includesTablesAndKeepsPlainTextWithoutVisualCalls() throws Exception {
    var parsed=service.extract(word(false,"用户提交预约申请"));
    assertTrue(parsed.text().contains("所属部门"));assertEquals(0,parsed.document().visualCount());
    verify(vision,never()).describe(any(),any());
  }
  @Test void includesImageDescriptionAndLocation() throws Exception {
    when(vision.available()).thenReturn(true);when(vision.describe(any(),any())).thenReturn("类图：用户关联预约，1对多，预约提交后为待审核状态。");
    var parsed=service.extract(word(true,"系统需求"));
    assertTrue(parsed.text().contains("Word 图片 1"));assertTrue(parsed.text().contains("1对多"));
    assertEquals(1,parsed.document().recognizedVisuals());assertTrue(parsed.document().warnings().isEmpty());
  }
  @Test void warnsWhenVisionIsUnavailable() throws Exception {
    var parsed=service.extract(word(true,"系统需求"));
    assertEquals(0,parsed.document().recognizedVisuals());assertFalse(parsed.document().warnings().isEmpty());
  }
  @Test void failedProviderDoesNotDiscardReadableBody() throws Exception {
    when(vision.available()).thenReturn(true);when(vision.describe(any(),any())).thenThrow(new IllegalStateException("视觉调用失败"));
    var parsed=service.extract(word(true,"用户提交需求"));
    assertTrue(parsed.text().contains("用户提交需求"));assertEquals(0,parsed.document().recognizedVisuals());
    assertTrue(parsed.document().warnings().stream().anyMatch(w->w.contains("视觉调用失败")));
  }
  @Test void recognizesScannedPdf() throws Exception {
    when(vision.available()).thenReturn(true);when(vision.describe(any(),any())).thenReturn("用户通过系统提交预约；活动图中失败分支返回错误提示。");
    var parsed=service.extract(scan(false));assertEquals(1,parsed.document().recognizedVisuals());
    assertTrue(parsed.text().contains("PDF 第 1 页"));assertTrue(parsed.text().contains("失败分支"));
  }
  @Test void rejectsScansWithoutRecognitionRatherThanReviewingPageMarkers() throws Exception {
    assertThrows(IllegalArgumentException.class,()->service.extract(scan(false)));
  }
  @Test void extractsPdfTextOnceAndLimitsVisionToDiagramEvidence() throws Exception {
    when(vision.available()).thenReturn(true);when(vision.describe(any(),any())).thenReturn("类图：用户关联预约，1对多。");
    var parsed=service.extract(scan(true));
    assertEquals(1,parsed.text().split("User submits a reservation",-1).length-1);
    verify(vision).describe(any(),org.mockito.ArgumentMatchers.contains("正文已从PDF文字层提取，不要复述正文"));
  }
  @Test void enforcesVisualLimitWithExplicitWarning() throws Exception {
    when(vision.available()).thenReturn(true);ReflectionTestUtils.setField(service,"maxUnits",0);
    var parsed=service.extract(word(true,"系统需求"));assertEquals(0,parsed.document().recognizedVisuals());
    assertTrue(parsed.document().warnings().stream().anyMatch(w->w.contains("VISION_MAX_UNITS")));
  }
  @Test void rejectsLongDocumentsWithoutTruncation() throws Exception {
    assertThrows(IllegalArgumentException.class,()->service.extract(word(false,"需".repeat(20001))));
  }
  @Test void rejectsLegacyWord() {
    assertThrows(IllegalArgumentException.class,()->service.extract(new MockMultipartFile("file","需求.doc","application/msword",new byte[]{1,2})));
  }
}
