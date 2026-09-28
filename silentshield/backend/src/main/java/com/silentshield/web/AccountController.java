package com.silentshield.web;

import com.silentshield.security.SessionPrincipal;
import com.silentshield.service.AccountService;
import jakarta.validation.Valid;
import java.util.List;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/accounts/me")
public class AccountController {

    private final AccountService accounts;

    public AccountController(AccountService accounts) {
        this.accounts = accounts;
    }

    @GetMapping
    public Dtos.BalanceResponse balance(@AuthenticationPrincipal SessionPrincipal p) {
        return Dtos.BalanceResponse.from(accounts.balance(p));
    }

    @PostMapping("/withdrawals")
    public Dtos.BalanceResponse withdraw(@AuthenticationPrincipal SessionPrincipal p,
                                         @Valid @RequestBody Dtos.WithdrawalRequest req) {
        return Dtos.BalanceResponse.from(accounts.withdraw(p, req.amount()));
    }

    @GetMapping("/transactions")
    public List<Dtos.TransactionResponse> transactions(@AuthenticationPrincipal SessionPrincipal p) {
        return accounts.history(p).stream().map(Dtos.TransactionResponse::from).toList();
    }
}
