# Spring Boot 2.7 + JDK 11 + LangChain4j + OpenAI + MCP 天气工具示例

这个仓库演示了：

- Spring Boot **2.7.x**
- JDK **11**（`maven-compiler-plugin` 编译目标为 11）
- 使用 **LangChain4j** 调用 **OpenAI** 大模型
- 通过 **MCP（Model Context Protocol）** 的 `tools/list` + `tools/call` 访问“天气工具”

其中 MCP 天气工具由本仓库自带的 `python3` 脚本提供（Open-Meteo 数据源，无需天气 API Key）。

## 运行前置

- **JDK 11+**
- **Maven 3.8+**
- **Python 3**（用于启动 MCP 天气 server）
- **OpenAI API Key**

## 快速开始

### 1) 配置 OpenAI Key

推荐用环境变量：

```bash
export OPENAI_API_KEY="YOUR_KEY"
```

（代码会优先读取 `app.ai.openai.api-key`，为空则自动读取 `OPENAI_API_KEY`）

### 2) 启动 Spring Boot

```bash
mvn spring-boot:run
```

启动后会暴露一个接口：

- `POST /api/chat`

### 3) 调用接口

```bash
curl -s http://localhost:8080/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"北京现在天气怎么样？"}'
```

LangChain4j 会在需要时通过 MCP 调用天气工具，然后把结果组织成回答。

## MCP 天气工具（stdio）

默认 MCP server 命令在 `src/main/resources/application.properties`：

- `app.ai.mcp.weather.command=python3,mcp/weather_mcp_server.py`

它实现了最小 MCP 协议（stdio + 换行分隔 JSON-RPC）：

- `initialize`
- `tools/list`
- `tools/call`（工具名：`get_weather`）
- `ping`

你也可以单独 smoke test：

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"x","version":"0"}}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_weather","arguments":{"city":"上海"}}}' \
| python3 mcp/weather_mcp_server.py
```

## 代码入口

- **OpenAI + MCP 组装**：`src/main/java/org/didinem/ai/AiConfig.java`
- **配置项**：`src/main/java/org/didinem/ai/AiProperties.java`
- **对外 REST API**：`src/main/java/org/didinem/web/rest/ChatController.java`
- **MCP 天气 server**：`mcp/weather_mcp_server.py`

