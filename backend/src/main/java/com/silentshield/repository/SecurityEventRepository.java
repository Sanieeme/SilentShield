package com.silentshield.repository;

import com.silentshield.domain.SecurityEvent;
import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface SecurityEventRepository extends JpaRepository<SecurityEvent, UUID> {
    List<SecurityEvent> findTop100ByOrderByCreatedAtDesc();
}
