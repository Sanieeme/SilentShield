package com.silentshield.security;

import com.silentshield.domain.Role;
import com.silentshield.domain.SessionMode;
import java.util.UUID;

/** Authenticated caller. Mode is resolved from the server-side session, never from the token. */
public record SessionPrincipal(UUID customerId, UUID sessionId, SessionMode mode, Role role) {}
