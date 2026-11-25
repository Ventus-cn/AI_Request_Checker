package com.example.ambiguity;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class AmbiguityApplication {
  public static void main(String[] args) { SpringApplication.run(AmbiguityApplication.class, args); }
}
