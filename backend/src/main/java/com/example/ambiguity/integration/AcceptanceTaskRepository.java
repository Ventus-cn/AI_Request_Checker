package com.example.ambiguity.integration;

import com.example.ambiguity.acceptance.dto.AcceptanceDtos.Checks;
import com.example.ambiguity.acceptance.dto.AcceptanceDtos.Report;
import org.springframework.data.jpa.repository.JpaRepository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

public interface AcceptanceTaskRepository extends JpaRepository<AcceptanceTask, String> {
  Optional<AcceptanceTask> findFirstByDedupeKeyAndStatusInOrderByCreatedAtDesc(String dedupeKey, List<String> statuses);

  List<AcceptanceTask> findTop20ByReviewIdOrderByCreatedAtDesc(String reviewId);

  List<AcceptanceTask> findByCreatedAtBeforeAndStatusIn(Instant before, List<String> statuses);
}