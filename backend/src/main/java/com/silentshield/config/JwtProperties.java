package com.silentshield.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "silentshield.jwt")
public record JwtProperties(String secret, long ttlMinutes) {}
