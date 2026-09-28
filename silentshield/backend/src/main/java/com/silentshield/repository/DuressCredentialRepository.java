package com.silentshield.repository;

import com.silentshield.domain.DuressCredential;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface DuressCredentialRepository extends JpaRepository<DuressCredential, UUID> {
    Optional<DuressCredential> findByCustomerIdAndActiveTrue(UUID customerId);
}
