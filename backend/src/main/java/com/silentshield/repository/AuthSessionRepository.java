package com.silentshield.repository;

import com.silentshield.domain.AuthSession;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AuthSessionRepository extends JpaRepository<AuthSession, UUID> {}
