package com.silentshield.domain;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.util.UUID;

/**
 * Holds two logically separate balances:
 *  - realBalance:   the customer's actual money
 *  - duressBalance: the shadow balance shown when a session was opened with the duress PIN
 *
 * A withdrawal in duress mode is real money leaving the account, so it reduces BOTH balances.
 * The visible duress balance is also capped at the real balance so it can never show more
 * money than actually exists.
 */
@Entity
@Table(name = "accounts")
public class Account {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(name = "customer_id", nullable = false, unique = true)
    private UUID customerId;

    @Column(name = "account_number", nullable = false, unique = true)
    private String accountNumber;

    @Column(name = "real_balance", nullable = false, precision = 19, scale = 2)
    private BigDecimal realBalance;

    @Column(name = "duress_balance", nullable = false, precision = 19, scale = 2)
    private BigDecimal duressBalance;

    protected Account() {}

    public Account(UUID customerId, String accountNumber, BigDecimal realBalance, BigDecimal duressBalance) {
        this.customerId = customerId;
        this.accountNumber = accountNumber;
        this.realBalance = realBalance;
        this.duressBalance = duressBalance;
    }

    public BigDecimal visibleBalance(SessionMode mode) {
        return mode == SessionMode.DURESS ? duressBalance.min(realBalance) : realBalance;
    }

    public void withdraw(SessionMode mode, BigDecimal amount) {
        if (amount == null || amount.signum() <= 0) {
            throw new IllegalArgumentException("Amount must be positive");
        }
        if (visibleBalance(mode).compareTo(amount) < 0) {
            throw new InsufficientFundsException();
        }
        realBalance = realBalance.subtract(amount);
        if (mode == SessionMode.DURESS) {
            duressBalance = duressBalance.subtract(amount);
        }
    }

    public UUID getId() { return id; }
    public UUID getCustomerId() { return customerId; }
    public String getAccountNumber() { return accountNumber; }
}
