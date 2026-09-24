package com.example.ambiguity.service;

import org.apache.pdfbox.Loader;
import org.apache.pdfbox.text.PDFTextStripper;
import org.apache.poi.xwpf.usermodel.XWPFDocument;
import org.apache.poi.xwpf.usermodel.XWPFParagraph;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import java.io.*;
import java.util.stream.Collectors;

@Service
public class DocumentService {
  public String extract(MultipartFile file) throws IOException {
    String name = file.getOriginalFilename() == null ? "" : file.getOriginalFilename().toLowerCase();
    if (name.endsWith(".docx")) {
      try (XWPFDocument doc = new XWPFDocument(file.getInputStream())) {
        return doc.getParagraphs().stream().map(XWPFParagraph::getText).filter(s -> !s.isBlank()).collect(Collectors.joining("\n"));
      }
    }
    if (name.endsWith(".pdf")) {
      try (var pdf = Loader.loadPDF(file.getBytes())) { return new PDFTextStripper().getText(pdf); }
    }
    throw new IllegalArgumentException("仅支持 .docx 和文字型 .pdf 文件");
  }
}
