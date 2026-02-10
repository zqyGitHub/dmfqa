package org.didinem.ai;

import org.springframework.boot.context.properties.ConfigurationProperties;

import java.util.Arrays;
import java.util.List;

@ConfigurationProperties(prefix = "app.ai")
public class AiProperties {

    private OpenAi openai = new OpenAi();
    private Mcp mcp = new Mcp();

    public OpenAi getOpenai() {
        return openai;
    }

    public void setOpenai(OpenAi openai) {
        this.openai = openai;
    }

    public Mcp getMcp() {
        return mcp;
    }

    public void setMcp(Mcp mcp) {
        this.mcp = mcp;
    }

    public static class OpenAi {
        private String apiKey;
        private String model = "gpt-4o-mini";
        private Double temperature = 0.2;

        public String getApiKey() {
            return apiKey;
        }

        public void setApiKey(String apiKey) {
            this.apiKey = apiKey;
        }

        public String getModel() {
            return model;
        }

        public void setModel(String model) {
            this.model = model;
        }

        public Double getTemperature() {
            return temperature;
        }

        public void setTemperature(Double temperature) {
            this.temperature = temperature;
        }
    }

    public static class Mcp {
        private Weather weather = new Weather();
        private boolean logEvents = false;

        public Weather getWeather() {
            return weather;
        }

        public void setWeather(Weather weather) {
            this.weather = weather;
        }

        public boolean isLogEvents() {
            return logEvents;
        }

        public void setLogEvents(boolean logEvents) {
            this.logEvents = logEvents;
        }

        public static class Weather {
            /**
             * Command for stdio MCP server, e.g. ["python3","mcp/weather_mcp_server.py"]
             */
            private List<String> command = Arrays.asList("python3", "mcp/weather_mcp_server.py");

            public List<String> getCommand() {
                return command;
            }

            public void setCommand(List<String> command) {
                this.command = command;
            }
        }
    }
}

