# LLM Provider 配置指南

本项目支持两种LLM后端：Ollama 和 llama.cpp。通过配置文件 `.env` 中的 `LLM_PROVIDER` 环境变量进行切换。

## 配置说明

### 1. 在 `.env` 文件中设置 LLM_PROVIDER

```bash
# LLM Provider Configuration
# Options: 'ollama' or 'llamacpp'
LLM_PROVIDER=ollama
```

### 2. Ollama 配置

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_DEFAULT_MODEL=qwen3:8b
```

### 3. llama.cpp 配置

```bash
# llama.cpp Configuration
LLAMACPP_BASE_URL=http://localhost:8080
LLAMACPP_MODEL_PATH=models/llama-model.gguf
LLAMACPP_N_CTX=4096
LLAMACPP_N_THREADS=4
LLAMACPP_N_BATCH=512
```

## 使用 llama.cpp

### 启动 llama.cpp 服务器

首先，需要启动 llama.cpp 服务器：

```bash
# 使用 llama-server 启动（llama.cpp 编译后的二进制文件）
./llama-server \
  -m models/your-model.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  -c 4096 \
  -t 4 \
  --embedding
```

参数说明：
- `-m`: 模型文件路径
- `--host`: 监听地址
- `--port`: 监听端口
- `-c`: 上下文长度
- `-t`: 线程数
- `--embedding`: 启用嵌入功能

### 修改配置使用 llama.cpp

1. 修改 `.env` 文件：
```bash
LLM_PROVIDER=llamacpp
LLAMACPP_BASE_URL=http://localhost:8080
```

2. 重启后端服务

## API 接口

### 获取 LLM 健康状态

```http
GET /api/models/health
Authorization: Bearer <token>
```

响应：
```json
{
  "code": 200,
  "data": {
    "provider": "ollama",
    "available": true,
    "default_model": "qwen3:8b"
  },
  "message": "success"
}
```

### 获取可用模型列表

```http
GET /api/models/ollama
Authorization: Bearer <token>
```

响应：
```json
{
  "code": 200,
  "data": [
    {
      "name": "qwen3:8b",
      "size": 1234567890,
      "modified_at": "2024-01-01T00:00:00Z",
      "provider": "ollama"
    }
  ],
  "message": "success"
}
```

## 代码中使用

### 使用 LLM Factory 获取服务

```python
from app.services import get_llm_service, get_llm_provider

# 获取当前配置的 LLM 服务
llm_service = get_llm_service()

# 获取当前 provider 类型
provider = get_llm_provider()  # 'ollama' 或 'llamacpp'

# 使用服务
models = llm_service.get_models()
response = llm_service.chat(model, messages)
```

### 直接使用特定服务

```python
from app.services import get_ollama_service, get_llamacpp_service

# 使用 Ollama
ollama = get_ollama_service()
models = ollama.get_models()

# 使用 llama.cpp
llamacpp = get_llamacpp_service()
models = llamacpp.get_models()
```

## 接口兼容性

两个服务实现了完全相同的接口：

| 方法 | 说明 |
|------|------|
| `get_models()` | 获取可用模型列表 |
| `generate()` | 生成文本（非流式） |
| `generate_stream()` | 生成文本（流式） |
| `chat()` | 对话完成（非流式） |
| `chat_stream()` | 对话完成（流式） |
| `is_available()` | 检查服务是否可用 |

## 注意事项

1. **llama.cpp 限制**：llama.cpp 服务器通常一次只加载一个模型，因此 `get_models()` 返回的列表可能只包含一个模型。

2. **嵌入模型**：当前嵌入功能仍使用 Ollama（通过 `OLLAMA_EMBEDDING_MODEL` 配置），llama.cpp 的嵌入支持需要单独配置。

3. **上下文长度**：llama.cpp 的上下文长度在启动服务器时通过 `-c` 参数设置，而不是通过 API 动态调整。

4. **模型格式**：llama.cpp 使用 GGUF 格式的模型文件，与 Ollama 的模型格式不同。

## 故障排除

### llama.cpp 连接失败

1. 检查 llama.cpp 服务器是否已启动
2. 检查 `LLAMACPP_BASE_URL` 配置是否正确
3. 检查防火墙设置

### 模型加载失败

1. 确保模型文件路径正确
2. 确保模型文件格式为 GGUF
3. 检查模型文件是否完整

### 切换 provider 后服务未生效

1. 重启后端服务
2. 检查 `.env` 文件是否保存
3. 检查环境变量是否正确加载
