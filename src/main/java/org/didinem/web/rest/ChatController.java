package org.didinem.web.rest;

import org.didinem.ai.WeatherAssistant;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
public class ChatController {

    private final WeatherAssistant assistant;

    public ChatController(WeatherAssistant assistant) {
        this.assistant = assistant;
    }

    @PostMapping(value = "/chat", consumes = MediaType.APPLICATION_JSON_VALUE, produces = MediaType.APPLICATION_JSON_VALUE)
    public ChatResponse chat(@RequestBody ChatRequest request) {
        String answer = assistant.chat(request.getMessage());
        return new ChatResponse(answer);
    }
}

