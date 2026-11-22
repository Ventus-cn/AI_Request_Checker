package com.example.ambiguity.acceptance;

import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Component;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

/** Prompt 放在 resources/acceptance 下，按版本加载，避免散落在 Java 字符串里。 */
@Component
public class AcceptancePrompts {
  private final String initial;
  private final String revised;

  public AcceptancePrompts() {
    this.initial = read("acceptance/prompt-initial.txt");
    String loadedRevised = read("acceptance/prompt-revised.txt");
    this.revised = loadedRevised == null ? initial : loadedRevised;
  }

  public String load(String version) {
    return "original".equalsIgnoreCase(version) ? initial : revised;
  }

  public String label(String version) {
    return "original".equalsIgnoreCase(version) ? "初版 Prompt" : "修订版 Prompt";
  }

  private String read(String path) {
    ClassPathResource resource = new ClassPathResource(path);
    if (!resource.exists()) return null;
    try (InputStream in = resource.getInputStream()) {
      return new String(in.readAllBytes(), StandardCharsets.UTF_8).trim();
    } catch (IOException e) {
      throw new IllegalStateException("读取 Prompt 失败：" + path, e);
    }
  }
}