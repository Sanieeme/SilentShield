package com.silentshield.domain;

import jakarta.persistence.*;
import java.util.UUID;

@Entity
@Table(name = "duress_credentials")
public class DuressCredential {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "customer_id", nullable = false)
    private UUID customerId;

    @Column(name = "pin_hash", nullable = false)
    private String pinHash;

    @Column(nullable = false)
    private boolean active = true;

    protected DuressCredential() {}

    public DuressCredential(UUID customerId, String pinHash) {
        this.customerId = customerId;
        this.pinHash = pinHash;
    }

    public UUID getCustomerId() { return customerId; }
    public String getPinHash() { return pinHash; }
    public boolean isActive() { return active; }
}
