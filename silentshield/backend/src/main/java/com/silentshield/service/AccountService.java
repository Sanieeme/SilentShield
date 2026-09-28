package com.silentshield.service;

import com.silentshield.domain.*;
import com.silentshield.repository.AccountRepository;
import com.silentshield.repository.AccountTransactionRepository;
import com.silentshield.security.SessionPrincipal;
import java.math.BigDecimal;
import java.util.List;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.server.ResponseStatusException;

@Service
public class AccountService {

    private final AccountRepository accounts;
    private final AccountTransactionRepository transactions;
    private final SecurityEventService events;

    public AccountService(AccountRepository accounts, AccountTransactionRepository transactions,
                          SecurityEventService events) {
        this.accounts = accounts;
        this.transactions = transactions;
        this.events = events;
    }

    @Transactional(readOnly = true)
    public AccountView balance(SessionPrincipal p) {
        Account a = accounts.findByCustomerId(p.customerId()).orElseThrow(this::noAccount);
        return new AccountView(a.getAccountNumber(), a.visibleBalance(p.mode()));
    }

    @Transactional
    public AccountView withdraw(SessionPrincipal p, BigDecimal amount) {
        Account a = accounts.lockByCustomerId(p.customerId()).orElseThrow(this::noAccount);

        a.withdraw(p.mode(), amount); // throws InsufficientFundsException -> tx rolls back
        BigDecimal visible = a.visibleBalance(p.mode());

        transactions.save(new AccountTransaction(
            a.getId(), TransactionType.WITHDRAWAL, amount, p.mode(), visible));

        if (p.mode() == SessionMode.DURESS) {
            events.record(p.customerId(), p.sessionId(), SecurityEventType.DURESS_TRANSACTION,
                Severity.HIGH, "Duress withdrawal of " + amount);
        }
        return new AccountView(a.getAccountNumber(), visible);
    }

    /**
     * Duress sessions see only the shadow ledger (transactions made in duress mode);
     * normal sessions see everything.
     */
    @Transactional(readOnly = true)
    public List<AccountTransaction> history(SessionPrincipal p) {
        Account a = accounts.findByCustomerId(p.customerId()).orElseThrow(this::noAccount);
        return p.mode() == SessionMode.DURESS
            ? transactions.findTop50ByAccountIdAndModeOrderByCreatedAtDesc(a.getId(), SessionMode.DURESS)
            : transactions.findTop50ByAccountIdOrderByCreatedAtDesc(a.getId());
    }

    private ResponseStatusException noAccount() {
        return new ResponseStatusException(HttpStatus.NOT_FOUND, "No account");
    }
}
