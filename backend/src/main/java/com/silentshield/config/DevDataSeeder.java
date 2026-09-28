package com.silentshield.config;

import com.silentshield.domain.*;
import com.silentshield.repository.*;
import java.math.BigDecimal;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Profile;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

/**
 * Seeds the README demo scenario. Fake credentials, dev profile only.
 *   Customer 1042 : real PIN 4826, duress PIN 1357, real R20,000, duress R1,000
 *   Analyst A-001 : PIN 9090
 */
@Component
@Profile("dev")
public class DevDataSeeder implements CommandLineRunner {

    private final CustomerRepository customers;
    private final DuressCredentialRepository duress;
    private final AccountRepository accounts;
    private final PasswordEncoder encoder;

    public DevDataSeeder(CustomerRepository customers, DuressCredentialRepository duress,
                         AccountRepository accounts, PasswordEncoder encoder) {
        this.customers = customers;
        this.duress = duress;
        this.accounts = accounts;
        this.encoder = encoder;
    }

    @Override
    public void run(String... args) {
        if (customers.count() > 0) return;

        Customer demo = customers.save(
            new Customer("1042", "Demo Customer", encoder.encode("4826"), Role.CUSTOMER));
        duress.save(new DuressCredential(demo.getId(), encoder.encode("1357")));
        accounts.save(new Account(demo.getId(), "ACC-1042-0001",
            new BigDecimal("20000.00"), new BigDecimal("1000.00")));

        customers.save(new Customer("A-001", "Demo Analyst", encoder.encode("9090"), Role.SECURITY_ANALYST));
    }
}
