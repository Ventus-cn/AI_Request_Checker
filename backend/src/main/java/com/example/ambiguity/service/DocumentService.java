package com.example.ambiguity.service;

import org.apache.pdfbox.Loader;
import org.apache.pdfbox.text.PDFTextStripper;
import org.apache.pdfbox.rendering.PDFRenderer;
import com.example.ambiguity.dto.ReviewDtos.*;
import org.apache.poi.xwpf.usermodel.XWPFDocument;
import org.apache.poi.xwpf.usermodel.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import java.io.*;
import java.util.*;
import java.util.List;
import javax.imageio.ImageIO;
import javax.imageio.ImageReader;
import java.awt.*;
import java.awt.image.BufferedImage;

@Service
public class DocumentService {
  private final VisionService vision;
  @Value("${app.vision-max-units:30}") private int maxUnits;
  public DocumentService(VisionService vision) { this.vision = vision; }

  public ParseResponse extract(MultipartFile file) throws IOException {
    String name = Optional.ofNullable(file.getOriginalFilename()).orElse("document");
    if (file.isEmpty()) throw new IllegalArgumentException("上传文件不能为空");
    if (file.getSize() > 10L * 1024 * 1024) throw new IllegalArgumentException("文件不能超过 10 MB");
    String suffix = name.toLowerCase(Locale.ROOT);
    StringBuilder text = new StringBuilder();
    List<String> warnings = new ArrayList<>();
    int total, recognized = 0;
    String kind;
    if (suffix.endsWith(".docx")) {
      kind = "image";
      try (XWPFDocument doc = new XWPFDocument(file.getInputStream())) {
        appendBody(doc.getBodyElements(), text);
        for (var header : doc.getHeaderList()) appendBody(header.getBodyElements(), text);
        for (var footer : doc.getFooterList()) appendBody(footer.getBodyElements(), text);
        var pictures = doc.getAllPictures();
        total = pictures.size();
        if (doc.getDocument().xmlText().matches("(?s).*<(?:[A-Za-z0-9_]+:)?(?:wsp|shape|relIds|chart|object)\\b.*"))
          warnings.add("文档可能包含 Word 原生形状、SmartArt、图表或嵌入对象；这些对象无法保证完整识别，建议另存为 PDF 后上传以识别整页。");
        if (canRecognize(total, warnings)) {
          for (int i = 0; i < Math.min(total, Math.max(0, maxUnits)); i++) {
            String location = "Word 图片 " + (i + 1) + "（" + pictures.get(i).getFileName() + "）";
            try {
              String description = vision.describe(normalizeImage(pictures.get(i).getData()), location);
              appendChecked(text, "\n[视觉识别：" + location + "；识别结果需核对原图]\n" + description + "\n");
              recognized++;
            } catch (IllegalArgumentException e) { throw e; }
            catch (Exception e) {
              warnings.add(location + " 未识别：" + e.getMessage());
              if (e instanceof IllegalStateException) break;
            }
          }
        }
      }
    } else if (suffix.endsWith(".pdf")) {
      kind = "page";
      try (var pdf = Loader.loadPDF(file.getBytes())) {
        if (pdf.isEncrypted() && !pdf.getCurrentAccessPermission().canExtractContent())
          throw new IllegalArgumentException("PDF 禁止提取内容，请上传有提取权限的文件");
        total = pdf.getNumberOfPages();
        PDFTextStripper stripper = new PDFTextStripper(); stripper.setSortByPosition(true);
        PDFRenderer renderer = new PDFRenderer(pdf); renderer.setSubsamplingAllowed(true);
        boolean recognize = canRecognize(total, warnings), providerFailed = false;
        for (int i = 0; i < total; i++) {
          stripper.setStartPage(i + 1); stripper.setEndPage(i + 1);
          String pageText = stripper.getText(pdf);
          appendChecked(text, "\n[PDF 第 " + (i + 1) + " 页正文]\n" + pageText);
          if (recognize && !providerFailed && i < Math.max(0, maxUnits)) {
            try {
              var box = pdf.getPage(i).getCropBox();
              float longest = Math.max(box.getWidth(), box.getHeight());
              if (!Float.isFinite(longest) || longest <= 0) throw new IOException("页面尺寸无效");
              BufferedImage image = renderer.renderImage(i, Math.min(1.7f, 1800f / longest));
              ByteArrayOutputStream output = new ByteArrayOutputStream(); ImageIO.write(image, "png", output);
              String scope = pageText.isBlank()
                  ? "；页面无可提取文字层，须转录图中文字、正文并识别图表"
                  : "；正文已从PDF文字层提取，不要复述正文，只转录图表标签并描述UML、流程图或其他图形的可见关系、顺序与条件";
              String description = vision.describe(output.toByteArray(), "PDF 第 " + (i + 1) + " 页" + scope);
              appendChecked(text, "\n[视觉识别：PDF 第 " + (i + 1) + " 页；识别结果需核对原图]\n" + description + "\n");
              recognized++;
            } catch (IllegalArgumentException e) { throw e; }
            catch (Exception e) {
              warnings.add("PDF 第 " + (i + 1) + " 页未识别：" + e.getMessage());
              if (e instanceof IllegalStateException) providerFailed = true;
            }
          }
        }
      }
    } else throw new IllegalArgumentException("仅支持 .docx 和 .pdf；旧版 .doc 请先另存为 .docx");
    if (total > recognized) warnings.add("有 " + (total - recognized) + ("page".equals(kind) ? " 页" : " 张图片") + "未完成视觉识别，审查可能遗漏图中的信息。");
    String result = text.toString().trim();
    if (result.replaceAll("\\[PDF 第 \\d+ 页正文\\]", "").isBlank())
      throw new IllegalArgumentException("未提取到可审查内容；扫描件或纯图片文档需要启用视觉模型并成功识别后重试");
    return new ParseResponse(name, result, result.length(), new DocumentSource(name, total, recognized, kind, warnings));
  }

  private boolean canRecognize(int total, List<String> warnings) {
    if (total == 0) return false;
    if (!vision.available()) {
      warnings.add("视觉识别未启用：需设置 AI_MODE=qwen、DASHSCOPE_API_KEY，并使用支持图片输入的 QWEN_VISION_MODEL。当前仅提取正文。");
      return false;
    }
    if (total > Math.max(0, maxUnits)) warnings.add("本次只识别前 " + Math.max(0, maxUnits) + " 个视觉单元；可调整 VISION_MAX_UNITS 或拆分文档。");
    return true;
  }
  private void appendBody(List<IBodyElement> elements, StringBuilder text) {
    for (IBodyElement element : elements) {
      if (element instanceof XWPFParagraph paragraph) appendChecked(text, paragraph.getText() + "\n");
      else if (element instanceof XWPFTable table) {
        for (XWPFTableRow row : table.getRows()) {
          for (XWPFTableCell cell : row.getTableCells()) { appendBody(cell.getBodyElements(), text); appendChecked(text, " | "); }
          appendChecked(text, "\n");
        }
      }
    }
  }
  private void appendChecked(StringBuilder text, String value) {
    if (text.length() + value.length() > 20000)
      throw new IllegalArgumentException("文档正文与图片识别结果合计超过 20000 个字符，请拆分文档后上传；系统不会截断内容");
    text.append(value);
  }
  private byte[] normalizeImage(byte[] bytes) throws IOException {
    try (var input = ImageIO.createImageInputStream(new ByteArrayInputStream(bytes))) {
      Iterator<ImageReader> readers = ImageIO.getImageReaders(input);
      if (!readers.hasNext()) throw new IOException("不支持此图片格式，请将 EMF/WMF/SVG 等图片转换为 PNG/JPEG 后重新上传");
      ImageReader reader = readers.next();
      try {
        reader.setInput(input);
        int longest = Math.max(reader.getWidth(0), reader.getHeight(0));
        var param = reader.getDefaultReadParam();
        int sample = Math.max(1, (int)Math.ceil(longest / 1800.0)); param.setSourceSubsampling(sample, sample, 0, 0);
        BufferedImage original = reader.read(0, param);
        BufferedImage rgb = new BufferedImage(original.getWidth(), original.getHeight(), BufferedImage.TYPE_INT_RGB);
        Graphics2D graphics = rgb.createGraphics(); graphics.setColor(Color.WHITE);
        graphics.fillRect(0, 0, rgb.getWidth(), rgb.getHeight()); graphics.drawImage(original, 0, 0, null); graphics.dispose();
        ByteArrayOutputStream output = new ByteArrayOutputStream(); ImageIO.write(rgb, "png", output); return output.toByteArray();
      } finally { reader.dispose(); }
    }
  }
}
