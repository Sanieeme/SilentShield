package com.silentshield.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "silentshield.lockout")
public record LockoutProperties(int maxFailedAttempts, long lockoutMinutes) {}
