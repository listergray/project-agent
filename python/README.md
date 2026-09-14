# Python AI 编排

| 路径 | 说明 |
| --- | --- |
| `src/project_agent/` | LangGraph RAG / Copilot / FastAPI |
| `prompts/` | Prompt 模板（与代码解耦） |
| `tests/` | pytest |

仓库根执行：

```bash
pip install -e .
agent-api
# 或
uvicorn project_agent.api.server:app --port 8080
```

配置仍在仓库根 `conf/.env`；数据在 `data/`。
