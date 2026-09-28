package com.silentshield.domain;

import jakarta.persistence.*;
import java.time.Duration;
import java.time.Instant;
import java.util.UUID;

@Entity
@Table(name = "customers")
public class Customer {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "customer_number", nullable = false, unique = true)
    private String customerNumber;

    @Column(name = "full_name", nullable = false)
    private String fullName;

    @Column(name = "real_pin_hash", nullable = false)
    private String realPinHash;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Role role;

    @Column(name = "failed_attempts", nullable = false)
    private int failedAttempts;

    @Column(name = "locked_until")
    private Instant lockedUntil;

    protected Customer() {}

    public Customer(String customerNumber, String fullName, String realPinHash, Role role) {
        this.customerNumber = customerNumber;
        this.fullName = fullName;
        this.realPinHash = realPinHash;
        this.role = role;
    }

    public boolean isLocked(Instant now) {
        return lockedUntil != null && lockedUntil.isAfter(now);
    }

    /** @return true if this failure caused a lockout */
    public boolean registerFailure(int maxAttempts, Duration lockout, Instant now) {
        failedAttempts++;
        if (failedAttempts >= maxAttempts) {
            lockedUntil = now.plus(lockout);
            failedAttempts = 0;
            return true;
        }
        return false;
    }

    public void resetFailures() {
        failedAttempts = 0;
        lockedUntil = null;
    }

    public UUID getId() { return id; }
    public String getCustomerNumber() { return customerNumber; }
    public String getFullName() { return fullName; }
    public String getRealPinHash() { return realPinHash; }
    public Role getRole() { return role; }
}
