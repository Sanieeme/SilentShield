package com.silentshield.web;

import com.silentshield.service.SecurityEventService;
import java.util.List;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/analyst")
public class AnalystController {

    private final SecurityEventService events;

    public AnalystController(SecurityEventService events) {
        this.events = events;
    }

    @GetMapping("/security-events")
    public List<Dtos.SecurityEventResponse> securityEvents() {
        return events.latest().stream().map(Dtos.SecurityEventResponse::from).toList();
    }
}
