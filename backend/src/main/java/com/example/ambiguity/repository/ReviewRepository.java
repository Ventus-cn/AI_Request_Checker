package com.example.ambiguity.repository;
import com.example.ambiguity.model.Review;
import org.springframework.data.jpa.repository.JpaRepository;
import java.util.UUID;
public interface ReviewRepository extends JpaRepository<Review, UUID> {}
