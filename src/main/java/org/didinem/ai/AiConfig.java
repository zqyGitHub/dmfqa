package org.didinem.ai;

import dev.langchain4j.mcp.McpToolProvider;
import dev.langchain4j.mcp.client.DefaultMcpClient;
import dev.langchain4j.mcp.client.McpClient;
import dev.langchain4j.mcp.client.transport.stdio.StdioMcpTransport;
import dev.langchain4j.model.chat.ChatModel;
import dev.langchain4j.model.openai.OpenAiChatModel;
import dev.langchain4j.service.AiServices;
import dev.langchain4j.service.tool.ToolProvider;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.util.StringUtils;

@Configuration
@EnableConfigurationProperties(AiProperties.class)
public class AiConfig {

    @Bean
    public ChatModel chatModel(AiProperties properties) {
        // Allow app to start without OPENAI_API_KEY; calls will fail at runtime.
        String apiKey = properties.getOpenai().getApiKey();
        if (!StringUtils.hasText(apiKey)) {
            apiKey = System.getenv("OPENAI_API_KEY");
        }
        if (!StringUtils.hasText(apiKey)) {
            apiKey = "missing";
        }

        return OpenAiChatModel.builder()
                .apiKey(apiKey)
                .modelName(properties.getOpenai().getModel())
                .temperature(properties.getOpenai().getTemperature())
                .strictTools(true)
                .parallelToolCalls(true)
                .build();
    }

    @Bean(destroyMethod = "close")
    public McpClient weatherMcpClient(AiProperties properties) {
        StdioMcpTransport transport = StdioMcpTransport.builder()
                .command(properties.getMcp().getWeather().getCommand())
                .logEvents(properties.getMcp().isLogEvents())
                .build();

        return DefaultMcpClient.builder()
                .key("weather")
                .clientName("springboot-weather-client")
                .clientVersion("0.1.0")
                .transport(transport)
                .build();
    }

    @Bean
    public ToolProvider toolProvider(McpClient weatherMcpClient) {
        return McpToolProvider.builder()
                .mcpClients(weatherMcpClient)
                .failIfOneServerFails(true)
                .build();
    }

    @Bean
    public WeatherAssistant weatherAssistant(ChatModel chatModel, ToolProvider toolProvider) {
        return AiServices.builder(WeatherAssistant.class)
                .chatModel(chatModel)
                .toolProvider(toolProvider)
                .systemMessage("你是一个天气助手。\n"
                        + "- 如果用户问题涉及“天气/温度/风速/下雨/穿衣”等，请优先调用工具获取实时数据。\n"
                        + "- 工具返回的 weather_code 需要用通俗中文解释（如果你不确定，直接说明是 Open-Meteo 的天气码并给出原始值）。\n"
                        + "- 回复尽量简洁、可执行（给出温度/体感/风速/时间）。\n")
                .build();
    }
}

