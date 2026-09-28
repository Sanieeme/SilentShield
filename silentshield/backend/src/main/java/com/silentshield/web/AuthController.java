package com.silentshield.web;

import com.silentshield.security.SessionPrincipal;
import com.silentshield.service.AuthService;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final AuthService auth;

    public AuthController(AuthService auth) {
        this.auth = auth;
    }

    @PostMapping("/login")
    public Dtos.LoginResponse login(@Valid @RequestBody Dtos.LoginRequest req) {
        var result = auth.login(req.customerNumber(), req.pin());
        return new Dtos.LoginResponse(result.accessToken(), result.expiresAt());
    }

    @PostMapping("/logout")
    public ResponseEntity<Void> logout(@AuthenticationPrincipal SessionPrincipal principal) {
        auth.logout(principal.sessionId());
        return ResponseEntity.noContent().build();
    }
}
