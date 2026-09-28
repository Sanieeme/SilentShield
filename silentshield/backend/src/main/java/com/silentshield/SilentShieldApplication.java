package com.silentshield;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
public class SilentShieldApplication {
    public static void main(String[] args) {
        SpringApplication.run(SilentShieldApplication.class, args);
    }
}
