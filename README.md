# InsureSpar 保险销售对练系统

## 📖 项目简介
InsureSpar 是一个基于大语言模型（LLM）与多智能体（Multi-Agent）技术构建的**保险销售对练与评测平台**。本项目作为系统的核心底层，为规划中的前端系统提供对话逻辑、状态机流转、异步打分机制以及对历史数据的查看支持。系统原生支持服务器推送事件（SSE）进行多路流式输出，为前端还原打字机等丰富交互提供了强大的服务端基础。

## ✨ 核心特性

- **双面对练模式支持**：
  - **人机对练 (Manual)**：支持真实销售员进行“人为输入”，与扮演特定画像难度的 AI 客户实时交锋。
  - **自动对战 (Auto)**：调用全局销售 Agent 自动对战接管大局，支持前端点按触发**单步演练**或**全自动推演到底**，用于优秀业务策略回放与话术学习。
- **千人千面的配置数据库**：
  - 在 `data` 目录内置了多维度的**不同难度客户画像**（小白、杠精、理智型等）及**多元化销售应对风格**，满足差异化测评需求。
- **差异化高性能数据引擎与工具链**：
  - **基础保费引擎**：由于基础费率表体积较小，使用轻量级 `CSV` 加载常驻内存以供快速调用。
  - **现金价值推演引擎**：考虑到全生命周期现金价值表体量堪称恐怖，本着业务训练项目灵活性，创新式采用“**二次函数分段拟合**”方法实现大规模近似值的免库极速计算。
  - **RAG 混合检索规则库**：集成 SentenceTransformer (向量语义) 与 BM25 (局部关键词) 双通道检索，利用 **RRF (Reciprocal Rank Fusion)** 在末端加权融合，极速对齐核保规则。
- **LangGraph 业务流转护城河**：
  - 定义了 6 种标准业务流转状态。
  - 设置底层防伪装护城河：**强制5轮防线**及 **2轮决策观察期**，有效防范 LLM 的阶段单回合跳跃幻觉。
- **多智能体与考管严密打分机制**：
  - 🧠 对话管家 (DM) / 🧑‍💼 客户 Agent / 🤖 销售 Agent各司其职。
  - 👓 **后台异步考官 Agent** 先调用工具**客观算账取铁证**，再带铁证进入连坐惩罚矩阵（如：数字瞎编必然导致合规直接0分甚至熔断扣分），杜绝只看话术态度的偏颇评价题。

## 🛠️ 技术栈
- **核心框架**：FastAPI (Python)
- **大模型及多智能体编排**：LangChain / LangGraph 
- **通信与交互流式推送**：Server-Sent Events (SSE) 协议（极致还原原生大模型的逐字打字机与内部思维链动态 `phase` 流式传输）
- **混合检索内核**：`sentence-transformers` + `rank_bm25`
- **数据分析生态**：Pandas (CSV预处理与读取)
- **数据持久化**：MySQL / SQLAlchemy ORM
- **接口文档**：自带 Swagger UI (`/docs`)

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

## 📖 详细技术方案
深入的底层运转机制、考官打分细节、RAG混合检索、及数据拟合引擎实现逻辑，请参阅根目录下的 [技术可行性与架构设计文档](technical_feasibility.md)。

## 🚀 快速启动与环境部署

### 1. 准备工作：环境变量与数据库
在启动项目前，系统重度依赖正确的环境变量与可用的 MySQL 数据库。

1. 进入 `backend/` 目录，复制配置模板：
   ```bash
   cd backend
   cp .env.example .env
   ```
2. 编辑 `.env` 文件，填入实际参数：
   ```ini
   # ── 数据库 ──
   # 替换 user:password 为你的实际账号密码及库名
   DATABASE_URL=mysql+pymysql://root:password@localhost:3306/insurespar

   # ── LLM (默认配合 DeepSeek API) ──
   LLM_MODEL=deepseek-chat
   LLM_BASE_URL=https://api.deepseek.com
   DEEPSEEK_API_KEY=sk-your-api-key-here
   ```
3. 请确保你的 MySQL 中已手动创建名为 `insurespar`（对应上述配置库名） 的空数据库。框架启动时会利用 SQLAlchemy 自动进行全量数据表创建。

### 2. 启动后台核心服务 (FastAPI)
前置要求：Python 3.10+

```bash
# 从项目根目录进入后端工作目录
cd backend

# 建立并激活虚拟环境 (以Windows为例; Mac/Linux 请用 source .venv/bin/activate)
python -m venv .venv
.venv\Scripts\activate

# 安装所需依赖库
pip install -r requirements.txt

# 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
后端服务启动成功后，可以首先访问 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) 接口文档层确认所有服务加载无误（比如加载图谱与词向量文件）。

### 3. 启动前端对练界面 (Vue3 + Vite)
前置要求：Node.js 18+

请保留后端终端不要关闭，新开启一个终端窗口：

```bash
# 从项目根目录进入前端工作目录
cd frontend

# 安装前端依赖包
npm install

# 启动本地开发服务器
npm run dev
```
按照终端提示的 URL（通常为 `http://localhost:5173/`），在浏览器打开该地址，立刻体验 AI 驱动的高仿真保险实战大厅！
