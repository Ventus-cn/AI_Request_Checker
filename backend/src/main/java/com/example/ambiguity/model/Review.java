package com.example.ambiguity.model;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.*;

@Entity
@Table(name="reviews")
public class Review {
  @Id @GeneratedValue(strategy=GenerationType.UUID) private UUID id;
  @Column(nullable=false, columnDefinition="TEXT") private String text;
  private String mode;
  private Instant createdAt;
  @Column(columnDefinition="TEXT") private String reportJson;
  @Column(columnDefinition="TEXT") private String versionsJson;
  protected Review() {}
  public Review(String text, String mode, String reportJson) { this.text=text; this.mode=mode; this.reportJson=reportJson; this.createdAt=Instant.now(); this.versionsJson="[]"; }
  public UUID getId(){return id;} public String getText(){return text;} public String getMode(){return mode;} public Instant getCreatedAt(){return createdAt;} public String getReportJson(){return reportJson;} public void setReportJson(String v){reportJson=v;} public String getVersionsJson(){return versionsJson;} public void setVersionsJson(String v){versionsJson=v;}
}
