package com.silentshield.service;

import com.silentshield.config.JwtProperties;
import com.silentshield.config.LockoutProperties;
import com.silentshield.domain.*;
import com.silentshield.repository.*;
import java.time.Duration;
import java.time.Instant;
import java.util.Optional;
import java.util.UUID;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AuthService {

    public record LoginResult(String accessToken, Instant expiresAt) {}

    private final CustomerRepository customers;
    private final DuressCredentialRepository duressCredentials;
    private final AuthSessionRepository sessions;
    private final PasswordEncoder encoder;
    private final JwtService jwt;
    private final JwtProperties jwtProps;
    private final LockoutProperties lockout;
    private final SecurityEventService events;
    private final String dummyHash;

    public AuthService(CustomerRepository customers, DuressCredentialRepository duressCredentials,
                       AuthSessionRepository sessions, PasswordEncoder encoder, JwtService jwt,
                       JwtProperties jwtProps, LockoutProperties lockout, SecurityEventService events) {
        this.customers = customers;
        this.duressCredentials = duressCredentials;
        this.sessions = sessions;
        this.encoder = encoder;
        this.jwt = jwt;
        this.jwtProps = jwtProps;
        this.lockout = lockout;
        this.events = events;
        this.dummyHash = encoder.encode("dummy-pin-for-constant-work");
    }

    /**
     * Real PIN  -> NORMAL session.
     * Duress PIN -> DURESS session (silent HIGH security event).
     * The response is identical in both cases.
     *
     * noRollbackFor: failed-attempt counters and security events must persist
     * even though we throw.
     */
    @Transactional(noRollbackFor = InvalidCredentialsException.class)
    public LoginResult login(String customerNumber, String pin) {
        Instant now = Instant.now();
        Optional<Customer> found = customers.findByCustomerNumber(customerNumber);

        if (found.isEmpty()) {
            encoder.matches(pin, dummyHash); // burn comparable time
            events.record(null, null, SecurityEventType.LOGIN_FAILED, Severity.LOW,
                "Unknown customer number: " + customerNumber);
            throw new InvalidCredentialsException();
        }
        Customer customer = found.get();

        if (customer.isLocked(now)) {
            encoder.matches(pin, dummyHash);
            throw new InvalidCredentialsException(); // same generic error, no lockout hint
        }

        // Always do BOTH comparisons so timing doesn't reveal which PIN type was entered.
        boolean realMatch = encoder.matches(pin, customer.getRealPinHash());
        boolean duressMatch = duressCredentials.findByCustomerIdAndActiveTrue(customer.getId())
            .map(d -> encoder.matches(pin, d.getPinHash()))
            .orElseGet(() -> encoder.matches(pin, dummyHash));

        if (!realMatch && !duressMatch) {
            boolean locked = customer.registerFailure(
                lockout.maxFailedAttempts(), Duration.ofMinutes(lockout.lockoutMinutes()), now);
            customers.save(customer);
            events.record(customer.getId(), null, SecurityEventType.LOGIN_FAILED, Severity.MEDIUM,
                "Failed PIN attempt");
            if (locked) {
                events.record(customer.getId(), null, SecurityEventType.ACCOUNT_LOCKED, Severity.HIGH,
                    "Locked after " + lockout.maxFailedAttempts() + " failed attempts");
            }
            throw new InvalidCredentialsException();
        }

        // Real PIN wins if (mis)configured so both match; enrollment must forbid equal PINs.
        SessionMode mode = realMatch ? SessionMode.NORMAL : SessionMode.DURESS;

        customer.resetFailures();
        customers.save(customer);

        Instant expiresAt = now.plus(Duration.ofMinutes(jwtProps.ttlMinutes()));
        AuthSession session = sessions.save(new AuthSession(customer.getId(), mode, expiresAt));

        if (mode == SessionMode.DURESS) {
            events.record(customer.getId(), session.getId(), SecurityEventType.DURESS_LOGIN,
                Severity.HIGH, "Login with duress PIN");
        }

        String token = jwt.issue(customer.getId(), session.getId(), customer.getRole(), expiresAt);
        return new LoginResult(token, expiresAt);
    }

    @Transactional
    public void logout(UUID sessionId) {
        sessions.findById(sessionId).ifPresent(s -> {
            s.revoke();
            sessions.save(s);
        });
    }
}
