# InsureSpar 保险销售对练系统

## 📖 项目简介
InsureSpar 是一个基于大语言模型（LLM）与多智能体（Multi-Agent）技术构建的**保险销售对练与评测平台**。本项目作为系统的核心底层，为规划中的前端系统提供对话逻辑、状态机流转、异步打分机制以及对历史数据的查看支持。系统原生支持服务器推送事件（SSE）进行多路流式输出，为前端还原打字机等丰富交互提供了强大的服务端基础。

## ✨ 核心特性

- **双面对练模式**：
  - **人机对练 (Manual)**：人类销售人员与扮演特定画像的 AI 客户进行实时对话对练。
  - **自动对战 (Auto)**：指定特定销售策略，让系统内置的 AI 销售与 AI 客户全自动模拟对局，用于策略回放和话术学习。
- **LangGraph 业务流转驱动**：
  - 定义了 6 种标准业务流转状态（破冰、异议处理、同意核保、签单成功、需要跟进、客户拒绝）。
  - 设置底层护城河：**强制5轮防线**（避免一上来即结束业务）及 **2轮决策观察期**（防范大模型单轮幻觉导致的误判结束）。
- **多智能体各司其职**：
  - 🧠 **对话管家 (DM)**：后台暗中管控与判定当前业务处于何种阶段。
  - 🧑‍💼 **客户 Agent**：作为对手盘，内置工具调用能力（如查产品费率、查健康告知）。
  - 👓 **考官 Agent**：后台静默异步运行，从专业、合规、策略三个维度进行（0-10分）打分及话术点拨。
  - 🤖 **销售 Agent**（仅 Auto 模式有效）：接管人类按策略自动推销。
- **丰富的数据复盘**：
  - 每轮实时保存日志，当对局终结后，更会异步生成全局能力雷达图谱及长篇**AI总监复盘报告**。

## 🛠️ 技术栈
- **核心框架**：FastAPI (Python)
- **大模型及编排工具**：LangChain / LangGraph 
- **通信机制**：基于原生 EventSource 的 Server-Sent Events (SSE) 协议式长链推送
- **数据持久化**：MySQL / SQLAlchemy ORM
- **接口文档**：自带 Swagger UI 测试界（默认在 `/docs` 路径可见）

## 📂 项目结构
```text
InsureSpar/
├── backend/
│   ├── app/
│   │   ├── agents/       # AI智能体定义 (DM管家、客户、考官、自动销售)
│   │   ├── api/          # 路由层 (chat流式分发, auto自动对战, history拉取日志)
│   │   ├── core/         # 核心配置项与常量
│   │   ├── models/       # 底层数据实体层 (MySQL DB Model)
│   │   ├── schemas/      # 数据传输层 (Pydantic 请求体/响应体育)
│   │   ├── services/     # 业务服务层
│   │   └── tools/        # 外部挂载工具箱(供AI客户调用)
│   ├── data/             # 存放本地业务补充数据
│   ├── main.py           # FastAPI 服务主启动入口点
│   └── API_DOCUMENTATION.md # 后端提供给前端的重要交互与流式对接底稿
└── frontend/             # 预留前端应用目录 (开发中)
```

## 🔌 API 接口概览
系统开放三大业务类接口：

1. **手动人机对练**
   - `POST /api/session/create`：依据画像起新对练。
   - `POST /api/chat/stream`：**核心**对练 SSE 长链接对话接口。
   - `GET /api/personas`：获取可用的人员画像库。
2. **自动化对练**
   - `POST /api/auto/session/create`：依策略设定新建自动对决战局。
   - `POST /api/auto/step`：前端手动触发下一步逻辑并获取 SSE 反应。
   - `GET /api/auto/session/{id}/final-report`：生成终局总报告（包含雷达数据）。
3. **数据管理查询**
   - `GET /api/history/sessions`：分页拉取对局列表。
   - `GET /api/history/sessions/{id}`：穿透查看某对局全量话术与考官评审分。

## 🌐 针对前端同学的开发指引
前端界面为了实现良好的用户体验，极重度依赖 **SSE 慢响应推流** 的方式来对接接口。请务必优先通读 `/backend/API_DOCUMENTATION.md` 进行流式对齐！
下面列出一些最关键的前端须渲染的 `type` 事件帧：
- `phase` / `status`: 状态机内部步骤跃迁（可以作为灰字系统提示展示）。
- `token` / `sales_token`: 分组代表客户或销售的逐字输出，需要以打字机特效对接。
- `tool_call` / `tool_result`: AI调取工具过程（如可以绘制一个Loading图标展示其查资料的动作）。
- `stage_update`: 解析它带有的 `is_finished` 以锁定对局结束。

## 🚀 后端服务如何运行
（前置条件：安装 Python 3.10+ 环境，并准备好可用的 MySQL 数据库配置）

```bash
# 1. 切换到后台工作目录
cd backend

# 2. 建立虚拟环境并激活 (以Windows为例)
python -m venv .venv
.venv\Scripts\activate

# 3. 安装所需依赖库
pip install -r requirements.txt

# 4. 启动服务 
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
运行后打开 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) 即可浏览系统全链路 API 并进行在线真机调试。
