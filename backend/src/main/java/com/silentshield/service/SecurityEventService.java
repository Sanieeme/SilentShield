package com.silentshield.service;

import com.silentshield.domain.SecurityEvent;
import com.silentshield.domain.SecurityEventType;
import com.silentshield.domain.Severity;
import com.silentshield.repository.SecurityEventRepository;
import java.util.List;
import java.util.UUID;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

/**
 * Single choke point for security events. In Phase 3 this is where events
 * will also be published to Kafka for the data pipeline.
 */
@Service
public class SecurityEventService {

    private final SecurityEventRepository repo;

    public SecurityEventService(SecurityEventRepository repo) {
        this.repo = repo;
    }

    @Transactional
    public void record(UUID customerId, UUID sessionId, SecurityEventType type,
                       Severity severity, String details) {
        repo.save(new SecurityEvent(customerId, sessionId, type, severity, details));
    }

    @Transactional(readOnly = true)
    public List<SecurityEvent> latest() {
        return repo.findTop100ByOrderByCreatedAtDesc();
    }
}
