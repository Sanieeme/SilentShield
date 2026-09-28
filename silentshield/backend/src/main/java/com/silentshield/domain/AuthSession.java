package com.silentshield.domain;

import jakarta.persistence.*;
import java.time.Instant;
import java.util.UUID;

/**
 * Server-side session. The duress/normal mode lives HERE, not in the JWT,
 * so a person holding the token cannot decode it to discover the mode.
 */
@Entity
@Table(name = "auth_sessions")
public class AuthSession {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "customer_id", nullable = false)
    private UUID customerId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private SessionMode mode;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt = Instant.now();

    @Column(name = "expires_at", nullable = false)
    private Instant expiresAt;

    @Column(nullable = false)
    private boolean revoked;

    protected AuthSession() {}

    public AuthSession(UUID customerId, SessionMode mode, Instant expiresAt) {
        this.customerId = customerId;
        this.mode = mode;
        this.expiresAt = expiresAt;
    }

    public void revoke() { this.revoked = true; }

    public UUID getId() { return id; }
    public UUID getCustomerId() { return customerId; }
    public SessionMode getMode() { return mode; }
    public Instant getExpiresAt() { return expiresAt; }
    public boolean isRevoked() { return revoked; }
}
