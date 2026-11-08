package com.example.ambiguity.agent.tool;

import java.util.Map;

/**
 * 工具契约：名称、用途说明和 JSON Schema 参数定义。
 * Schema 采用 OpenAI function.parameters 结构，程序按此校验，不依赖模型自觉。
 */
public record ToolSpec(String name, String description, Map<String, Object> parameters) {
}