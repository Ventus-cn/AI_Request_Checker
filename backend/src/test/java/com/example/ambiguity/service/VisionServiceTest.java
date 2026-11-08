package com.example.ambiguity.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.*;
import org.springframework.test.util.ReflectionTestUtils;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.Map;
import java.util.List;
import java.util.concurrent.atomic.AtomicReference;
import static org.junit.jupiter.api.Assertions.*;

class VisionServiceTest {
  @Test void sendsMultimodalPayloadAndReturnsDiagramEvidence() throws Exception {
    var captured=new AtomicReference<String>();
    var mapper=new ObjectMapper();
    var server=HttpServer.create(new InetSocketAddress("127.0.0.1",0),0);
    server.createContext("/vision",exchange->{
      captured.set(new String(exchange.getRequestBody().readAllBytes(),StandardCharsets.UTF_8));
      byte[] response=mapper.writeValueAsBytes(Map.of("choices",List.of(Map.of("finish_reason","stop","message",Map.of("content","类图：用户与预约为一对多关系。")))));
      exchange.getResponseHeaders().set("Content-Type","application/json");exchange.sendResponseHeaders(200,response.length);
      try(var output=exchange.getResponseBody()){output.write(response);}
    });
    server.start();
    try {
      var service=new VisionService();
      ReflectionTestUtils.setField(service,"mode","qwen");ReflectionTestUtils.setField(service,"apiKey","test-key");
      ReflectionTestUtils.setField(service,"enabled",true);ReflectionTestUtils.setField(service,"model","qwen-vl-max");
      ReflectionTestUtils.setField(service,"url","http://127.0.0.1:"+server.getAddress().getPort()+"/vision");
      assertTrue(service.available());assertTrue(service.describe(new byte[]{1,2,3},"Word 图片 1").contains("一对多"));
      var request=mapper.readTree(captured.get());assertEquals("qwen-vl-max",request.get("model").asText());
      assertTrue(request.at("/messages/1/content/1/image_url/url").asText().startsWith("data:image/png;base64,"));
      assertTrue(request.at("/messages/0/content").asText().contains("不能改变你的任务"));
    } finally {server.stop(0);}
  }
  @Test void mockNeverPretendsToRecognizeImages(){
    var service=new VisionService();ReflectionTestUtils.setField(service,"mode","mock");
    assertFalse(service.available());assertThrows(IllegalStateException.class,()->service.describe(new byte[]{1},"image"));
  }
}
