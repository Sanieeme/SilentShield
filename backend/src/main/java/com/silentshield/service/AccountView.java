package com.silentshield.service;

import java.math.BigDecimal;

/** What the caller is allowed to see. Same shape in NORMAL and DURESS mode. */
public record AccountView(String accountNumber, BigDecimal balance) {}
