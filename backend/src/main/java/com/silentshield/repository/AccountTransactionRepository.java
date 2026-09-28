package com.silentshield.repository;

import com.silentshield.domain.AccountTransaction;
import com.silentshield.domain.SessionMode;
import java.util.List;
import java.util.UUID;
import org.springframework.data.jpa.repository.JpaRepository;

public interface AccountTransactionRepository extends JpaRepository<AccountTransaction, UUID> {
    List<AccountTransaction> findTop50ByAccountIdOrderByCreatedAtDesc(UUID accountId);
    List<AccountTransaction> findTop50ByAccountIdAndModeOrderByCreatedAtDesc(UUID accountId, SessionMode mode);
}
