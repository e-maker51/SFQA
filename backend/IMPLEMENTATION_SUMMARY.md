# LangChain + llama.cpp 实现总结

## 完成的工作

### 1. 配置文件更新 (`.env`)

新增以下配置项：

```bash
# LLM Provider Configuration
LLM_PROVIDER=ollama  # Options: 'ollama' or 'llamacpp'

# llama.cpp Configuration
LLAMACPP_BASE_URL=http://localhost:8080
LLAMACPP_MODEL_PATH=models/llama-model.gguf
LLAMACPP_N_CTX=4096
LLAMACPP_N_THREADS=4
LLAMACPP_N_BATCH=512
```

### 2. 后端配置更新 (`app/config.py`)

新增配置属性：
- `LLM_PROVIDER`: LLM 提供商选择
- `LLAMACPP_BASE_URL`: llama.cpp 服务器地址
- `LLAMACPP_MODEL_PATH`: 模型文件路径
- `LLAMACPP_N_CTX`: 上下文长度
- `LLAMACPP_N_THREADS`: 线程数
- `LLAMACPP_N_BATCH`: 批处理大小

### 3. 新建 llama.cpp 服务 (`app/services/llamacpp_service.py`)

实现了与 `OllamaService` 完全兼容的接口：

- `get_models()`: 获取可用模型
- `generate()`: 非流式文本生成
- `generate_stream()`: 流式文本生成
- `chat()`: 非流式对话
- `chat_stream()`: 流式对话（支持 OpenAI-compatible API 和 fallback 到 /completion）
- `is_available()`: 服务健康检查

### 4. 新建 LLM 工厂 (`app/services/llm_factory.py`)

提供统一的 LLM 服务接口：

- `LLMService`: 统一的 LLM 服务类，自动根据配置选择后端
- `LLMFactory`: 工厂类，管理 LLM 服务实例
- `get_llm_service()`: 获取 LLM 服务实例
- `get_llm_provider()`: 获取当前提供商

### 5. 更新现有服务

#### `app/services/chat_service.py`
- 将 `ollama_service` 替换为 `llm_service`
- `QuestionClassifier` 现在使用统一的 LLM 服务
- 所有聊天功能通过 `llm_service` 调用

#### `app/services/__init__.py`
- 导出新的服务类和函数

#### `app/api/model.py`
- 更新 `/api/models/ollama` 接口，返回包含 provider 信息
- 新增 `/api/models/health` 接口，返回 LLM 服务健康状态

## 文件变更列表

### 修改的文件
1. `backend/.env` - 添加 LLM_PROVIDER 和 llama.cpp 配置
2. `backend/app/config.py` - 添加配置属性
3. `backend/app/services/__init__.py` - 导出新服务
4. `backend/app/services/chat_service.py` - 使用统一的 LLM 服务
5. `backend/app/api/model.py` - 更新 API 接口

### 新建的文件
1. `backend/app/services/llamacpp_service.py` - llama.cpp 服务实现
2. `backend/app/services/llm_factory.py` - LLM 工厂类
3. `backend/test_llm_provider_simple.py` - 测试脚本
4. `backend/LLM_PROVIDER_GUIDE.md` - 使用指南

## 接口兼容性

`OllamaService` 和 `LlamaCppService` 实现了完全相同的公共接口：

| 方法 | Ollama | llama.cpp | 说明 |
|------|--------|-----------|------|
| `get_models()` | ✓ | ✓ | 获取模型列表 |
| `generate()` | ✓ | ✓ | 文本生成 |
| `generate_stream()` | ✓ | ✓ | 流式生成 |
| `chat()` | ✓ | ✓ | 对话完成 |
| `chat_stream()` | ✓ | ✓ | 流式对话 |
| `is_available()` | ✓ | ✓ | 健康检查 |

## 测试验证

运行测试脚本验证功能：

```bash
cd backend
python test_llm_provider_simple.py
```

测试结果：
- ✓ 服务接口兼容性测试
- ✓ LLM Factory 功能测试
- ✓ OllamaService 功能测试
- ✓ LlamaCppService 功能测试
- ✓ 统一接口测试
- ✓ 配置文件测试
- ✓ 配置类测试

## 使用方式

### 切换 Provider

修改 `.env` 文件中的 `LLM_PROVIDER`：

```bash
# 使用 Ollama
LLM_PROVIDER=ollama

# 使用 llama.cpp
LLM_PROVIDER=llamacpp
```

然后重启后端服务。

### 代码中使用

```python
from app.services import get_llm_service, get_llm_provider

# 获取当前配置的 LLM 服务
llm_service = get_llm_service()

# 检查当前 provider
provider = get_llm_provider()  # 'ollama' 或 'llamacpp'

# 使用服务（接口与之前相同）
models = llm_service.get_models()
response = llm_service.chat(model, messages)
```

## 注意事项

1. **嵌入模型**：当前嵌入功能仍使用 Ollama，llama.cpp 的嵌入支持需要额外配置
2. **llama.cpp 服务器**：需要单独启动 llama.cpp 服务器
3. **模型格式**：llama.cpp 使用 GGUF 格式模型
4. **上下文长度**：llama.cpp 的上下文长度在服务器启动时设置

## 后续建议

1. 考虑为 llama.cpp 添加嵌入支持
2. 添加更多的错误处理和重试机制
3. 考虑支持更多的 LLM 后端（如 vLLM、TGI 等）
