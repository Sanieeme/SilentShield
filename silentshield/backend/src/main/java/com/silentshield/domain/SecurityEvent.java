package com.silentshield.domain;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "security_events")
public class SecurityEvent {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "customer_id")
    private UUID customerId;

    @Column(name = "session_id")
    private UUID sessionId;

    @Enumerated(EnumType.STRING)
    @Column(name = "event_type", nullable = false)
    private SecurityEventType eventType;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Severity severity;

    @Column(columnDefinition = "TEXT")
    private String details;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt = Instant.now();

    protected SecurityEvent() {}

    public SecurityEvent(UUID customerId, UUID sessionId, SecurityEventType eventType,
                         Severity severity, String details) {
        this.customerId = customerId;
        this.sessionId = sessionId;
        this.eventType = eventType;
        this.severity = severity;
        this.details = details;
    }

    public UUID getId() { return id; }
    public UUID getCustomerId() { return customerId; }
    public UUID getSessionId() { return sessionId; }
    public SecurityEventType getEventType() { return eventType; }
    public Severity getSeverity() { return severity; }
    public String getDetails() { return details; }
    public Instant getCreatedAt() { return createdAt; }
}
