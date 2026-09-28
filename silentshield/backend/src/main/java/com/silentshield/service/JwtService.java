package com.silentshield.service;

import com.silentshield.config.JwtProperties;
import com.silentshield.domain.Role;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Date;
import java.util.UUID;
import javax.crypto.SecretKey;
import org.springframework.stereotype.Service;

@Service
public class JwtService {

    private final SecretKey key;

    public JwtService(JwtProperties props) {
        this.key = Keys.hmacShaKeyFor(props.secret().getBytes(StandardCharsets.UTF_8));
    }

    /** Deliberately contains NO duress/normal mode information. */
    public String issue(UUID customerId, UUID sessionId, Role role, Instant expiresAt) {
        return Jwts.builder()
            .subject(customerId.toString())
            .claim("sid", sessionId.toString())
            .claim("role", role.name())
            .issuedAt(new Date())
            .expiration(Date.from(expiresAt))
            .signWith(key)
            .compact();
    }

    public Claims parse(String token) {
        return Jwts.parser().verifyWith(key).build().parseSignedClaims(token).getPayload();
    }
}
