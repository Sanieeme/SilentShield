package com.silentshield.domain;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.math.BigDecimal;
import java.util.UUID;
import org.junit.jupiter.api.Test;

class AccountTest {

    private static BigDecimal r(String v) { return new BigDecimal(v); }

    private Account demoAccount() {
        return new Account(UUID.randomUUID(), "ACC-1", r("20000.00"), r("1000.00"));
    }

    @Test
    void readmeDemoScenario_duressWithdrawalsPersistAndReduceRealBalance() {
        Account a = demoAccount();

        assertThat(a.visibleBalance(SessionMode.DURESS)).isEqualByComparingTo("1000.00");

        a.withdraw(SessionMode.DURESS, r("400.00"));
        assertThat(a.visibleBalance(SessionMode.DURESS)).isEqualByComparingTo("600.00");

        // "next day" - same persisted account state, new duress session
        assertThat(a.visibleBalance(SessionMode.DURESS)).isEqualByComparingTo("600.00");
        a.withdraw(SessionMode.DURESS, r("200.00"));
        assertThat(a.visibleBalance(SessionMode.DURESS)).isEqualByComparingTo("400.00");

        // real PIN -> actual balance: 20,000 - 600
        assertThat(a.visibleBalance(SessionMode.NORMAL)).isEqualByComparingTo("19400.00");
    }

    @Test
    void duressWithdrawalCannotExceedShadowBalance() {
        Account a = demoAccount();
        assertThatThrownBy(() -> a.withdraw(SessionMode.DURESS, r("1000.01")))
            .isInstanceOf(InsufficientFundsException.class);
        assertThat(a.visibleBalance(SessionMode.NORMAL)).isEqualByComparingTo("20000.00");
    }

    @Test
    void normalWithdrawalDoesNotTouchDuressBalance() {
        Account a = demoAccount();
        a.withdraw(SessionMode.NORMAL, r("5000.00"));
        assertThat(a.visibleBalance(SessionMode.NORMAL)).isEqualByComparingTo("15000.00");
        assertThat(a.visibleBalance(SessionMode.DURESS)).isEqualByComparingTo("1000.00");
    }

    @Test
    void visibleDuressBalanceNeverExceedsRealBalance() {
        Account a = new Account(UUID.randomUUID(), "ACC-2", r("300.00"), r("1000.00"));
        assertThat(a.visibleBalance(SessionMode.DURESS)).isEqualByComparingTo("300.00");
        assertThatThrownBy(() -> a.withdraw(SessionMode.DURESS, r("500.00")))
            .isInstanceOf(InsufficientFundsException.class);
    }

    @Test
    void rejectsNonPositiveAmounts() {
        Account a = demoAccount();
        assertThatThrownBy(() -> a.withdraw(SessionMode.NORMAL, BigDecimal.ZERO))
            .isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> a.withdraw(SessionMode.NORMAL, r("-1.00")))
            .isInstanceOf(IllegalArgumentException.class);
    }
}
