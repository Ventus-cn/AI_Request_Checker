package com.example.ambiguity.agent.tool;

import java.util.*;

/**
 * 按 ToolSpec 的 JSON Schema 校验模型给出的参数。
 * 这里是程序侧的强制检查，不写在提示词里，模型无法跳过。
 */
public final class ArgumentValidator {
  private ArgumentValidator() {}

  @SuppressWarnings("unchecked")
  public static Map<String, Object> validate(ToolSpec spec, Map<String, Object> raw) {
    Map<String, Object> schema = spec.parameters();
    Map<String, Object> properties = (Map<String, Object>) schema.getOrDefault("properties", Map.of());
    List<String> required = (List<String>) schema.getOrDefault("required", List.of());
    Map<String, Object> input = raw == null ? Map.of() : raw;

    for (String key : input.keySet()) {
      if (!properties.containsKey(key)) {
        throw new ToolException(ToolException.ARG_INVALID,
            "不支持的参数：" + key + "；可用参数：" + String.join("、", properties.keySet()));
      }
    }
    for (String key : required) {
      if (input.get(key) == null) {
        throw new ToolException(ToolException.ARG_INVALID, "缺少必填参数：" + key);
      }
    }

    Map<String, Object> normalized = new LinkedHashMap<>();
    for (Map.Entry<String, Object> entry : properties.entrySet()) {
      String name = entry.getKey();
      Map<String, Object> definition = (Map<String, Object>) entry.getValue();
      Object value = input.get(name);
      if (value == null) {
        if (definition.containsKey("default")) normalized.put(name, definition.get("default"));
        continue;
      }
      normalized.put(name, check(spec.name(), name, value, definition));
    }
    return normalized;
  }

  private static Object check(String tool, String name, Object value, Map<String, Object> definition) {
    String type = String.valueOf(definition.getOrDefault("type", "string"));
    if ("integer".equals(type)) {
      if (!(value instanceof Number number) || number.doubleValue() != Math.rint(number.doubleValue())) {
        throw new ToolException(ToolException.ARG_INVALID, tool + "." + name + " 需要整数，收到：" + value);
      }
      int result = number.intValue();
      if (definition.get("minimum") instanceof Number min && result < min.intValue()) {
        throw new ToolException(ToolException.ARG_INVALID,
            tool + "." + name + " 不能小于 " + min.intValue() + "，收到：" + result);
      }
      if (definition.get("maximum") instanceof Number max && result > max.intValue()) {
        throw new ToolException(ToolException.ARG_INVALID,
            tool + "." + name + " 不能大于 " + max.intValue() + "，收到：" + result);
      }
      return result;
    }
    if ("string".equals(type)) {
      if (!(value instanceof String text)) {
        throw new ToolException(ToolException.ARG_INVALID, tool + "." + name + " 需要字符串，收到：" + value);
      }
      String trimmed = text.trim();
      if (definition.get("minLength") instanceof Number minLength && trimmed.length() < minLength.intValue()) {
        throw new ToolException(ToolException.ARG_INVALID,
            tool + "." + name + " 至少需要 " + minLength.intValue() + " 个字符");
      }
      if (definition.get("maxLength") instanceof Number maxLength && trimmed.length() > maxLength.intValue()) {
        throw new ToolException(ToolException.ARG_INVALID,
            tool + "." + name + " 不能超过 " + maxLength.intValue() + " 个字符，收到 " + trimmed.length());
      }
      if (definition.get("pattern") instanceof String pattern && !trimmed.matches(pattern)) {
        throw new ToolException(ToolException.ARG_INVALID,
            tool + "." + name + " 格式不正确：" + trimmed);
      }
      if (definition.get("enum") instanceof List<?> allowed && !allowed.contains(trimmed)) {
        throw new ToolException(ToolException.ARG_INVALID,
            tool + "." + name + " 只能取 " + allowed + "，收到：" + trimmed);
      }
      return trimmed;
    }
    throw new ToolException(ToolException.ARG_INVALID, tool + "." + name + " 的类型定义不受支持");
  }
}