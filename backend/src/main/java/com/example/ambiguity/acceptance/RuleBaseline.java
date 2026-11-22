package com.example.ambiguity.acceptance;

import com.example.ambiguity.acceptance.dto.AcceptanceDtos.Criterion;
import com.example.ambiguity.acceptance.dto.AcceptanceDtos.Report;
import com.example.ambiguity.acceptance.dto.AcceptanceDtos.TestSample;

import java.util.ArrayList;
import java.util.List;

/** 无 AI 基线：按中文句号切句，套固定模板。用于和模型方案对比，不参与产品主流程。 */
public final class RuleBaseline {
  private RuleBaseline() {}

  public static Report build(String text) {
    List<String> sentences = new ArrayList<>();
    for (String raw : text.split("[。；！？\\n]")) {
      String sentence = raw.trim();
      if (sentence.length() >= 8) sentences.add(sentence);
      if (sentences.size() >= 4) break;
    }
    if (sentences.isEmpty()) sentences.add(text.trim());

    List<Criterion> criteria = new ArrayList<>();
    for (int i = 0; i < sentences.size(); i++) {
      String sentence = sentences.get(i);
      criteria.add(new Criterion(
          "AC-" + (i + 1),
          "需求语句 " + (i + 1),
          "系统已部署并处于可用状态",
          "用户按需求描述执行操作",
          sentence,
          sentence,
          "must"));
    }

    List<TestSample> samples = List.of(new TestSample(
        "TS-1",
        "normal",
        sentences.get(0),
        "系统返回符合该句描述的结果",
        sentences.get(0)));

    return new Report(
        "normal",
        "按句子模板生成的初版验收标准（无 AI 基线）",
        criteria,
        samples,
        List.of(),
        List.of("无 AI 基线不判断需求是否充分，也不检查引用与覆盖"));
  }
}