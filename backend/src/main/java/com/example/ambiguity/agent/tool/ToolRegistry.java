package com.example.ambiguity.agent.tool;

import org.springframework.stereotype.Component;

import java.util.*;

/**
 * 工具白名单。模型给出的函数名必须命中这里，否则直接拒绝；
 * 程序不会执行模型生成的任意方法名或命令。
 */
@Component
public class ToolRegistry {
  private final Map<String, Tool> tools = new LinkedHashMap<>();

  public ToolRegistry(List<Tool> discovered) {
    for (Tool tool : discovered) {
      tools.put(tool.spec().name(), tool);
    }
  }

  public Tool require(String name) {
    Tool tool = tools.get(name);
    if (tool == null) {
      throw new ToolException(ToolException.ARG_INVALID,
          "未知工具：" + name + "；允许调用：" + String.join("、", tools.keySet()));
    }
    return tool;
  }

  public Set<String> names() {
    return Collections.unmodifiableSet(tools.keySet());
  }

  public List<Map<String, Object>> schemas() {
    List<Map<String, Object>> list = new ArrayList<>();
    for (Tool tool : tools.values()) {
      Map<String, Object> function = new LinkedHashMap<>();
      function.put("name", tool.spec().name());
      function.put("description", tool.spec().description());
      function.put("parameters", tool.spec().parameters());
      Map<String, Object> item = new LinkedHashMap<>();
      item.put("type", "function");
      item.put("function", function);
      list.add(item);
    }
    return list;
  }
}