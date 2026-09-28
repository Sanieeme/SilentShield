package com.silentshield.security;

import com.silentshield.domain.Role;
import com.silentshield.repository.AuthSessionRepository;
import com.silentshield.service.JwtService;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.time.Instant;
import java.util.List;
import java.util.UUID;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.filter.OncePerRequestFilter;

public class JwtAuthFilter extends OncePerRequestFilter {

    private final JwtService jwtService;
    private final AuthSessionRepository sessions;

    public JwtAuthFilter(JwtService jwtService, AuthSessionRepository sessions) {
        this.jwtService = jwtService;
        this.sessions = sessions;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res, FilterChain chain)
            throws ServletException, IOException {
        String header = req.getHeader("Authorization");
        if (header != null && header.startsWith("Bearer ")) {
            try {
                Claims claims = jwtService.parse(header.substring(7));
                UUID customerId = UUID.fromString(claims.getSubject());
                UUID sessionId = UUID.fromString(claims.get("sid", String.class));
                Role role = Role.valueOf(claims.get("role", String.class));

                sessions.findById(sessionId)
                    .filter(s -> !s.isRevoked()
                              && s.getExpiresAt().isAfter(Instant.now())
                              && s.getCustomerId().equals(customerId))
                    .ifPresent(s -> {
                        var principal = new SessionPrincipal(customerId, sessionId, s.getMode(), role);
                        var auth = new UsernamePasswordAuthenticationToken(
                            principal, null, List.of(new SimpleGrantedAuthority("ROLE_" + role)));
                        SecurityContextHolder.getContext().setAuthentication(auth);
                    });
            } catch (JwtException | IllegalArgumentException e) {
                // Invalid token: leave unauthenticated; the entry point returns 401.
            }
        }
        chain.doFilter(req, res);
    }
}
