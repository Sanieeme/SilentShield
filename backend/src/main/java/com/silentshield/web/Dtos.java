package com.silentshield.web;

import com.silentshield.domain.AccountTransaction;
import com.silentshield.domain.SecurityEvent;
import com.silentshield.service.AccountView;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Digits;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

/**
 * Note: no response type here has a "mode" field. Duress state must never
 * be observable from the customer-facing API.
 */
public final class Dtos {
    private Dtos() {}

    public record LoginRequest(
        @NotBlank @Pattern(regexp = "[A-Za-z0-9-]{1,32}") String customerNumber,
        @NotBlank @Pattern(regexp = "\\d{4,6}") String pin) {}

    public record LoginResponse(String accessToken, Instant expiresAt) {}

    public record WithdrawalRequest(
        @NotNull @DecimalMin("0.01") @Digits(integer = 12, fraction = 2) BigDecimal amount) {}

    public record BalanceResponse(String accountNumber, BigDecimal balance, String currency) {
        public static BalanceResponse from(AccountView v) {
            return new BalanceResponse(v.accountNumber(), v.balance(), "ZAR");
        }
    }

    public record TransactionResponse(String type, BigDecimal amount, BigDecimal balanceAfter, Instant createdAt) {
        public static TransactionResponse from(AccountTransaction t) {
            return new TransactionResponse(t.getType().name(), t.getAmount(), t.getBalanceAfter(), t.getCreatedAt());
        }
    }

    /** Analyst-only. */
    public record SecurityEventResponse(UUID id, UUID customerId, UUID sessionId, String eventType,
                                        String severity, String details, Instant createdAt) {
        public static SecurityEventResponse from(SecurityEvent e) {
            return new SecurityEventResponse(e.getId(), e.getCustomerId(), e.getSessionId(),
                e.getEventType().name(), e.getSeverity().name(), e.getDetails(), e.getCreatedAt());
        }
    }
}
