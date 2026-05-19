<!-- Dev specification skeleton for the project. Fill sections with details later. -->
# Developer Specification (DEV_SPEC)

> 版本：0.1 — 文档结构草案

## 目录

- 项目概述
- 核心特点
- 技术选型
- 测试方案
- 系统架构与模块设计
- 项目排期
- 可扩展性与未来展望

---

## 1. 项目概述
本项目基于多阶段检索增强生成（RAG, Retrieval-Augmented Generation）与模型上下文协议（MCP, Model Context Protocol）设计，目标是搭建一个可扩展、高可观测、易迭代的智能问答与知识检索框架。

### 设计理念 (Design Philosophy)

本项目不仅是一个功能完备的智能问答框架，更是一个专为 **RAG 技术学习与面试求职** 设计的实战平台：

#### 1️⃣ 实战驱动学习 (Learn by Doing)
项目架构本身就是 RAG 面试题的"**活体答案**"。我们将经典面试考点直接融入代码设计，通过动手实践来巩固理论知识：
- 分层检索 (Hierarchical Retrieval)
- Hybrid Search (BM25 + Dense Embedding)
- Rerank 重排序机制
- Embedding 策略与优化
- RAG 性能评测 (Ragas/DeepEval)

#### 2️⃣ 开箱即用与深度扩展并重 (Plug-and-Play & Extensible)
- **开箱即用**：提供 MCP 标准接口，可直接对接 Copilot/Claude，拿到项目即可运行体验。
- **深度扩展**：保留完全模块化的内部结构，方便开发者替换组件、魔改算法，作为具备深度的个人简历项目。
- **扩展指引**：文档中会明确指出各模块的扩展方向与建议，帮助你在掌握基础后继续深入迭代。

#### 3️⃣ 配套教学资源 (Comprehensive Learning Materials)
我会提供**三位一体**的配套学习资源，帮助你快速吃透项目：

| 资源类型 | 内容说明 |
|---------|---------|
| 📄 **技术文档** | 架构设计文档、技术选型说明、模块详解 |
| 💻 **代码示范** | 带详细注释的源码、关键模块的 Step-by-step 实现 |
| 🎬 **视频讲解** | RAG 核心知识点回顾、代码细节精讲、环境配置教程 |

#### 4️⃣ 学习路线与面试指南 (Study Guide & Interview Prep)
针对每个模块，我会整理：
- **📚 知识点清单**：这块涉及哪些理论知识需要提前学习（如 BM25 原理、FAISS 索引类型、Cross-Encoder vs Bi-Encoder）
- **❓ 高频面试题**：结合项目代码讲解常见面试问题及参考答案
- **📝 简历撰写建议**：如何将本项目的亮点写进简历，突出技术深度

---

## 2. 核心特点

### RAG 策略与设计亮点
本项目在 RAG 链路的关键环节采用了经典的工程化优化策略，平衡了检索的查准率与查全率，具体思想如下：
- **分块策略 (Chunking Strategy)**：采用智能分块与上下文增强，为高质量检索打下基础。
    - **智能分块**：摒弃机械的定长切分，采用语义感知的切分策略以保留完整语义；
    - **上下文增强**：为 Chunk 注入文档元数据（标题、页码）和图片描述（Image Caption），确保检索时不仅匹配文本，还能感知上下文。
- **粗排召回 (Coarse Recall / Hybrid Search)**：采用 **混合检索** 策略作为第一阶段召回，快速筛选候选集。
    - 结合 **稀疏检索 (Sparse Retrieval/BM25)** 利用关键词精确匹配，解决专有名词查找问题；
    - 结合 **稠密检索 (Dense Retrieval/Embedding)** 利用语义向量，解决同义词与模糊表达问题；
    - 两者互补，通过 RRF (Reciprocal Rank Fusion) 算法融合，确保查全率与查准率的平衡。
- **精排重排 (Rerank / Fine Ranking)**：在粗排召回的基础上进行深度语义排序。
	- 采用 Cross-Encoder（专用重排模型）或 LLM Rerank（可选后端）对候选集进行逐一打分，识别细微的语义差异。
    - 通过 **"粗排(低成本泛召回) -> 精排(高成本精过滤)"** 的两段式架构，在不牺牲整体响应速度的前提下大幅提升 Top-Results 的精准度。

### 全链路可插拔架构 (Pluggable Architecture)
鉴于 AI 技术的快速演进，本项目在架构设计上追求**极致的灵活性**，拒绝与特定模型或供应商强绑定。**整个系统**（不仅是 RAG 链路）的每一个核心环节均定义了抽象接口，支持"乐高积木式"的自由替换与组合：

- **LLM 调用层插拔 (LLM Provider Agnostic)**：
    - 核心推理 LLM 通过统一的抽象接口封装，支持**多协议**无缝切换：
        - **Azure OpenAI**：企业级 Azure 云端服务，符合合规与安全要求；
        - **OpenAI API**：直接对接 OpenAI 官方接口；
        - **本地模型**：支持 Ollama、vLLM、LM Studio 等本地私有化部署方案；
        - **其他云服务**：DeepSeek、Anthropic Claude 等第三方 API。
    - 通过配置文件一键切换后端，**零代码修改**即可完成 LLM 迁移，便于成本优化、隐私合规或 A/B 测试。

- **Embedding & Rerank 模型插拔 (Model Agnostic)**：
    - Embedding 模型与 Rerank 模型同样采用统一接口封装；
    - 支持云端服务（OpenAI Embedding, Cohere Rerank）与本地模型（Sentence-Transformers, BGE）自由切换。

- **RAG Pipeline 组件插拔**：
    - **Loader（解析器）**：支持 PDF、Markdown、Code 等多种文档解析器独立替换；
    - **Smart Splitter（切分策略）**：语义切分、定长切分、递归切分等策略可配置；
    - **Transformation（元数据/图文增强逻辑）**：OCR、Image Captioning 等增强模块可独立配置。

- **检索策略插拔 (Retrieval Strategy)**：
    - 支持动态配置纯向量、纯关键词或混合检索模式；
    - 支持灵活更换向量数据库后端（如从 Chroma 迁移至 Qdrant、Milvus）。

- **评估体系插拔 (Evaluation Framework)**：
    - 评估模块不锁定单一指标，支持挂载不同的 Evaluator（如 Ragas, DeepEval）以适应不同的业务考核维度。

这种设计确保开发者可以**零代码修改**即可进行 A/B 测试、成本优化或隐私迁移，使系统具备极强的生命力与环境适应性。

### MCP 生态集成 (Copilot / ReSearch)
本项目的核心设计完全遵循 Model Context Protocol (MCP) 标准，这使得它不仅是一个独立的问答服务，更是一个即插即用的知识上下文提供者。

- **工作原理**：
    - 我们的 Server 作为一个 **MCP Server** 运行，暴露一组标准的 `tools` 和 `resources` 接口。
    - **MCP Clients**（如 GitHub Copilot, ReSearch Agent, Claude Desktop 等）可以直接连接到这个 Server。
    - **无缝接入**：当你在 GitHub Copilot 中提问时，Copilot 作为一个 MCP Host，能够自动发现并调用我们的 Server 提供的工具（如 `search_documentation`），获取我们内置的私有文档知识，然后结合这些上下文来回答你的问题。
- **优势**：
    - **零前端开发**：无需为知识库开发专门的 Chat UI，直接复用开发者已有的编辑器（VS Code）和 AI 助手。
    - **上下文互通**：Copilot 可以同时看到你的代码文件和我们的知识库内容，进行更深度的推理。
    - **标准兼容**：任何支持 MCP 的 AI Agent（不仅是 Copilot）都可以即刻接入我们的知识库，一次开发，处处可用。

### 多模态图像处理 (Multimodal Image Processing)
本项目采用了经典的 **"Image-to-Text" (图转文)** 策略来处理文档中的图像内容，实现了低成本且高效的多模态检索：
- **图像描述生成 (Captioning)**：利用 LLM 的视觉能力，自动提取文档中插图的核心信息，并生成详细的文字描述（Caption）。
- **统一向量空间**：将生成的图像描述文字直接嵌入到文档文本块（Chunk）中进行向量化。
- **优势**：
    - **架构统一**：无需引入复杂的 CLIP 等多模态向量库，复用现有的纯文本 RAG 检索链路即可实现“搜文字出图”。
    - **语义对齐**：通过 LLM 将图像的视觉特征转化为语义理解，使用户能通过自然语言精准检索到图表、流程图等视觉信息。

### 可观测性、可视化管理与评估体系 (Observability, Visual Management & Evaluation)
针对 RAG 系统常见的“黑盒”问题，本项目致力于让每一次生成过程都**透明可见**且**可量化**，并提供完整的**本地可视化管理平台**：
- **全链路白盒化 (White-box Tracing)**：
    - 记录并可视化 RAG 流水线的每一个中间状态：覆盖 Ingestion（加载→切分→增强→编码→存储）与 Query（查询预处理→Dense/Sparse 召回→融合→重排→响应构建）两条完整链路。
    - 开发者可以清晰看到“系统为什么选了这个文档”以及“Rerank 起了什么作用”，从而精准定位坏 Case。
- **可视化管理平台 (Visual Management Dashboard)**：
    - 基于 Streamlit 的本地 Web 管理面板，提供六大功能页面：
        - **系统总览**：展示当前可插拔组件配置（LLM/Embedding/Splitter/Reranker）与数据资产统计。
        - **数据浏览器**：查看已索引的文档列表、Chunk 详情（原文、metadata 各字段、关联图片），支持搜索过滤。
        - **Ingestion 管理**：通过界面选择文件触发摄取、实时展示各阶段进度、支持删除已摄入文档（跨 4 个存储的协调删除）。
        - **Query 追踪**：查询历史列表，耗时瀑布图，Dense/Sparse 召回对比，Rerank 前后排名变化。
        - **Ingestion 追踪**：摄取历史列表，各阶段耗时与处理详情。
        - **评估面板**：运行评估任务、查看各项指标、历史趋势对比。
    - 所有页面基于 Trace 中的 `method`/`provider` 字段**动态渲染**，更换可插拔组件后 Dashboard 自动适配，无需修改代码。
- **自动化评估闭环 (Automated Evaluation)**：
    - 集成 Ragas 等评估框架（可插拔），为每一次检索和生成计算“体检报告”（如召回率 Hit Rate、准确性 Faithfulness 等指标）。
    - 拒绝“凭感觉”调优，建立基于数据的迭代反馈回路，确保每一次策略调整（如修改 Chunk Size 或更换 Reranker）都有量化的分数支撑。

### 业务可扩展性 (Extensibility for Your Own Projects)
本项目采用**通用化架构设计**，不仅是一个开箱即用的知识问答系统，更是一个可以快速适配各类业务场景的**扩展基座**：

- **Agent 客户端扩展 (Build Your Own Agent Client)**：
    - 本项目的 MCP Server 天然支持被各类 Agent 调用，你可以基于此构建属于自己的 Agent 客户端：
        - **学习 Agent 开发**：通过实现一个调用本 Server 的 Agent，深入理解 Agent 的核心概念（Tool Calling、Chain of Thought、ReAct 模式等）；
        - **定制业务 Agent**：结合你的具体业务需求，开发专属的智能助手（如代码审查 Agent、文档写作 Agent、客服问答 Agent）；
        - **多 Agent 协作**：将本 Server 作为知识检索 Agent，与其他功能 Agent（如代码生成、任务规划）组合，构建复杂的 Multi-Agent 系统。

- **业务场景快速适配 (Adapt to Your Domain)**：
    - **数据层扩展**：只需替换数据源（接入你自己的文档、数据库、API），即可将本系统改造为你的私有知识库；
    - **检索逻辑定制**：基于可插拔架构，轻松调整检索策略以适配不同业务特点（如电商搜索偏重关键词、法律文档偏重语义）；
    - **Prompt 模板定制**：修改系统 Prompt 和输出格式，使其符合你的业务风格与专业术语。

- **学习与实战并重 (Learn While Building)**：
    - 通过扩展本项目，你将同步掌握：
        - **Agent 架构设计**：Function Calling、Tool Use、Memory 管理等核心概念；
        - **LLM 应用工程化**：Prompt Engineering、Token 优化、流式输出等实战技能；
        - **系统集成能力**：如何将 AI 能力嵌入现有业务系统，构建端到端的智能应用。

这种设计让本项目不仅是"学完即弃"的 Demo，而是可以**持续迭代、真正落地**的工程化模板，帮助你将学到的知识转化为实际项目经验。


## 3. 技术选型

### 3.1 RAG 核心流水线设计 

#### 3.1.1 数据摄取流水线 

**目标：** 构建统一、可配置且可观测的数据摄取流水线，覆盖文档加载、格式解析、语义切分、多模态增强、嵌入计算、去重与批量上载到向量存储。该能力应是可重用的库模块，便于在 `ingest.py`、Dashboard 管理面板、离线批处理和测试中调用。

- **自研 Pipeline 框架（设计灵感参考 LlamaIndex 分层思想，但不依赖 LlamaIndex 库）：**
	- 采用自定义抽象接口（`BaseLoader`/`BaseSplitter`/`BaseTransform`/`BaseEmbedding`/`BaseVectorStore`），实现完全可控的可插拔架构。
	- 支持可组合的 Loader -> Splitter -> Transform -> Embed -> Upsert 流程，便于实现可观测的流水线。
	- 与主流 embedding provider 有良好适配，架构中统一使用 Chroma 作为向量存储。


设计要点：
- **明确分层职责**：
  - Loader：负责把原始文件解析为统一的 `Document` 对象（`text` + `metadata`；类型定义集中在 `src/core/types.py`）。**在当前阶段，仅实现 PDF 格式的 Loader。**
		- 统一输出格式采用规范化 Markdown作为 `Document.text`：这样可以更好的配合后面的Splitte（Langchain RCTS RecursiveCharacterTextSplitte）方法产出高质量切块。
		- Loader 同时抽取/补齐基础 metadata（如 `source_path`, `doc_type=pdf`, `page`, `title/heading_outline`, `images` 引用列表等），为定位、回溯与后续 Transform 提供依据。
	- Splitter：基于 Markdown 结构（标题/段落/代码块等）与参数配置把 `Document` 切为若干 Chunk，保留原始位置与上下文引用。
	- Transform：可插入的处理步骤（ImageCaptioning、OCR、code-block normalization、html-to-text cleanup 等），Transform 可以选择把额外信息追加到 chunk.text 或放入 chunk.metadata（推荐默认追加到 text 以保证检索覆盖）。
	- Embed & Upsert：按批次计算 embedding，并上载到向量存储；支持向量 + metadata 上载，并提供幂等 upsert 策略（基于 id/hash）。
	- Dedup & Normalize：在上载前运行向量/文本去重与哈希过滤，避免重复索引。

关键实现要素：

- Loader（统一格式与元数据）
	- **前置去重 (Early Exit / File Integrity Check)**：
		- 机制：在解析文件前，计算原始文件的 SHA256 哈希指纹。
		- 动作：检索 `ingestion_history` 表，若发现相同 Hash 且状态为 `success` 的记录，则认定该文件未发生变更，直接跳过后续所有处理（解析、切分、LLM重写），实现**零成本 (Zero-Cost)** 的增量更新。
		- **存储方案**（初期实现，可插拔）：
			- **默认选择：SQLite**，存储于 `data/db/ingestion_history.db`
			- **表结构**：
				```sql
				CREATE TABLE ingestion_history (
				    file_hash TEXT PRIMARY KEY,
				    file_path TEXT NOT NULL,
				    file_size INTEGER,
				    status TEXT NOT NULL CHECK(status IN ('success', 'failed', 'processing')),
				    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
				    error_msg TEXT,
				    chunk_count INTEGER
				);
				CREATE INDEX idx_status ON ingestion_history(status);
				CREATE INDEX idx_processed_at ON ingestion_history(processed_at);
				```
			- **查询逻辑**：`SELECT status FROM ingestion_history WHERE file_hash = ? AND status = 'success'`
			- **替换路径**：后续可升级为 Redis（分布式缓存）或 PostgreSQL（企业级中心化存储）
	
	> **📌 持久化存储架构统一说明**
	> 
	> 本项目在多个核心模块中采用 **SQLite** 作为轻量级持久化存储方案，避免引入重量级数据库依赖，保持本地优先（Local-First）的设计理念：
	> 
	> | 存储模块 | 数据库文件 | 用途 | 表结构关键字段 |
	> |---------|-----------|------|---------------|
	> | **文件完整性检查** | `data/db/ingestion_history.db` | 记录已处理文件的 SHA256 哈希，实现增量摄取 | `file_hash`, `status`, `processed_at` |
	> | **图片索引映射** | `data/db/image_index.db` | 记录 image_id → 文件路径映射，支持图片检索与引用 | `image_id`, `file_path`, `collection` |
	> | **BM25 索引元数据** | `data/db/bm25/` | 存储倒排索引和 IDF 统计信息（未来可扩展用 SQLite） | 当前使用 pickle，可迁移至 SQLite |
	> 
	> **设计优势**：
	> - **零依赖部署**：无需安装 MySQL/PostgreSQL 等数据库服务，`pip install` 即可运行
	> - **并发安全**：WAL (Write-Ahead Logging) 模式支持多进程安全读写
	> - **持久化保证**：摄取历史和索引映射在进程重启后自动恢复，避免重复计算
	> - **架构一致性**：所有 SQLite 模块遵循相同的初始化、查询与错误处理模式，便于维护与扩展
	> 
	> **升级路径**：当系统规模扩展至分布式场景时，可通过统一的抽象接口将 SQLite 替换为 PostgreSQL 或 Redis，无需修改上层业务逻辑。
	
	- **解析与标准化**：
		- 当前范围：**仅实现 PDF -> canonical Markdown 子集** 的转换。
	- 技术选型（Python PDF -> Markdown）：
		- **首选：MarkItDown**（作为默认 PDF 解析/转换引擎）。优点是直接产出 Markdown 形态文本，便于与后续 `RecursiveCharacterTextSplitter` 的 separators 配合。
	- 输出标准 `Document`：`id|source|text(markdown)|metadata`。metadata 至少包含 `source_path`, `doc_type`, `title/heading_outline`, `page/slide`（如适用）, `images`（图片引用列表）。
	- Loader 不负责切分：只做“格式统一 + 结构抽取 + 引用收集”，确保切分策略可独立迭代与度量。

- Splitter（LangChain 负责切分；独立、可控）
	- **实现方案：使用 LangChain 的 `RecursiveCharacterTextSplitter` 进行切分。**
		- 优势：该方法对 Markdown 文档的结构（标题、段落、列表、代码块）有天然的适配性，能够通过配置语义断点（Separators）实现高质量、语义完整的切块。
	- Splitter 输入：Loader 产出的 Markdown `Document`。
	- Splitter 输出：若干 `Chunk`（或 Document-like chunks），每个 chunk 必须携带稳定的定位信息与来源信息：`source`, `chunk_index`, `start_offset/end_offset`（或等价定位字段）。

- Transform & Enrichment（结构转换与深度增强）
	本阶段是 ETL 管道的核心“智力”环节，负责将 Splitter 产出的非结构化文本块转化为结构化、富语义的智能切片（Smart Chunk）。
	
	- **结构转换 (Structure Transformation)**：将原始的 `String` 类型数据转化为强类型的 `Record/Object`，为下游检索提供字段级支持。
	- **核心增强策略**：
		1. **智能重组 (Smart Chunking & Refinement)**：
			- 策略：利用 LLM 的语义理解能力，对上一阶段“粗切分”的片段进行二次加工。
			- 动作：合并在逻辑上紧密相关但被物理切断的段落，剔除无意义的页眉页脚或乱码（去噪），确保每个 Chunk 是自包含（Self-contained）的语义单元。
		2. **语义元数据注入 (Semantic Metadata Enrichment)**：
			- 策略：在基础元数据（路径、页码）之上，利用 LLM 提取高维语义特征。
			- 产出：为每个 Chunk 自动生成 `Title`（精准小标题）、`Summary`（内容摘要）和 `Tags`（主题标签），并将其注入到 Metadata 字段中，支持后续的混合检索与精确过滤。
		3. **多模态增强 (Multimodal Enrichment / Image Captioning)**：
			- 策略：扫描文档片段中的图像引用，调用 Vision LLM（如 GPT-4o）进行视觉理解。
			- 动作：生成高保真的文本描述（Caption），描述图表逻辑或提取截图文字。
			- 存储：将 Caption 文本“缝合”进 Chunk 的正文或 Metadata 中，打通模态隔阂，实现“搜文出图”。
	- **工程特性**：Transform 步骤设计为原子化与幂等操作，支持针对特定 Chunk 的独立重试与增量更新，避免因 LLM 调用失败导致整个文档处理中断。
	
- **Embedding (双路向量化)**
	- **差量计算 (Incremental Embedding / Cost Optimization)**：
	  - 策略：在调用昂贵的 Embedding API 之前，计算 Chunk 的内容哈希（Content Hash）。仅针对数据库中不存在的新内容哈希执行向量化计算，对于文件名变更但内容未变的片段，直接复用已有向量，显著降低 API 调用成本。
	
	  > **文件级去重是“粗筛”，快速跳过完全不变的文件；Chunk 级去重是“细筛”，在文件部分变化时最大程度复用已有向量。两者不重复，而是分层协同，实现更精细的成本优化。**
	
	- **核心策略**：为了支持高精度的混合检索（Hybrid Search），系统对每个 Chunk 并行执行双路编码计算。
	  - **Dense Embeddings（语义向量）**：调用 Embedding 模型（如 OpenAI text-embedding-3 或 BGE）生成高维浮点向量，捕捉文本的深层语义关联，解决“词不同意同”的检索难题。
	  - **Sparse Embeddings（稀疏向量）**：利用 BM25 编码器或 SPLADE 模型生成稀疏向量（Keyword Weights），捕捉精确的关键词匹配信息，解决专有名词查找问题。
	
	- **批处理优化**：所有计算均采用 `batch_size` 驱动的批处理模式，最大化 CPU 利用率并减少网络 RTT。
	
- **Upsert & Storage (索引存储)**
	- **存储后端**：统一使用向量数据库（如 Chroma/Qdrant）作为存储引擎，同时持久化存储 Dense Vector、Sparse Vector 以及 Transform 阶段生成的富 Metadata。
	- **All-in-One 存储策略**：执行原子化存储，每条记录同时包含：
		1. **Index Data**: 用于计算相似度的 Dense Vector 和 Sparse Vector。
		2. **Payload Data**: 完整的 Chunk 原始文本 (Content) 及 Metadata。
		**机制优势**：确保检索命中 ID 后能立即取回对应的正文内容，无需额外的查库操作 (Lookup)，保障了 Retrieve 阶段的毫秒级响应。
	
- **幂等性设计 (Idempotency)**：
		- 为每个 Chunk 生成全局唯一的 `chunk_id`，生成算法采用确定的哈希组合：`hash(source_path + section_path + content_hash)`。
		- 写入时采用 "Upsert"（更新或插入）语义，确保同一文档即使被多次处理，数据库中也永远只有一份最新副本，彻底避免重复索引问题。
	
	- **原子性保证**：以 Batch 为单位进行事务性写入，确保索引状态的一致性。
	
- **文档生命周期管理 (Document Lifecycle Management)**

	为支持 Dashboard 管理面板中的文档浏览与删除功能，Ingestion 层需要提供完整的文档生命周期管理能力：

	- **DocumentManager（文档管理器）**：独立于 Pipeline 的文档管理模块（`src/ingestion/document_manager.py`），负责跨存储的协调操作：
		
		- `list_documents(collection?) -> List[DocumentInfo]`：列出已摄入文档及其统计信息（chunk 数、图片数、摄入时间）。
		- `get_document_detail(doc_id) -> DocumentDetail`：获取单个文档的详细信息（所有 chunk 内容、metadata、关联图片）。
		- `delete_document(source_path, collection) -> DeleteResult`：协调删除跨 4 个存储的关联数据，
			1. **Chroma** — 按 `metadata.source` 删除所有 chunk 向量
			2. **BM25 Indexer** — 移除对应文档的倒排索引条目
			3. **ImageStorage** — 删除该文档关联的所有图片文件
			4. **FileIntegrity** — 移除处理记录，使文件可重新摄入
		- `get_collection_stats(collection?) -> CollectionStats`：返回集合级统计（文档数、chunk 数、存储大小等）。
		
	- **Pipeline 进度回调 (Progress Callback)**：在 `IngestionPipeline.run()` 方法中新增可选 `on_progress` 参数：
		
		```python
		def run(self, source_path: str, collection: str = "default",
		        on_progress: Callable[[str, int, int], None] | None = None) -> IngestionResult:
		```
		- 回调签名：`on_progress(stage_name: str, current: int, total: int)`
		- 各阶段（load / split / transform / embed / upsert）在处理每个 batch 时调用回调，Dashboard 据此展示实时进度条。
		- `on_progress` 为 `None` 时行为与当前完全一致，不影响 CLI 和测试场景。
		
	- **存储层接口扩展**：为支持 DocumentManager 的删除操作，需扩展以下存储接口：
		
		- `BaseVectorStore` 新增 `delete_by_metadata(filter: dict) -> int` — 按 metadata 条件批量删除
		- `BM25Indexer` 新增 `remove_document(source: str) -> None` — 移除指定文档的索引条目
		- `FileIntegrityChecker` 新增 `remove_record(file_hash: str) -> None` 和 `list_processed() -> List[dict]`

#### 3.1.2 检索流水线


本模块实现核心的 RAG 检索引擎，采用 **“多阶段过滤 (Multi-stage Filtering)”** 架构，负责接收已消歧的独立查询（Standalone Query），并精准召回 Top-K 最相关片段。

- **Query Processing (查询预处理)**
	- **核心假设**：输入 Query 已由上游（Client/MCP Host）完成会话上下文补全（De-referencing），不仅如此，还进行了指代消歧。
	- **查询转换 (Transformation) 与扩张策略 (Expansion Strategy)**：
		- **Keyword Extraction**：利用 NLP 工具提取 Query 中的关键实体与动词（去停用词），生成用于稀疏检索的 Token 列表。
		- **Query Expansion **：
			- 系统需要支持 **两类可选的 Query Expansion 能力**，并统一纳入“服务端检索编排 Orchestration“：
				1. **Synonym/Alias Expansion（同义词/别名/缩写扩展）**
				2. **Logical Decomposition（逻辑拆解）**：将一个复杂问题拆为多个有检索价值的子查询（例如先问 A，再问 B，或并列拆为 A/B/C）
			- **策略选择机制**：是否开启 Query Expansion、采用哪一种 Expansion、以及是否退化为“不扩展”，均通过配置驱动，并由 LLM 在运行时做判定；LLM 输出必须是严格结构化结果（例如 JSON），避免自由文本导致编排不稳定。
			- **Synonym/Alias Expansion 路径**：
				- 默认策略采用“**扩展融入稀疏检索、稠密检索保持单次**”以控制成本与复杂度。
				- **Sparse Route (BM25)**：将“关键词 + 同义词/别名”合并为一个查询表达式（逻辑上按 `OR` 扩展），**只执行一次稀疏检索**。原始关键词可赋予更高权重以抑制语义漂移。
				- **Dense Route (Embedding)**：使用原始 query（或轻度改写后的语义 query）生成 embedding，**只执行一次稠密检索**；默认不为每个同义词单独触发额外的向量检索请求。
			- **Logical Decomposition 路径**：
				- Expansion Planner 先将原始 Query 规划为一个有序的子查询列表 `sub_queries`，每个子查询都保留独立的检索意图说明。
				- 子查询默认走**多 Query 并行检索 + 聚合合并**路径；当 Planner 显式声明依赖顺序时，允许按阶段串行执行，但本期以“可并行子查询”为主。
				- 子查询检索完成后，由服务端统一做结果去重、融合、重排与响应构建，对 MCP Client 仍表现为一次 `query_knowledge_hub` 调用。

- **Query Orchestration (查询编排)**
	- **能力目标**：在不改变 MCP Tool 入口语义的前提下，为单次用户查询增加“规划 -> 检索 -> 合并 -> 精排”的服务端编排能力。
	- **编排模式**：
		1. **Direct Mode**：不做 Expansion，直接进入当前 Hybrid Search。
		2. **Synonym Expansion Mode**：生成扩展词，仍保持一次 Dense + 一次 Sparse 的单 Query 检索。
		3. **Decomposition Mode**：生成多个子查询，对各子查询执行并行 Hybrid Search，再做统一聚合。
	- **Multi-Query Parallel Merge（多 Query 并行 + 合并）**：
		- 当 Logical Decomposition 产出多个 `sub_queries` 时，系统需要支持对多个子查询并行执行检索。
		- 每个子查询内部仍然保持原有的 Dense/Sparse 双路召回、Fusion、Metadata Filtering、Rerank 契约，避免引入第二套检索实现。
		- 并行结果合并时，至少需要经过以下步骤：
			1. **Per-Query Top-N 截断**：每个子查询先截断为可控候选集；
			2. **Cross-Query Dedup**：基于 `chunk_id` 去重；
			3. **Merge Fusion**：对多子查询结果做统一融合（默认推荐 RRF 的多列表扩展）；
			4. **Final Rerank**：在合并后的候选集上执行一次全局重排，确保最终 Top-K 与原始用户问题对齐。
	- **失败回退 (Fallback)**：
		- 当 Expansion Planner 不可用、输出非法、超时或判断“不需要扩展”时，必须无损回退到 Direct Mode。
		- 当某些子查询检索失败时，不中断整体请求；保留成功子查询的结果并在 Trace 中标记降级原因。
		- 当 Multi-Query Merge 阶段异常时，允许回退到“主子查询结果优先”的安全默认策略。

- **Hybrid Search Execution (双路混合检索)**
	- **并行召回 (Parallel Execution)**：
		- **Dense Route**：计算 Query Embedding -> 检索向量库（Cosine Similarity）-> 返回 Top-N 语义候选。
		- **Sparse Route**：使用 BM25 算法 -> 检索倒排索引 -> 返回 Top-N 关键词候选。
	- **结果融合 (Fusion)**：
		- 采用 **RRF (Reciprocal Rank Fusion)** 算法，不依赖各路分数的绝对值，而是基于排名的倒数进行加权融合。
		- 公式策略：`Score = 1 / (k + Rank_Dense) + 1 / (k + Rank_Sparse)`，平滑因单一模态缺陷导致的漏召回。

- **Filtering & Reranking (精确过滤与重排)**
	- **Metadata Filtering Strategy (通用过滤策略)**：
		- **原则：先解析、能前置则前置、无法前置则后置兜底。**
		- Query Processing 阶段应将结构化约束解析为通用 `filters`（例如 `collection`/`doc_type`/`language`/`time_range`/`access_level` 等）。
		- 若底层索引支持且属于硬约束（Hard Filter），则在 Dense/Sparse 检索阶段做 Pre-filter 以缩小候选集、降低成本。
		- 无法前置的过滤（索引不支持或字段缺失/质量不稳）在 Rerank 前统一做 Post-filter 作为 safety net；对缺失字段默认采取“宽松包含”(missing->include) 以避免误杀召回。
		- 软偏好（Soft Preference，例如“更近期更好”）不应硬过滤，而应作为排序信号在融合/重排阶段加权。
	- **Rerank Backend (可插拔精排后端)**：
		- **目标**：在 Top-M 候选上进行高精度排序/过滤；该模块必须可关闭，并提供稳定回退策略。
		- **后端选项**：
			1. **None (关闭精排)**：直接返回融合后的 Top-K（RRF 排名作为最终结果）。
			2. **Cross-Encoder Rerank (本地/托管模型)**：输入为 `[Query, Chunk]` 对，输出相关性分数并排序；适合稳定、结构化输出。CPU 环境下建议默认仅对较小的 Top-M 执行（例如 M=10~30），并提供超时回退。
			3. **LLM Rerank (可选)**：使用 LLM 对候选集排序/选择；适合需要更强指令理解或无本地模型环境时。为控制成本与稳定性，候选数应更小（例如 M<=20），并要求输出严格结构化格式（如 JSON 的 ranked ids）。
		- **默认与回退 (Fallback)**：
			- 默认策略面向通用框架与 CPU 环境：优先保证“可用与可控”，Cross-Encoder/LLM 均为可选增强。
			- 当精排不可用/超时/失败时，必须回退到融合阶段的排序（RRF Top-K），确保系统可用性与结果稳定性。

### 3.2 MCP 服务设计 (MCP Service Design)

**目标：** 设计并实现一个符合 Model Context Protocol (MCP) 规范的 Server，使其能够作为知识上下文提供者，无缝对接主流 MCP Clients（如 GitHub Copilot、Claude Desktop 等），让用户通过现有 AI 助手即可查询私有知识库。

#### 3.2.1 核心设计理念

- **协议优先 (Protocol-First)**：严格遵循 MCP 官方规范（JSON-RPC 2.0），确保与任何合规 Client 的互操作性。
- **开箱即用 (Zero-Config for Clients)**：Client 端无需任何特殊配置，只需在配置文件中添加 Server 连接信息即可使用全部功能。
- **引用透明 (Citation Transparency)**：所有检索结果必须携带完整的来源信息，支持 Client 端展示"回答依据"，增强用户对 AI 输出的信任。
- **多模态友好 (Multimodal-Ready)**：返回格式应支持文本与图像等多种内容类型，为未来的富媒体展示预留扩展空间。

#### 3.2.2 传输协议：Stdio 本地通信

本项目采用 **Stdio Transport** 作为唯一通信模式。

- **工作方式**：Client（VS Code Copilot、Claude Desktop）以子进程方式启动我们的 Server，双方通过标准输入/输出交换 JSON-RPC 消息。
- **选型理由**：
	- **零配置**：无需网络端口、无需鉴权，用户只需在 Client 配置文件中指定启动命令即可使用。
	- **隐私安全**：数据不经过网络，天然适合处理私有知识库与敏感业务数据。
	- **契合定位**：Stdio 完美适配开发者本地工作流，满足私有知识管理与快速原型验证需求。
- **实现约束**：
	- `stdout` 仅输出合法 MCP 消息，禁止混入任何日志或调试信息。
	- 日志统一输出至 `stderr`，避免污染通信通道。

#### 3.2.3 SDK 与实现库选型

- **首选：Python 官方 MCP SDK (`mcp`)**
	- **优势**：
		- 官方维护，与协议规范同步更新，保证最新特性支持（如 `outputSchema`、`annotations` 等）。
		- 提供 `@server.tool()` 等装饰器，声明式定义 Tools/Resources/Prompts，代码简洁。
		- 内置 Stdio 与 HTTP Transport 支持，无需手动处理 JSON-RPC 序列化与生命周期管理。
	- **适用**：本项目的默认实现方案。

- **备选：FastAPI + 自定义协议层**
	- **场景**：需要深度定制 HTTP 行为（如自定义中间件、复杂鉴权流程）或希望学习 MCP 协议底层细节时可考虑。
	- **权衡**：开发成本更高，需自行实现能力协商 (Capability Negotiation)、错误码映射等，且需持续跟进协议版本更新。

- **协议版本**：跟踪 MCP 最新稳定版本（如 `2025-06-18`），在 `initialize` 阶段进行版本协商，确保 Client/Server 兼容性。

#### 3.2.4 对外暴露的工具函数设计 (Tools Design)

Server 通过 `tools/list` 向 Client 注册可调用的工具函数。工具设计应遵循"单一职责、参数明确、输出丰富"原则。

- **核心工具集**：

| 工具名称 | 功能描述 | 典型输入参数 | 输出特点 |
|---------|---------|-------------|---------|
| `query_knowledge_hub` | 主检索入口，执行混合检索 + Rerank，返回最相关片段 | `query: string`, `top_k?: int`, `collection?: string` | 返回带引用的结构化结果 |
| `list_collections` | 列举知识库中可用的文档集合 | 无 | 集合名称、描述、文档数量 |
| `get_document_summary` | 获取指定文档的摘要与元信息 | `doc_id: string` | 标题、摘要、创建时间、标签 |

- **扩展工具（Agentic 演进方向）**：
	- `search_by_keyword` / `search_by_semantic`：拆分独立的检索策略，供 Agent 自主选择。
	- `verify_answer`：事实核查工具，检测生成内容是否有依据支撑。
	- `list_document_sections`：浏览文档目录结构，支持多步导航式检索。

#### 3.2.5 返回内容与引用透明设计 (Response & Citation Design)

MCP 协议的 Tool 返回格式支持多种内容类型（`content` 数组），本项目将充分利用这一特性实现"可溯源"的回答：

- **结构化引用设计**：
	- 每个检索结果片段应包含完整的定位信息：`source_file`（文件名/路径）、`page`（页码，如适用）、`chunk_id`（片段标识）、`score`（相关性分数）。
	- 推荐在返回的 `structuredContent` 中采用统一的 Citation 格式：
		```
		{
		  "answer": "...",
		  "citations": [
		    { "id": 1, "source": "xxx.pdf", "page": 5, "text": "原文片段...", "score": 0.92 },
		    ...
		  ]
		}
		```
	- 同时在 `content` 数组中以 Markdown 格式呈现人类可读的带引用回答（`[1]` 标注），保证 Client 无论是否解析结构化内容都能展示引用。

- **多模态内容返回**：
	- **文本内容 (TextContent)**：默认返回类型，Markdown 格式，支持代码块、列表等富文本。
	- **图像内容 (ImageContent)**：当检索结果关联图像时，Server 读取本地图片文件并编码为 Base64 返回。
		- **格式**：`{ "type": "image", "data": "<base64>", "mimeType": "image/png" }`
		- **工作流程**：数据摄取阶段存储图片本地路径 → 检索命中后 Server 动态读取 → 编码为 Base64 → 嵌入返回消息。
		- **Client 兼容性**：图像展示能力取决于 Client 实现，GitHub Copilot 可能降级处理，Claude Desktop 支持完整渲染。Server 端统一返回 Base64 格式，由 Client 决定如何渲染。

- **Client 适配策略**：
	- **GitHub Copilot (VS Code)**：当前对 MCP 的支持集中在 Tools 调用，返回的 `content` 中的文本会展示给用户。建议以清晰的 Markdown 文本（含引用标注）为主，图像作为补充。
	- **Claude Desktop**：对 MCP Tools/Resources 有完整支持，图像与资源链接可直接渲染。可更激进地使用多模态返回。
	- **通用兼容原则**：始终在 `content` 数组第一项提供纯文本/Markdown 版本的答案，确保最低兼容性；将结构化数据、图像等放在后续项或 `structuredContent` 中，供高级 Client 解析。

### 3.3 可插拔架构设计 (Pluggable Architecture Design)

**目标：** 定义清晰的抽象层与接口契约，使 RAG 链路的每个核心组件都能够独立替换与升级，避免技术锁定，支持低成本的 A/B 测试与环境迁移。

> **术语说明**：本节中的"提供者 (Provider)"、"实现 (Implementation)"指的是完成某项功能的**具体技术方案**，而非传统 Web 架构中的"后端服务器"。例如，LLM 提供者可以是远程的 Azure OpenAI API，也可以是本地运行的 Ollama；向量存储可以是本地嵌入式的 Chroma，也可以是云端托管的 Pinecone。本项目作为本地 MCP Server，通过统一接口对接这些不同的提供者，实现灵活切换。

#### 3.3.1 设计原则

- **接口隔离 (Interface Segregation)**：为每类组件定义最小化的抽象接口，上层业务逻辑仅依赖接口而非具体实现。
- **配置驱动 (Configuration-Driven)**：通过统一配置文件（如 `settings.yaml`）指定各组件的具体后端，代码无需修改即可切换实现。
- **工厂模式 (Factory Pattern)**：使用工厂函数根据配置动态实例化对应的实现类，实现"一处配置，处处生效"。
- **优雅降级 (Graceful Fallback)**：当首选后端不可用时，系统应自动回退到备选方案或安全默认值，保障可用性。

**通用结构示意（适用于 3.3.2 / 3.3.3 / 3.3.4 等可插拔组件）**：

```
业务代码
  │
  ▼
<Component>Factory.get_xxx()  ← 读取配置，决定用哪个实现
  │
  ├─→ ImplementationA()
  ├─→ ImplementationB()  
  └─→ ImplementationC()
      │
      ▼
    都实现了统一的抽象接口
```

#### 3.3.2 LLM 与 Embedding 提供者抽象

这是可插拔设计的核心环节，因为模型提供者的选择直接影响成本、性能与隐私合规。

代码里没有直接写死 OpenAI 或 Azure，而是先定义 BaseLLM 、 BaseEmbedding 、 BaseVisionLLM 这些统一 llm 接口，再由工厂读取 settings.yaml 的 provider 字段路由到具体实现。上层模块像 ChunkRefiner 、 MetadataEnricher 、 ImageCaptioner 、 DenseEncoder 都只依赖抽象接口，因此切换 Provider 时只改 settings 的配置，不改业务代码。

* 先定义 **llm 统一抽象接口**，真正封装了 OpenAI 的请求参数、认证方式和 chat() 调用逻辑

  - LLM 抽象接口 base_llm.py

    - Message、 ChatResponse、 BaseLLM.chat(messages, ...)
    - 这三者是并列的，Message、ChatResponse 是包中共享的统一 API

  - Embedding 抽象接口 base_embedding.py

    - BaseEmbedding.embed(texts, ...)、 get_dimension()

  - Vision LLM 抽象接口 base_vision_llm.py

    针对图像描述生成（Image Captioning）需求，系统扩展了 `BaseVisionLLM` 接口，支持文本+图片的多模态输入

    - ImageInput、 BaseVisionLLM.chat_with_image(text, image, ...)

* 又由于**配置入口 settings.yaml** 定义了 LLMSettings、 EmbeddingSettings、 VisionLLMSettings、 Settings

- 以及 **LLM Provider 注册点 init.py**

  - 把具体 Provider 实现类 import 进来，并调用 LLMFactory.register_provider(...) 注册到了工厂

  * 通过 __all__ 将 libs/llm 包的所有接口暴露给外部使用，只要 import 这个包，就可以这样调用：

    ```python
    from src.libs.llm import BaseLLM, Message, ChatResponse, LLMFactory
    ```

    - 简化 import 路径
    - 统一包入口
    - 隐藏内部文件结构

- 于是**工厂**就能根据 settings.llm.provider 选择对应 Provider 类并实例化，对上层暴露统一入口 XxxFactory.create(settings)

  - LLM 工厂 llm_factory.py
    - 文本模型： LLMFactory.create(settings)
    - 视觉模型： LLMFactory.create_vision_llm(settings)
  - Embedding 工厂 embedding_factory.py
    - EmbeddingFactory.create(settings)

- **具体 Provider 实现类**，继承统一抽象接口

  - LLM：
    - openai_llm.py
    - azure_llm.py
    - deepseek_llm.py
    - ollama_llm.py
  - Vision：
    - azure_vision_llm.py
    - openai_vision_llm.py
  - Embedding：
    - openai_embedding.py
    - azure_embedding.py
    - ollama_embedding.py

| 提供者类型               | 典型场景                           | `settings.yaml` 配置切换点                                  |
| ------------------------ | ---------------------------------- | ----------------------------------------------------------- |
| **Azure OpenAI**         | 企业合规、私有云部署、区域数据驻留 | `provider: azure`, `azure_endpoint`, `api_key`, `deployment_name` |
| **OpenAI 原生**          | 通用开发、最新模型尝鲜             | `provider: openai`, `api_key`, `model`                      |
| **DeepSeek / 其他云端**  | 成本优化、特定语言优化             | `provider: deepseek`, `api_key`, `model`                    |
| **Ollama / vLLM (本地)** | 完全离线、隐私敏感、无 API 成本    | `provider: ollama`, `base_url`, `model`                     |

**技术选型建议**：

- 对于其他 Provider，可通过 **OpenAI-Compatible 模式**接入（设置自定义 `base_url`），或实现 `BaseLLM` 接口并在工厂中注册。

- 对于企业级需求，可在其基础上增加统一的 **重试、限流、日志** 中间层，提升生产可靠性，但本项目暂不实现，这里仅提供思路。
- **Vision LLM 扩展**：针对图像描述生成（Image Captioning）需求，系统扩展了 `BaseVisionLLM` 接口，支持文本+图片的多模态输入。

#### 3.3.3 摄入/检索策略抽象

摄入/检索层的可插拔性决定了系统在不同数据规模与查询模式下的适应能力。

与 3.3.2 节的 LLM 抽象类似，检索层各组件的可插拔性同样依赖两层设计：

1. **自研的统一抽象接口**：本项目为加载器（`base_loader.py`）、分块（`base_splitter.py`）、Embedding（`base_embedding.py`）、向量数据库（`base_vector_store.py`）、重排序（`base_reranker.py`）等核心组件定义了统一的抽象基类，不同实现只需遵循相同接口即可无缝替换。

2. **工厂函数路由**：每个抽象层配套工厂函数（如 `embedding_factory.py`、`splitter_factory.py`），利用 `init.py` 进行具体实现类的注册，并根据 `settings.yaml` 中的配置字段自动实例化对应实现，实现"改配置不改代码"的切换体验。

下面分别说明各组件如何应用这一模式：

**1. 分块策略 (Chunking Strategy)**

分块是 Ingestion Pipeline 的核心环节之一，决定了文档如何被切分为适合检索的语义单元。本项目的 Splitter 层采用可插拔设计（BaseSplitter 抽象接口 + SplitterFactory 工厂），不同分块实现只需遵循相同接口即可无缝替换。

> **当前实现说明**：目前系统使用 LangChain RecursiveCharacterTextSplitter。架构设计上预留了切换能力，如需切换为 SentenceSplitter、SemanticSplitter 或自定义切分器，只需实现 BaseSplitter 接口并在配置中指定即可。

---

**2. 向量数据库 (Vector Store)**

本项目自定义了统一的 BaseVectorStore 抽象接口，暴露 .add()、.query()、.delete() 等方法。所有向量数据库后端（Chroma、Qdrant、Pinecone 等）只需实现该接口即可插拔替换，通过 VectorStoreFactory 根据配置自动选择具体实现。

本项目选用 **Chroma** 作为向量数据库。相比 Qdrant、Milvus、Weaviate 等需要 Docker 容器或分布式架构支撑的方案，Chroma 采用嵌入式设计，`pip install chromadb` 即可使用，无需额外部署数据库服务，非常适合本地开发与快速原型验证。同时 ChromaStore 适配器（src/libs/vector_store/chroma_store.py），与 Pipeline 无缝集成。

> **当前实现说明**：目前系统仅实现了 Chroma 后端。虽然架构设计上预留了工厂模式以支持未来扩展，但当前版本尚未实现其他向量数据库的适配器。

---

**3. 向量编码策略 (Embedding Strategy)**

向量编码是 Ingestion Pipeline 的关键环节，决定了 Chunk 如何被转换为可检索的向量表示。本项目自定义了 BaseEmbedding 抽象接口（src/libs/embedding/base_embedding.py），支持不同 Embedding 模型的可插拔替换。

常见的编码策略包括：
- **纯稠密编码（Dense Only）**：仅生成语义向量，适合通用场景。
- **纯稀疏编码（Sparse Only）**：仅生成关键词权重向量，适合精确匹配场景。
- **双路编码（Dense + Sparse）**：同时生成稠密向量和稀疏向量，为混合检索提供数据基础。

本项目当前采用 **双路编码（Dense + Sparse）** 策略：
- **Dense Embeddings（语义向量）**：调用 Embedding 模型（如 OpenAI text-embedding-3）生成高维浮点向量，捕捉文本的深层语义关联。
- **Sparse Embeddings（稀疏向量）**：利用 BM25 编码器生成稀疏向量（Keyword Weights），捕捉精确的关键词匹配信息。

存储时，Dense Vector 和 Sparse Vector 与 Chunk 原文、Metadata 一起原子化写入向量数据库，确保检索时可同时利用两种向量。

> **当前实现说明**：目前系统实现了 Dense + Sparse 双路编码。架构设计上预留了切换能力，如需使用其他 Embedding 模型（如 BGE、Ollama 本地模型）或调整编码策略，可在 Pipeline 中替换相应组件。

---

**4. 召回策略 (Retrieval Strategy)**

召回策略决定了查询阶段如何从知识库中检索相关内容。基于 Ingestion 阶段存储的向量类型，可采用不同的召回方案：
- **纯稠密召回（Dense Only）**：仅使用语义向量进行相似度匹配。
- **纯稀疏召回（Sparse Only）**：仅使用 BM25 进行关键词匹配。
- **混合召回（Hybrid）**：并行执行稠密和稀疏两路召回，再通过融合算法合并结果。
- **混合召回 + 精排（Hybrid + Rerank）**：在混合召回基础上，增加精排步骤进一步提升相关性。

本项目当前采用 **混合召回 + 精排（Hybrid + Rerank）** 策略：
- **稠密召回（Dense Route）**：计算 Query Embedding，在向量库中进行 Cosine Similarity 检索，返回 Top-N 语义候选。
- **稀疏召回（Sparse Route）**：使用 BM25 算法检索倒排索引，返回 Top-N 关键词候选。
- **融合（Fusion）**：使用 RRF (Reciprocal Rank Fusion) 算法将两路结果合并排序。
- **精排（Rerank）**：对融合后的候选集进行重排序，支持 None / Cross-Encoder / LLM Rerank 三种模式。

> **当前实现说明**：目前系统实现了 Hybrid + Rerank 策略。架构设计上预留了策略切换能力，如需使用纯稠密或纯稀疏召回，可通过配置切换；融合算法和 Reranker 同样支持替换。

#### 3.3.4 评估框架抽象

评估体系的可插拔性确保团队可以根据业务目标灵活选择或组合不同的质量度量维度。

- **设计思路**：
	- 定义统一的 `Evaluator` 接口，暴露 `evaluate(query, retrieved_chunks, generated_answer, ground_truth) -> metrics` 方法。
	- 各评估框架实现该接口，输出标准化的指标字典。

- **可选评估框架**：

| 框架 | 特点 | 适用场景 |
|-----|------|---------|
| **Ragas** | RAG 专用、指标丰富（Faithfulness, Answer Relevancy, Context Precision 等） | 全面评估 RAG 质量、学术对比 |
| **自定义指标** | Hit Rate, MRR 等轻量、确定性指标 | 快速回归测试、上线前 Sanity Check |
| **组合评估器** | 组合多个 Evaluator 并汇总指标 | 需要同时观察检索指标与 LLM-as-Judge 指标 |

- **组合与扩展**：
	- 评估模块支持两种后端：`custom`（轻量离线指标 hit_rate/mrr）和 `ragas`（LLM-as-Judge 指标 faithfullness/answer_relevancy/context_precision）。
	- 配置入口为 `evaluation.provider` + `evaluation.metrics`，通过 `EvaluatorFactory` 自动实例化对应后端。

#### 3.3.5 配置管理与切换流程

- **配置文件结构示例** (`config/settings.yaml`)：
	
	```yaml
	llm:
	  provider: azure  # azure | openai | ollama | deepseek
	  model: gpt-4o
	  # provider-specific configs...
	
	embedding:
	  provider: openai
	  model: text-embedding-3-small
	
	vector_store:
	  backend: chroma  # chroma | qdrant | pinecone
	
	retrieval:
	  sparse_backend: bm25  # bm25 | elasticsearch
	  fusion_algorithm: rrf  # rrf | weighted_sum
	  rerank_backend: cross_encoder  # none | cross_encoder | llm
	  query_orchestration:
	    enabled: false
	    planner_provider: llm  # llm | rules
	    mode: auto  # off | auto | synonym | decomposition
	    max_sub_queries: 4
	    parallel_sub_queries: true
	    merge_fusion: rrf  # rrf | weighted_rrf
	    fallback_to_direct: true
	    planner_timeout_seconds: 8
	
	evaluation:
	  enabled: true
	  provider: custom  # custom | ragas
	  metrics: [hit_rate, mrr]
	
	dashboard:
	  enabled: true
	  port: 8501
	  traces_dir: ./logs
	```
	
	- **当前实现说明**：
		- `provider: custom` 为轻量、确定性评估，不依赖云端 API，支持 `hit_rate` / `mrr`。
		- `provider: ragas` 用于 LLM-as-Judge 评估，支持 `faithfulness` / `answer_relevancy` / `context_precision`，需要额外安装 `ragas` 依赖，并依赖可用的 LLM/Embedding API。
		- 按当前实现，`RagasEvaluator` 仅支持基于 `openai` / `azure` 风格的 LLM 与 Embedding 配置；若主链路使用 `deepseek` / `ollama` 等 provider，则不应直接将 `evaluation.provider` 切换为 `ragas`。
		- `retrieval.query_orchestration` 是本次扩展新增的可选配置块，用于控制 Query Expansion、Logical Decomposition 与多 Query 并行合并能力。默认应保持关闭，以保证对现有查询链路零影响。
	
- **切换流程**：

	1. 修改 `settings.yaml` 中对应组件的 `backend` / `provider` 字段。
	2. 确保新后端的依赖已安装、凭据已配置。
	3. 重启服务，工厂函数自动加载新实现，无需修改业务代码。

### 3.4 可观测性与可视化管理平台设计 (Observability & Visual Management Platform Design)

**目标：** 针对 RAG 系统常见的"黑盒"问题，设计全链路可观测的追踪体系与完整的可视化管理平台。覆盖 **Ingestion（摄取链路）** 与 **Query（查询链路）** 两条完整流水线的追踪记录，同时提供数据浏览、文档管理、组件概览等管理功能，使整个系统**透明可见**、**可管理**且**可量化**。

#### 3.4.1 设计理念

- **双链路全覆盖追踪 (Dual-Pipeline Tracing)**：
    - **Ingestion Trace**：以 `trace_id` 为核心，记录一次摄取从文件加载到存储完成的全过程（load → split → transform → embed → upsert），包含各阶段耗时、处理的 chunk 数量、跳过/失败详情。
    - **Query Trace**：以 `trace_id` 为核心，记录一次查询从 Query 输入到 Response 输出的全过程（query_processing → dense → sparse → fusion → rerank），包含各阶段候选数量、分数分布与耗时。
- **透明可回溯 (Transparent & Traceable)**：每个阶段的中间状态都被记录，开发者可以清晰看到"系统为什么召回了这些文档"、"Rerank 前后排名如何变化"，从而精准定位问题。
- **低侵入性 (Low Intrusiveness)**：追踪逻辑与业务逻辑解耦，通过 `TraceContext` 显式调用模式注入，避免污染核心代码。
- **轻量本地化 (Lightweight & Local)**：采用结构化日志 + 本地 Dashboard 的方案，零外部依赖，开箱即用。
- **动态组件感知 (Dynamic Component Awareness)**：Dashboard 基于 Trace 中的 `method`/`provider`/`details` 字段动态渲染，更换可插拔组件后自动适配展示内容，无需修改 Dashboard 代码。


#### 3.4.2 追踪数据结构

系统定义两类 Trace 记录，分别覆盖查询与摄取两条链路：

**A. Query Trace（查询追踪）**

每次查询请求生成唯一的 `trace_id`，记录从 Query 输入到 Response 输出的全过程：

**基础信息**：

- `trace_id`：请求唯一标识
- `trace_type`：`"query"`
- `timestamp`：请求时间戳
- `user_query`：用户原始查询
- `collection`：检索的知识库集合

**各阶段详情 (Stages)**：

| 阶段 | 记录内容 |
|-----|---------|
| **Query Processing** | 原始 Query、改写后 Query（若有）、提取的关键词、method、耗时 |
| **Query Orchestration** | Expansion 是否启用、Planner 决策（direct/synonym/decomposition）、子查询列表、回退原因、耗时 |
| **Dense Retrieval** | 返回的 Top-N 候选及相似度分数、provider、耗时 |
| **Sparse Retrieval** | 返回的 Top-N 候选及 BM25 分数、method、耗时 |
| **Fusion** | 融合后的统一排名、algorithm、耗时 |
| **Rerank** | 重排后的最终排名及分数、backend、是否触发 Fallback、耗时 |

**汇总指标**：
- `total_latency`：端到端总耗时
- `top_k_results`：最终返回的 Top-K 文档 ID
- `error`：异常信息（若有）

**评估指标 (Evaluation Metrics)**：
- `context_relevance`：召回文档与 Query 的相关性分数
- `answer_faithfulness`：生成答案与召回文档的一致性分数（若有生成环节）

**B. Ingestion Trace（摄取追踪）**

每次文档摄取生成唯一的 `trace_id`，记录从文件加载到存储完成的全过程：

**基础信息**：
- `trace_id`：摄取唯一标识
- `trace_type`：`"ingestion"`
- `timestamp`：摄取开始时间
- `source_path`：源文件路径
- `collection`：目标集合名称

**各阶段详情 (Stages)**：

| 阶段 | 记录内容 |
|-----|---------|
| **Load** | 文件大小、解析器（method: markitdown）、提取的图片数、耗时 |
| **Split** | splitter 类型（method）、产出 chunk 数、平均 chunk 长度、耗时 |
| **Transform** | 各 transform 名称与处理详情（refined/enriched/captioned 数量）、LLM provider、耗时 |
| **Embed** | embedding provider、batch 数、向量维度、dense + sparse 编码耗时 |
| **Upsert** | 存储后端（method: chroma）、upsert 数量、BM25 索引更新、图片存储、耗时 |

**汇总指标**：
- `total_latency`：端到端总耗时
- `total_chunks`：最终存储的 chunk 数量
- `total_images`：处理的图片数量
- `skipped`：跳过的文件/chunk 数（已存在、未变更等）
- `error`：异常信息（若有）


#### 3.4.3 技术方案：结构化日志 + 本地 Web Dashboard

本项目采用 **"结构化日志 + 本地 Web Dashboard"** 作为可观测性的实现方案。

**选型理由**：
- **零外部依赖**：不依赖 LangSmith、LangFuse 等第三方平台，无需网络连接与账号注册，完全本地化运行。
- **轻量易部署**：仅需 Python 标准库 + 一个轻量 Web 框架（如 Streamlit），`pip install` 即可使用，无需 Docker 或数据库服务。
- **学习成本低**：结构化日志是通用技能，调试时可直接用 `jq`、`grep` 等命令行工具查询；Dashboard 代码简单直观，便于理解与二次开发。
- **契合项目定位**：本项目面向本地 MCP Server 场景，单用户、单机运行，无需分布式追踪或多租户隔离等企业级能力。

**实现架构**：

```
RAG Pipeline
    │
    ▼
Trace Collector (装饰器/回调)
    │
    ▼
JSON Lines 日志文件 (logs/traces.jsonl)
    │
    ▼
本地 Web Dashboard (Streamlit)
    │
    ▼
按 trace_id 查看各阶段详情与性能指标
```

**核心组件**：
- **结构化日志层**：基于 Python `logging` + JSON Formatter，将每次请求的 Trace 数据以 JSON Lines 格式追加写入本地文件。每行一条完整的请求记录，包含 `trace_id`、各阶段详情与耗时。
- **本地 Web Dashboard**：基于 Streamlit 构建的轻量级 Web UI，读取日志文件并提供交互式可视化。核心功能是按 `trace_id` 检索并展示单次请求的完整追踪链路。

#### 3.4.4 追踪机制实现

为确保各 RAG 阶段（可替换、可自定义）都能输出统一格式的追踪日志，系统采用 **TraceContext（追踪上下文）** 作为核心机制。

**工作原理**：

1. **请求开始**：Pipeline 入口创建一个 `TraceContext` 实例，生成唯一 `trace_id`，记录请求基础信息（Query、Collection 等）。

2. **阶段记录**：`TraceContext` 提供 `record_stage()` 方法，各阶段执行完毕后调用该方法，传入阶段名称、耗时、输入输出等数据。

3. **请求结束**：调用 `trace.finish()`，`TraceContext` 将收集的完整数据序列化为 JSON，追加写入日志文件。

**与可插拔组件的配合**：
- 各阶段组件（Retriever、Reranker 等）的接口约定中包含 `TraceContext` 参数。
- 组件实现者在执行核心逻辑后，调用 `trace.record_stage()` 记录本阶段的关键信息。
- 这是**显式调用**模式：不强制、不会因未调用而报错，但依赖开发者主动记录。好处是代码透明，开发者清楚知道哪些数据被记录；代价是需要开发者自觉遵守约定。

**阶段划分原则**：
- **Stage 是固定的通用大类**：`retrieval`（检索）、`rerank`（重排）、`generation`（生成）等，不随具体实现方案变化。
- **具体实现是阶段内部的细节**：在 `record_stage()` 中通过 `method` 字段记录采用的具体方法（如 `bm25`、`hybrid`），通过 `details` 字段记录方法相关的细节数据。
- 这样无论底层方案怎么替换，阶段结构保持稳定，Dashboard 展示逻辑无需调整。

#### 3.4.5 Dashboard 功能设计（六页面架构）

Dashboard 基于 Streamlit 构建多页面应用（`st.navigation`），提供六大功能页面：

**页面 1：系统总览 (Overview)**
- **当前页面结构**：基于 `src/observability/dashboard/pages/overview.py`，实际分为三个区域：
    - `Component Configuration`：读取 `ConfigService.get_component_cards()` 返回的组件卡片
    - `Collection Statistics`：直接连接 ChromaDB，枚举所有 collection 并显示 `chunk_count`
    - `Trace Statistics`：读取 `logs/traces.jsonl` 文件并显示总 trace 行数
- **组件配置卡片（当前实现顺序）**：卡片数据由 `src/observability/dashboard/services/config_service.py` 从 `Settings` 映射而来，渲染 `summary[] + extra + status`
    - `LLM`
        - 摘要字段：`Provider` ← `settings.llm.provider`，`Model` ← `settings.llm.model`
        - Details：`temperature` ← `settings.llm.temperature`，`max_tokens` ← `settings.llm.max_tokens`
        - 可选/固定：均为配置字段；Provider/Model 可配置
    - `Embedding`
        - 摘要字段：`Provider` ← `settings.embedding.provider`，`Model` ← `settings.embedding.model`
        - Details：`dimensions` ← `settings.embedding.dimensions`
        - 可选/固定：均为配置字段；Provider/Model/Dimensions 可配置
    - `Vector Store`
        - 摘要字段：`Engine` ← `settings.vector_store.provider`，`Default Collection` ← `settings.vector_store.collection_name`
        - Details：`persist_directory` ← `settings.vector_store.persist_directory`
        - 可选/固定：均为配置字段；`Default Collection` 表示默认 collection 名，不表示系统中唯一 collection
    - `Query Orchestration`
        - `Status` ← 由 `settings.retrieval.query_orchestration.enabled` 派生：`True -> enabled`，`False -> disabled`
        - 摘要字段：`Planner` ← `settings.retrieval.query_orchestration.planner_provider`（禁用时显示 `-`），`Configured Mode` ← `settings.retrieval.query_orchestration.mode`（禁用时显示 `off`）
        - Details：`enabled`、`max_sub_queries`、`parallel_sub_queries`、`merge_fusion (decomposition)` 均来自 `settings.retrieval.query_orchestration`
        - 可选/固定：
            - `planner_provider` 可选值固定为 `llm | rules`
            - `mode` 可选值固定为 `off | auto | synonym | decomposition`
            - `merge_fusion` 可选值固定为 `rrf | weighted_rrf`，仅作用在 decomposition 多子查询合并阶段，不影响主检索的 dense + sparse 融合
            - `parallel_sub_queries` 仅在 `mode = decomposition` 时显示为配置值，其余 mode 下显示 `False`（因为不产生子查询，该配置实际不生效）
            - `merge_fusion = rrf`：所有子查询结果等权重 RRF 融合；`weighted_rrf`：子查询按顺序递减权重（1.0 / 0.9 / 0.8 ... 最低 0.6），使靠前的子查询对最终排名影响更大
            - 其余为配置驱动数值/布尔字段
    - `Retrieval`
        - 摘要字段：`Pipeline = hybrid`，`Rank Fusion = dense + sparse -> RRF`
        - Details：`dense_top_k` ← `settings.retrieval.dense_top_k`，`sparse_top_k` ← `settings.retrieval.sparse_top_k`，`fusion_top_k` ← `settings.retrieval.fusion_top_k`
        - 可选/固定：
            - `Pipeline` 和 `Rank Fusion` 为页面固定文案，用于描述当前实现，不直接对应一个独立的 strategy 配置开关
            - Details 中的 Top-K 数值为可配置字段
            - 主检索 dense + sparse 融合始终使用标准 RRF（由 `settings.retrieval.rrf_k` 控制平滑常数），与 `query_orchestration.merge_fusion` 是两个独立的融合入口
    - `Reranker`
        - `Status` ← 由 `settings.rerank.enabled` 派生：`True -> enabled`，`False -> disabled`
        - 摘要字段：`Type` ← `settings.rerank.provider`（禁用时显示 `-`），`Top K` ← `settings.rerank.top_k`
        - Details：`enabled` ← `settings.rerank.enabled`，`configured_model` ← `settings.rerank.model`
        - 可选/固定：
            - `provider` 为配置字段，典型可选值为 `none | cross_encoder | llm`
            - `Top K` 与 `configured_model` 为配置字段
            - `Status` 与 `Details.enabled` 必须保持同步，二者来自同一个布尔值
    - `Vision LLM`
        - 仅当 `settings.vision_llm` 存在时显示卡片
        - `Status` ← `settings.vision_llm.enabled`
        - 摘要字段：`Provider` ← `settings.vision_llm.provider`，`Model` ← `settings.vision_llm.model`
        - Details：`enabled` ← `settings.vision_llm.enabled`，`max_image_size` ← `settings.vision_llm.max_image_size`
        - 可选/固定：整个卡片是可选模块；模块存在时其字段为配置驱动
    - `Ingestion`
        - 仅当 `settings.ingestion` 存在时显示卡片
        - 摘要字段：`Splitter` ← `settings.ingestion.splitter`，`Chunking` ← `settings.ingestion.chunk_size / settings.ingestion.chunk_overlap`
        - Details：`batch_size` ← `settings.ingestion.batch_size`
        - 可选/固定：
            - `splitter` 为配置字段，当前注释定义的可选值为 `recursive | semantic | fixed_length`
            - `Chunking` 为页面拼接文案，不是单独配置键名
- **Collection Statistics（当前实现）**
    - 数据来源：`overview._safe_collection_stats()`
    - 配置字段映射：
        - `settings.vector_store.persist_directory`：用于定位 ChromaDB 持久化目录
        - 不读取 `settings.vector_store.collection_name` 作为展示过滤条件，而是调用 `client.list_collections()` 枚举当前实际存在的全部 collections
    - 展示字段：
        - 卡片标题：真实 collection 名（运行时数据，不是配置常量）
        - 指标值：`collection.count()` 返回的 `chunk_count`
    - 可选/固定：
        - collection 列表与数量均为运行时数据
        - 页面空态文案固定；当 Chroma 不可用或无 collection 时显示 warning
- **Trace Statistics（当前实现）**
    - 数据来源：`overview.render()`
    - 配置字段映射：
        - 路径当前固定读取 `resolve_path("logs/traces.jsonl")`
        - 注意：这里尚未直接复用 `settings.observability.trace_file`，因此是代码常量路径，不是配置驱动路径
    - 展示字段：
        - `Total traces`：文件总行数
    - 可选/固定：
        - 指标值为运行时文件内容
        - 标题与空态文案为固定页面文案
- **与旧设计说明的差异（按当前代码为准）**
    - Overview 当前不展示 `Evaluator` 配置卡片
    - Overview 当前不展示“最近一次 Ingestion/Query trace 的时间与耗时”等系统健康指标
    - Overview 当前的 `Collection Statistics` 是直接访问 ChromaDB 统计 chunk 数，而不是调用 `DocumentManager.get_collection_stats()`

**页面 2：数据浏览器 (Data Browser)**
- **文档列表视图**：展示已摄入的文档（source_path、集合、chunk 数、摄入时间），支持按集合筛选与关键词搜索。
- **Chunk 详情视图**：点击文档展开其所有 chunk，每个 chunk 显示：
    - 原文内容（可折叠长文本）
    - Metadata 各字段（title、summary、tags、page、image_refs 等）
    - 关联图片预览（从 ImageStorage 读取并展示缩略图）
- **数据来源**：通过 `DataService` 读取 ChromaDB 数据。
- **默认 Collection 逻辑**：页面初始化时通过 `DataService.get_default_collection_name()` 读取 `settings.vector_store.collection_name` 作为默认集合名。下拉框中仍会列出所有真实存在的 collections。

**页面 3：Ingestion 管理 (Ingestion Manager)**
- **文件选择与摄取触发**：
    - 文件上传组件（`st.file_uploader`）或目录路径输入
    - 选择目标集合（下拉选择或新建）
    - 点击"开始摄取"按钮触发 `IngestionPipeline.run()`
    - 利用 `on_progress` 回调驱动 Streamlit 进度条（`st.progress`），实时显示当前阶段与处理进度
- **默认 Collection 逻辑**：Collection 输入框默认值与空值回退均读取 `settings.vector_store.collection_name`
- **文档删除**：
    - 在文档列表中提供"删除"按钮
    - 调用 `DocumentManager.delete_document()` 协调跨存储删除
    - 删除完成后刷新列表
- **注意**：Pipeline 执行为同步阻塞操作，Streamlit 的 rerun 机制天然支持（进度条在同一 request 中更新）。

**页面 4：Ingestion 追踪 (Ingestion Traces)**
- **摄取历史列表**：按时间倒序展示 `trace_type == "ingestion"` 的历史记录，显示文件名、集合、总耗时、状态（成功/失败）。
- **单次摄取详情**：
    - **阶段耗时瀑布图**：横向条形图展示 load/split/transform/embed/upsert 各阶段时间分布。
    - **处理统计**：chunk 数、图片数、跳过数、失败数。
    - **各阶段详情展开**：点击查看 method/provider、输入输出样本。

**页面 5：Query 追踪 (Query Traces)**
- **查询历史列表**：按时间倒序展示 `trace_type == "query"` 的历史记录，支持按 Query 关键词筛选。
- **单次查询详情**：
    - **耗时瀑布图**：展示 query_processing/query_orchestration/dense/sparse/fusion/rerank 各阶段时间分布。
    - **编排详情面板**：展示 Planner 决策结果、是否采用同义扩展或逻辑拆解、生成的子查询列表、是否发生回退。
    - **子查询执行视图**：当采用 Decomposition Mode 时，展示每个子查询的执行状态、返回候选数与合并前排名样本。
    - **Dense vs Sparse 对比**：并列展示两路召回结果的 Top-N 文档 ID 与分数。
    - **Rerank 前后对比**：展示融合排名与精排后排名的变化（排名跃升/下降标记）。
    - **最终结果表**：展示 Top-K 候选文档的标题、分数、来源。

**页面 6：评估面板 (Evaluation Panel)**

**评估架构**：

```
UI 层: Streamlit Panel (evaluation_panel.py) / CLI (scripts/evaluate.py)
编排层: EvalRunner (eval_runner.py) — 加载 Golden Test Set → 检索 → 评估 → 聚合
评估层: CustomEvaluator / RagasEvaluator
工厂层: EvaluatorFactory (evaluator_factory.py)
抽象层: BaseEvaluator — 统一 evaluate(query, chunks, answer, ground_truth) 接口
```

**两种评估后端**：

| 后端 | 依赖 | 指标 | 使用条件 |
|------|------|------|----------|
| `custom` | 无（纯离线确定性计算） | `hit_rate`（命中率）、`mrr`（Mean Reciprocal Rank） | Golden Test Set 需提供 `expected_chunk_ids` |
| `ragas` | 需 OpenAI/Azure 兼容 LLM + Embedding | `faithfulness`（忠实度）、`answer_relevancy`（回答相关性）、`context_precision`（上下文精确度） | Golden Test Set 需提供 `reference_answer` 或在 UI 中手动填写 |

- **配置与运行**：
  - 页面上方选择评估后端（`custom` / `ragas`）、Top-K、Collection（可选）、Golden Test Set 路径。
  - 选择 `ragas` 后端时，页面自动展开 **回答输入区**：列出 Golden Test Set 中每个 `query`，预填 `reference_answer`，用户可手动修改或直接使用。
  - 点击 `▶️ Run Evaluation` 后，系统执行：HybridSearch 检索 → 可选 Reranker 重排序 → 评估器评分 → 聚合所有 Query 的平均指标。
  - 也可通过命令行运行：`python scripts/evaluate.py --test-set path/to/golden.json --top-k 10 --collection my_docs`。
- **Golden Test Set 格式**（JSON，默认路径 `tests/fixtures/golden_test_set.json`）：
  ```json
  {
    "description": "...",
    "version": "1.0",
    "test_cases": [
      {
        "query": "What is Modular RAG?",
        "expected_chunk_ids": ["chunk_001", "chunk_003"],
        "expected_sources": [],
        "reference_answer": "Modular RAG is a ..."
      }
    ]
  }
  ```
  - `query`：测试问题（必填，所有后端使用）。
  - `expected_chunk_ids`：期望检索到的 chunk ID 列表（custom 后端用于计算 hit_rate / mrr）。
  - `reference_answer`：参考/期望回答文本（ragas 后端用于 LLM-as-Judge 评估）。
- **评估流程**：对每个 test_case → HybridSearch 检索（Dense + Sparse + RRF 融合）→ 可选 Reranker 重排 → 获取回答（优先 UI 手动输入 → fallback 拼接前 5 个 chunk 文本）→ 构建 ground_truth → 运行 Evaluator → 所有 Query 指标取平均值得到聚合分数。
- **指标展示**：聚合指标以 Metric Card 展示；Per-Query 详情以可折叠面板展示，包含检索到的 chunk ID 列表和生成回答文本。
- **历史趋势**：每次测评结果自动保存到 `logs/eval_history.jsonl`，页面底部按 evaluator 类型分为两张独立表格：
    - **📊 Custom Evaluator History**：列固定为 `Timestamp / Test Set / Queries / Time (ms) / hit_rate / mrr`。即使某次测评因空知识库导致 aggregate_metrics 为空，表格仍显示这些列（值为 0.0），不会因缺值而列不出现。
    - **🤖 Ragas Evaluator History**：列固定为 `Timestamp / Test Set / Queries / Time (ms) / faithfulness / answer_relevancy / context_precision`。同样缺值显示 0.0。
    - 分表原因：Custom 和 Ragas 的指标维度完全不同，单表混合会导致大量交叉空列，用户难以阅读。
- **空知识库容错（当前实现）**：
    - `CustomEvaluator.evaluate()`：当 `retrieved_chunks` 为空列表时，直接返回 `{metric: 0.0 for metric in self.metrics}`（例如 `{"hit_rate": 0.0, "mrr": 0.0}`），不再抛出 `ValueError("retrieved_chunks cannot be empty")`。这使得空知识库测评仍能看到指标卡片与 History 列。
    - `RagasEvaluator.evaluate()`：同上处理，空 chunks 返回 `{m: 0.0 for m in self._metric_names}`。

**Dashboard 技术架构**：

```
src/observability/dashboard/
├── app.py                    # Streamlit 入口，页面导航注册
├── pages/
│   ├── overview.py           # 页面 1：系统总览
│   ├── data_browser.py       # 页面 2：数据浏览器
│   ├── ingestion_manager.py  # 页面 3：Ingestion 管理
│   ├── ingestion_traces.py   # 页面 4：Ingestion 追踪
│   ├── query_traces.py       # 页面 5：Query 追踪
│   └── evaluation_panel.py   # 页面 6：评估面板
└── services/
    ├── trace_service.py      # Trace 数据读取服务（解析 traces.jsonl）
    ├── data_service.py       # 数据浏览服务（封装 ChromaStore/ImageStorage 读取）
    └── config_service.py     # 配置读取服务（封装 Settings 读取与展示）
```

**Dashboard 与 Trace 的数据关系**：
- Dashboard 页面 4/5 读取 `logs/traces.jsonl`（通过 `TraceService`），按 `trace_type` 分类展示。
- Dashboard 页面 1/2/3 直接读取存储层（通过 `DataService` 封装 ChromaStore/ImageStorage/FileIntegrity），不依赖 Trace。
- 所有页面基于 Trace 中 `method`/`provider` 字段动态渲染标签，更换组件后自动适配。


#### 3.4.6 配置示例

```yaml
observability:
  enabled: true
  
  # 日志配置
  logging:
    log_file: logs/traces.jsonl  # JSON Lines 格式日志文件
    log_level: INFO  # DEBUG | INFO | WARNING
  
  # 追踪粒度控制
  detail_level: standard  # minimal | standard | verbose

# Dashboard 管理平台配置
dashboard:
  enabled: true
  port: 8501                     # Streamlit 服务端口
  traces_dir: ./logs             # Trace 日志文件目录
  auto_refresh: true             # 是否自动刷新（轮询新 trace）
  refresh_interval: 5            # 自动刷新间隔（秒）
```


### 3.5 多模态图片处理设计 (Multimodal Image Processing Design)

**目标：** 设计一套完整的图片处理方案，使 RAG 系统能够理解、索引并检索文档中的图片内容，实现"用自然语言搜索图片"的能力，同时保持架构的简洁性与可扩展性。

#### 3.5.1 设计理念与策略选型

多模态 RAG 的核心挑战在于：**如何让纯文本的检索系统"看懂"图片**。业界主要有两种技术路线：

| 策略 | 核心思路 | 优势 | 劣势 |
|-----|---------|------|------|
| **Image-to-Text (图转文)** | 利用 Vision LLM 将图片转化为文本描述，复用纯文本 RAG 链路 | 架构统一、实现简单、成本可控 | 描述质量依赖 LLM 能力，可能丢失视觉细节 |
| **Multi-Embedding (多模态向量)** | 使用 CLIP 等模型将图文统一映射到同一向量空间 | 保留原始视觉特征，支持图搜图 | 需引入额外向量库，架构复杂度高 |

**本项目选型：Image-to-Text（图转文）策略**

选型理由：
- **架构统一**：无需引入 CLIP 等多模态 Embedding 模型，无需维护独立的图像向量库，完全复用现有的文本 RAG 链路（Ingestion → Hybrid Search → Rerank）。
- **语义对齐**：通过 LLM 将图片的视觉信息转化为自然语言描述，天然与用户的文本查询在同一语义空间，检索效果可预期。
- **成本可控**：仅在数据摄取阶段一次性调用 Vision LLM，检索阶段无额外成本。
- **渐进增强**：未来如需支持"图搜图"等高级能力，可在此基础上叠加 CLIP Embedding，无需重构核心链路。

#### 3.5.2 图片处理全流程设计

图片处理贯穿 Ingestion Pipeline 的多个阶段，整体流程如下：

```
原始文档 (PDF/PPT/Markdown)
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  Loader 阶段：图片提取与引用收集                           │
│  - 解析文档，识别并提取嵌入的图片资源                        │
│  - 为每张图片生成唯一标识 (image_id)                       │
│  - 在文档文本中插入图片占位符/引用标记                       │
│  - 输出：Document (text + metadata.images[])             │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  Splitter 阶段：保持图文关联                               │
│  - 切分时保留图片引用标记在对应 Chunk 中                     │
│  - 确保图片与其上下文段落保持关联                            │
│  - 输出：Chunks (各自携带关联的 image_refs)                │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  Transform 阶段：图片理解与描述生成                         │
│  - 调用 Vision LLM 对每张图片生成结构化描述                  │
│  - 将描述文本注入到关联 Chunk 的正文或 Metadata 中           │
│  - 输出：Enriched Chunks (含图片语义信息)                  │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  Storage 阶段：双轨存储                                    │
│  - 向量库：存储增强后的 Chunk (含图片描述) 用于检索           │
│  - 文件系统/Blob：存储原始图片文件用于返回展示                │
└─────────────────────────────────────────────────────────┘
```

#### 3.5.3 各阶段技术要点

**1. Loader 阶段：图片提取与引用收集**

- **提取策略**：
  - 解析文档时识别嵌入的图片资源（PDF 中的 XObject、PPT 中的媒体文件、Markdown 中的 `![]()` 引用）。
  - 为每张图片生成全局唯一的 `image_id`（建议格式：`{doc_hash}_{page}_{seq}`）。
  - 将图片二进制数据提取并暂存，记录其在原文档中的位置信息。

- **引用标记**：
  - 在转换后的 Markdown 文本中，于图片原始位置插入占位符（如 `[IMAGE: {image_id}]`）。
  - 在 Document 的 Metadata 中维护 `images` 列表，记录每张图片的 `image_id`、相对存储路径、页码、尺寸等基础信息。

- **存储原始图片**：
  - 将提取的图片保存至本地文件系统的约定目录（当前实现为 `data/images/{collection}/{doc_hash}/{image_id}.{ext}`）。
  - 仅保存需要的图片格式（推荐统一转换为 PNG/JPEG），控制存储体积。
  - **安全约束**：图片读取与返回阶段只允许访问 `data/images/` 沙箱目录内的文件；对来自 Metadata 的路径必须先做 `Path.resolve()` + 基目录约束校验，禁止越界读取任意本地文件。
  - **Collection 约束**：用于文件系统目录名的 `collection` 必须通过白名单校验，当前规则为 `^[A-Za-z0-9_-]+$`，不允许路径分隔符、空白和 `..` 等穿越模式。

**2. Splitter 阶段：保持图文关联**

- **关联保持原则**：
  - 图片引用标记应与其说明性文字（Caption、前后段落）尽量保持在同一 Chunk 中。
  - 若图片出现在章节开头或结尾，切分时应将其归入语义上最相关的 Chunk。

- **Chunk Metadata 扩展**：
  - 每个 Chunk 的 Metadata 中增加 `image_refs: List[image_id]` 字段，记录该 Chunk 关联的图片列表。
  - 此字段用于后续 Transform 阶段定位需要处理的图片，以及检索命中后定位需要返回的图片。

**3. Transform 阶段：图片理解与描述生成**

这是多模态处理的核心环节，负责将视觉信息转化为可检索的文本语义。

- **Vision LLM 选型**：

| 模型 | 提供商 | 特点 | 适用场景 | 推荐指数 |
|-----|--------|------|---------|---------|
| **GPT-4o** | OpenAI / Azure | 理解能力强，支持复杂图表解读，英文文档表现优异 | 高质量需求、复杂业务文档、国际化场景 | ⭐⭐⭐⭐⭐ |
| **Qwen-VL-Max** | 阿里云 (DashScope) | 中文理解能力出色，性价比高，对中文图表/文档支持好 | 中文文档、国内部署、成本敏感场景 | ⭐⭐⭐⭐⭐ |
| **Qwen-VL-Plus** | 阿里云 (DashScope) | 速度更快，成本更低，适合大批量处理 | 大批量中文文档、快速迭代场景 | ⭐⭐⭐⭐ |
| **Claude 3.5 Sonnet** | Anthropic | 多模态原生支持，长上下文 | 需要结合大段文字理解图片 | ⭐⭐⭐⭐ |
| **Gemini Pro Vision** | Google | 成本较低，速度较快 | 大批量处理、成本敏感场景 | ⭐⭐⭐ |
| **GLM-4V** | 智谱 AI (ZhipuAI) | 国内老牌，稳定性好，中文支持佳 | 国内部署备选、企业级应用 | ⭐⭐⭐⭐ |

**双模型选型策略（推荐）**：

本项目采用**国内 + 国外双模型**方案，通过配置切换，兼顾不同部署环境和文档类型：

| 部署环境 | 主选模型 | 备选模型 | 说明 |
|---------|---------|---------|------|
| **国际化 / Azure 环境** | GPT-4o (Azure) | Qwen-VL-Max | 英文文档优先用 GPT-4o，中文文档可切换 Qwen-VL |
| **国内部署 / 纯中文场景** | Qwen-VL-Max | GPT-4o | 中文图表理解用 Qwen-VL，特殊需求可切换 GPT-4o |
| **成本敏感 / 大批量** | Qwen-VL-Plus | Gemini Pro Vision | 牺牲部分质量换取速度和成本 |

**选型理由**：

1. **GPT-4o (国外首选)**：
   - 视觉理解能力业界领先，复杂图表解读准确率高
   - Azure 部署可满足企业合规要求
   - 英文技术文档理解效果最佳

2. **Qwen-VL-Max (国内首选)**：
   - 中文场景下表现与 GPT-4o 接近，部分中文图表任务甚至更优
   - 通过阿里云 DashScope API 调用，国内访问稳定、延迟低
   - 价格约为 GPT-4o 的 1/3 ~ 1/5，性价比极高
   - 原生支持中文 OCR，对中文截图、表格识别更准确

- **描述生成策略**：
  - **结构化 Prompt**：设计专用的图片理解 Prompt，引导 LLM 输出结构化描述，而非自由发挥。
  - **上下文感知**：将图片的前后文本段落一并传入 Vision LLM，帮助其理解图片在文档中的语境与作用。
  - **分类型处理**：针对不同类型的图片采用差异化的理解策略：

| 图片类型 | 理解重点 | Prompt 引导方向 |
|---------|---------|----------------|
| **流程图/架构图** | 节点、连接关系、流程逻辑 | "描述这张图的结构和流程步骤" |
| **数据图表** | 数据趋势、关键数值、对比关系 | "提取图表中的关键数据和结论" |
| **截图/UI** | 界面元素、操作指引、状态信息 | "描述截图中的界面内容和关键信息" |
| **照片/插图** | 主体对象、场景、视觉特征 | "描述图片中的主要内容" |

- **描述注入方式**：
  - **推荐：注入正文**：将生成的描述直接替换或追加到 Chunk 正文中的图片占位符位置，格式如 `[图片描述: {caption}]`。这样描述会被 Embedding 覆盖，可被直接检索。
  - **备选：注入 Metadata**：将描述存入 `chunk.metadata.image_captions` 字段。需确保检索时该字段也被索引。

- **幂等与增量处理**：
  - 为每张图片的描述计算内容哈希，存入 `processing_cache` 表。
  - 重复处理时，若图片内容未变且 Prompt 版本一致，直接复用缓存的描述，避免重复调用 Vision LLM。

**4. Storage 阶段：双轨存储**

- **向量库存储（用于检索）**：
  - 存储增强后的 Chunk，其正文已包含图片描述，Metadata 包含 `image_refs` 列表。
  - 检索时通过文本相似度即可命中包含相关图片描述的 Chunk。

- **原始图片存储（用于返回）**：
  - 图片文件存储于本地文件系统，路径记录在独立的 `images` 索引表中。
  - 索引表字段：`image_id`, `file_path`, `source_doc`, `page`, `width`, `height`, `mime_type`。
  - 检索命中后，根据 Chunk 的 `image_refs` 查询索引表，获取图片文件路径用于返回。
  - **安全约束**：返回前必须再次校验图片路径仍位于 `data/images/` 沙箱目录内，Vision LLM 本地图片读取同样遵循这一约束。

#### 3.5.4 检索与返回流程

当用户查询命中包含图片的 Chunk 时，系统需要将图片与文本一并返回：

```
用户查询: "系统架构是什么样的？"
    │
    ▼
Hybrid Search 命中 Chunk（正文含 "[图片描述: 系统采用三层架构...]"）
    │
    ▼
从 Chunk.metadata.image_refs 获取关联的 image_id 列表
    │
    ▼
查询 images 索引表，获取图片文件路径
    │
    ▼
读取图片文件，编码为 Base64
    │
    ▼
构造 MCP 响应，包含 TextContent + ImageContent
```

**MCP 响应格式**：

```json
{
  "content": [
    {
      "type": "text",
      "text": "根据文档，系统架构如下：...\n\n[1] 来源: architecture.pdf, 第5页"
    },
    {
      "type": "image",
      "data": "<base64-encoded-image>",
      "mimeType": "image/png"
    }
  ]
}
```

#### 3.5.5 质量保障与边界处理

- **描述质量检测**：
  - 对生成的描述进行基础质量检查（长度、是否包含关键信息）。
  - 若描述过短或 LLM 返回"无法识别"，标记该图片为 `low_quality`，可选择人工复核或跳过索引。

- **大尺寸/特殊图片处理**：
  - 超大图片在传入 Vision LLM 前进行压缩（保持宽高比，限制最大边长）。
  - 对于纯装饰性图片（如分隔线、背景图），可通过尺寸或位置规则过滤，不进入描述生成流程。

- **批量处理优化**：
  - 图片描述生成支持批量异步调用，提高吞吐量。
  - 单个文档处理失败时，记录失败的图片 ID，不影响其他图片的处理进度。

- **降级策略**：
  - 当 Vision LLM 不可用时，系统回退到"仅保留图片占位符"模式，图片不参与检索但不阻塞 Ingestion 流程。
  - 在 Chunk 中标记 `has_unprocessed_images: true`，后续可增量补充描述。

## 4. 测试方案

### 4.1 设计理念：测试驱动开发 (TDD)

本项目采用**测试驱动开发（Test-Driven Development）**作为核心开发范式，确保每个组件在实现前就已明确其预期行为，通过自动化测试持续验证系统质量。

**核心原则**：
- **早测试、常测试**：每个功能模块实现的同时就编写对应的单元测试，而非事后补测。
- **测试即文档**：测试用例本身就是最准确的行为规范，新加入的开发者可通过阅读测试快速理解各模块功能。
- **快速反馈循环**：单元测试应在秒级完成，支持开发者高频执行，立即发现引入的问题。
- **分层测试金字塔**：大量快速的单元测试作为基座，少量关键路径的集成测试作为保障，极少数端到端测试验证完整流程。

```
        /\
       /E2E\         <- 少量，验证关键业务流程
      /------\
     /Integration\   <- 中量，验证模块协作
    /------------\
   /  Unit Tests  \  <- 大量，验证单个函数/类
  /________________\
```

### 4.2 测试分层策略

#### 4.2.1 单元测试 (Unit Tests)

**目标**：验证每个独立组件的内部逻辑正确性，隔离外部依赖。

**覆盖范围**：

| 模块 | 测试重点 | 典型测试用例 |
|-----|---------|------------|
| **Loader (文档解析器)** | 格式解析、元数据提取、图片引用收集 | - 测试解析单页/多页 PDF<br>- 验证 Markdown 标题层级提取<br>- 检查图片占位符插入位置 |
| **Splitter (切分器)** | 切分边界、上下文保留、元数据传递 | - 验证按标题切分不破坏段落<br>- 测试超长文本的递归切分<br>- 检查 Chunk 的 `source` 字段正确性 |
| **Transform (增强器)** | 图片描述生成、元数据注入 | - Mock Vision LLM，验证描述注入逻辑<br>- 测试无图片时的降级行为<br>- 验证幂等性（重复处理相同输入） |
| **Embedding (向量化)** | 批处理、差量计算、向量维度 | - 验证相同文本生成相同向量<br>- 测试批量请求的拆分与合并<br>- 检查缓存命中逻辑 |
| **BM25 (稀疏编码)** | 关键词提取、权重计算 | - 验证停用词过滤<br>- 测试 IDF 计算准确性<br>- 检查稀疏向量格式 |
| **Retrieval (检索器)** | 召回精度、融合算法 | - 测试纯 Dense/Sparse/Hybrid 三种模式<br>- 验证 RRF 融合分数计算<br>- 检查 Top-K 结果排序 |
| **Reranker (重排器)** | 分数归一化、降级回退 | - Mock Cross-Encoder，验证分数重排<br>- 测试超时后的 Fallback 逻辑<br>- 验证空候选集处理 |

**技术选型**：
- **测试框架**：`pytest`（Python 标准选择，支持参数化测试、Fixture 机制）
- **Mock 工具**：`unittest.mock` / `pytest-mock`（隔离外部依赖，如 LLM API）
- **断言增强**：`pytest-check`（支持多断言不中断执行）
- **测试标记**：使用 `unit` / `integration` / `e2e` / `image` / `llm` 等 pytest markers 对测试分层与能力边界进行显式标记。

#### 4.2.2 集成测试 (Integration Tests)

**目标**：验证多个组件协作时的数据流转与接口兼容性。

**覆盖范围**：

| 测试场景 | 验证要点 | 测试策略 |
|---------|---------|---------|
| **Ingestion Pipeline** | Loader → Splitter → Transform → Storage 的完整流程 | - 使用真实的测试 PDF 文件<br>- 验证最终存入向量库的数据完整性<br>- 检查中间产物（如临时图片文件）是否正确清理 |
| **Hybrid Search** | Dense + Sparse 召回的融合结果 | - 准备已知答案的查询-文档对<br>- 验证融合后的 Top-1 是否命中正确文档<br>- 测试极端情况（某一路无结果） |
| **Rerank Pipeline** | 召回 → 过滤 → 重排的组合 | - 验证 Metadata 过滤后的候选集正确性<br>- 检查 Reranker 是否改变了 Top-1 结果<br>- 测试 Reranker 失败时的回退 |
| **MCP Server** | 工具调用的端到端流程 | - 模拟 MCP Client 发送 JSON-RPC 请求<br>- 验证返回的 `content` 格式符合协议<br>- 测试错误处理（如查询语法错误） |

**技术选型**：
- **数据隔离**：每个测试使用独立的临时数据库/向量库（`pytest-tempdir`）
- **异步测试**：`pytest-asyncio`（若 MCP Server 采用异步实现）
- **契约测试**：定义各模块间的 Schema，确保接口不漂移
- **运行策略**：默认全量测试应可在离线、本地、无额外凭据环境下稳定运行；依赖真实云端 API 或真实服务状态的集成测试应通过显式开关 opt-in（当前约定为环境变量 `RUN_REAL_API_TESTS=1`），而不是默认执行。

**开启方式示例**：
- 默认运行全量测试（不触发真实 API / 真实服务测试）：
  - `uv run pytest tests -q`
- 单次命令显式开启真实 API / 真实服务测试：
  - `RUN_REAL_API_TESTS=1 uv run pytest tests -q`
- 只运行某个 live integration test：
  - `RUN_REAL_API_TESTS=1 uv run pytest tests/integration/test_metadata_enricher_llm.py -v -s`
  - `RUN_REAL_API_TESTS=1 uv run pytest tests/integration/test_vision_llm_integration.py -v -s`
- 若使用特定云端 Provider，还需同时提供该 Provider 所需的凭据或配置，例如：
  - `OPENAI_API_KEY=your_key RUN_REAL_API_TESTS=1 uv run pytest tests/integration/test_metadata_enricher_llm.py -v -s`

#### 4.2.3 端到端测试 (End-to-End Tests)

**目标**：模拟真实用户操作，验证完整业务流程的可用性。

**核心场景**：

**场景 1：数据准备（离线摄取）**
- **测试目标**：验证文档摄取流程的完整性与正确性
- **测试步骤**：
  - 准备测试文档（PDF 文件，包含文本、图片、表格等多种元素）
  - 执行离线摄取脚本，将文档导入知识库
  - 验证摄取结果：检查生成的 Chunk 数量、元数据完整性、图片描述生成
  - 验证存储状态：确认向量库和 BM25 索引正确创建
  - 验证幂等性：重复摄取同一文档，确保不产生重复数据
- **验证要点**：
  - Chunk 的切分质量（语义完整性、上下文保留）
  - 元数据字段完整性（source、page、title、tags 等）
  - 图片处理结果（Caption 生成、Base64 编码存储）
  - 向量与稀疏索引的正确性

**场景 2：召回测试**
- **测试目标**：验证检索系统的召回精度与排序质量
- **测试步骤**：
  - 基于已摄取的知识库，准备一组测试查询（包含不同难度与类型）
  - 执行混合检索（Dense + Sparse + Rerank）
  - 验证召回结果：检查 Top-K 文档是否包含预期来源
  - 对比不同检索策略的效果（纯 Dense、纯 Sparse、Hybrid）
  - 验证 Rerank 的影响：对比重排前后的结果变化
- **验证要点**：
  - Hit Rate@K：Top-K 结果命中率是否达标
  - 排序质量：正确答案是否排在前列（MRR、NDCG）
  - 边界情况处理：空查询、无结果查询、超长查询
  - 多模态召回：包含图片的文档是否能通过文本查询召回

**场景 3：MCP Client 功能测试**
- **测试目标**：验证 MCP Server 与 Client（如 GitHub Copilot）的协议兼容性与功能完整性
- **测试步骤**：
  - 启动 MCP Server（Stdio Transport 模式）
  - 模拟 MCP Client 发送各类 JSON-RPC 请求
  - 测试工具调用：`query_knowledge_hub`、`list_collections` 等
  - 验证返回格式：符合 MCP 协议规范（content 数组、structuredContent）
  - 测试引用透明性：返回结果包含完整的 Citation 信息
  - 测试多模态返回：包含图片的响应正确编码为 Base64
- **验证要点**：
  - 协议合规性：JSON-RPC 2.0 格式、错误码映射
  - 工具注册：`tools/list` 返回所有可用工具及其 Schema
  - 响应格式：TextContent 与 ImageContent 的正确组合
  - 错误处理：无效参数、超时、服务不可用等异常场景
  - 性能指标：单次请求的端到端延迟（含检索、重排、格式化）

**测试工具**：
- **BDD 框架**：`behave` 或 `pytest-bdd`（以 Gherkin 语法描述场景）
- **环境准备**：
  - 临时测试向量库（独立于生产数据）
  - 预置的标准测试文档集
  - 本地 MCP Server 进程（Stdio Transport）
  - 真实 API / 真实云端 Provider 测试需显式开启（当前约定通过环境变量 `RUN_REAL_API_TESTS=1`），默认 E2E/Integration 套件应避免误触发线上调用与额外费用。

### 4.3 RAG 质量评估测试

**目标**：验证已设计的评估体系（见 3.3.4 评估框架抽象）是否正确实现，并能有效评估 RAG 系统的召回与生成质量。

**测试要点**：

1. **黄金测试集准备**
   - 构建标准的"问题-答案-来源文档"测试集（JSON 格式）
   - 初期人工标注核心场景，后期持续积累坏 Case

2. **评估框架实现验证**
   - 验证 Ragas/DeepEval 等评估框架的正确集成
   - 确认评估接口能输出标准化的指标字典
   - 测试多评估器并行执行与结果汇总

3. **关键指标达标验证**
   - 检索指标：Hit Rate@K ≥ 90%、MRR ≥ 0.8、NDCG@K ≥ 0.85
   - 生成指标：Faithfulness ≥ 0.9、Answer Relevancy ≥ 0.85
   - 定期运行评估，监控指标是否回归

**说明**：本节重点是验证评估体系的工程实现，而非重新设计评估方法（评估方法的设计见第 3 章技术选型）。

### 4.4 性能与压力测试（可选）

> **说明**：本项目定位为本地 MCP Server，单用户开发环境，采用 Stdio Transport 通信方式。性能与压力测试在当前阶段**不是必需的**，此处列出主要用于：
> 1. **架构完整性**：展示完整的工程化测试体系，体现系统设计的专业性
> 2. **未来扩展性**：若后续需要云端部署或多用户支持，可直接参考此方案
> 3. **性能基准建立**：通过基础性能测试了解系统瓶颈，为优化提供数据支撑

**可选测试场景**：

| 测试类型 | 验证点 | 工具 | 优先级 |
|---------|-------|------|-------|
| **延迟测试** | 单次查询的 P50/P95/P99 延迟 | `pytest-benchmark` | 中（可帮助识别慢查询） |
| **吞吐量测试** | 并发查询时的 QPS 上限 | `locust` | 低（本地单用户无需求） |
| **内存泄漏检测** | 长时间运行后的内存占用 | `memory_profiler` | 低（短期运行无影响） |
| **向量库性能** | 不同数据规模下的查询速度 | 自定义 Benchmark | 中（验证扩展性） |

### 4.5 测试工具链与 CI/CD 集成

**本地开发工作流**：
- **快速验证**：仅运行单元测试，秒级反馈
- **完整验证**：单元测试 + 集成测试，生成覆盖率报告
- **质量评估**：定期执行 RAG 质量测试，监控指标变化

**CI/CD Pipeline 设计**（可选）：
> **说明**：本地项目不强制要求 CI/CD，但配置自动化测试流程有助于代码质量保障与持续集成实践。

- **单元测试阶段**：每次提交自动触发，验证基础功能，生成覆盖率报告
- **集成测试阶段**：单元测试通过后执行，验证模块协作
- **质量评估阶段**：PR 触发，运行完整的 RAG 质量测试，发布评估报告

**测试覆盖率目标**：
- **单元测试**：核心逻辑覆盖率 ≥ 80%
- **集成测试**：关键路径覆盖率 100%（如 Ingestion、Hybrid Search）
- **E2E 测试**：核心用户场景覆盖率 100%（至少 3 个关键流程）


## 5. 系统架构与模块设计

### 5.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                     MCP Clients (外部调用层)                                  │
│                                                                                             │
│    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐                        │
│    │  GitHub Copilot │    │  Claude Desktop │    │  其他 MCP Agent │                        │
│    └────────┬────────┘    └────────┬────────┘    └────────┬────────┘                        │
│             │                      │                      │                                 │
│             └──────────────────────┼──────────────────────┘                                 │
│                                    │  JSON-RPC 2.0 (Stdio Transport)                       │
└────────────────────────────────────┼────────────────────────────────────────────────────────┘
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   MCP Server 层 (接口层)                                     │
│                                                                                             │
│    ┌─────────────────────────────────────────────────────────────────────────────────┐      │
│    │                              MCP Protocol Handler                               │      │
│    │                    (tools/list, tools/call, resources/*)                        │      │
│    └─────────────────────────────────────────────────────────────────────────────────┘      │
│                                           │                                                 │
│    ┌──────────────────────┬───────────────┼───────────────┬──────────────────────┐          │
│    ▼                      ▼               ▼               ▼                      ▼          │
│ ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│ │query_knowledge│ │list_collections│ │get_document_ │  │search_by_    │  │  其他扩展    │    │
│ │    _hub      │  │              │  │   summary    │  │  keyword     │  │   工具...    │    │
│ └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   Core 层 (核心业务逻辑)                                     │
│                                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐    │
│  │                            Query Engine (查询引擎)                                   │    │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐    │    │
│  │  │                         Query Processor (查询预处理)                         │    │    │
│  │  │            关键词提取 | 查询扩展 (同义词/别名) | Metadata 解析               │    │    │
│  │  └─────────────────────────────────────────────────────────────────────────────┘    │    │
│  │                                       │                                             │    │
│  │  ┌────────────────────────────────────┼────────────────────────────────────┐        │    │
│  │  │                     Hybrid Search Engine (混合检索引擎)                  │        │    │
│  │  │                                    │                                    │        │    │
│  │  │    ┌───────────────────┐    ┌──────┴──────┐    ┌───────────────────┐    │        │    │
│  │  │    │   Dense Route     │    │   Fusion    │    │   Sparse Route    │    │        │    │
│  │  │    │ (Embedding 语义)  │◄───┤    (RRF)    ├───►│   (BM25 关键词)   │    │        │    │
│  │  │    └───────────────────┘    └─────────────┘    └───────────────────┘    │        │    │
│  │  └─────────────────────────────────────────────────────────────────────────┘        │    │
│  │                                       │                                             │    │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐    │    │
│  │  │                        Reranker (重排序模块) [可选]                          │    │    │
│  │  │          None (关闭) | Cross-Encoder (本地模型) | LLM Rerank               │    │    │
│  │  └─────────────────────────────────────────────────────────────────────────────┘    │    │
│  │                                       │                                             │    │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐    │    │
│  │  │                      Response Builder (响应构建器)                           │    │    │
│  │  │            引用生成 (Citation) | 多模态内容组装 (Text + Image)               │    │    │
│  │  └─────────────────────────────────────────────────────────────────────────────┘    │    │
│  └─────────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐    │
│  │                          Trace Collector (追踪收集器)                                │    │
│  │                   trace_id 生成 | 各阶段耗时记录 | JSON Lines 输出                  │    │
│  └─────────────────────────────────────────────────────────────────────────────────────┘    │
└────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                         │
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   Storage 层 (存储层)                                        │
│                                                                                             │
│    ┌─────────────────────────────────────────────────────────────────────────────────┐      │
│    │                             Vector Store (向量存储)                              │      │
│    │                                                                                 │      │
│    │     ┌─────────────────────────────────────────────────────────────────────┐     │      │
│    │     │                         Chroma DB                                   │     │      │
│    │     │    Dense Vector | Sparse Vector | Chunk Content | Metadata          │     │      │
│    │     └─────────────────────────────────────────────────────────────────────┘     │      │
│    └─────────────────────────────────────────────────────────────────────────────────┘      │
│                                                                                             │
│    ┌──────────────────────────────────┐    ┌──────────────────────────────────┐             │
│    │       BM25 Index (稀疏索引)       │    │       Image Store (图片存储)     │             │
│    │        倒排索引 | IDF 统计        │    │    本地文件系统 | Base64 编码     │             │
│    └──────────────────────────────────┘    └──────────────────────────────────┘             │
│                                                                                             │
│    ┌──────────────────────────────────┐    ┌──────────────────────────────────┐             │
│    │     Trace Logs (追踪日志)         │    │   Processing Cache (处理缓存)    │             │
│    │     JSON Lines 格式文件           │    │   文件哈希 | Chunk 哈希 | 状态   │             │
│    └──────────────────────────────────┘    └──────────────────────────────────┘             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                              Ingestion Pipeline (离线数据摄取)                               │
│                                                                                             │
│    ┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐   │
│    │   Loader   │───►│  Splitter  │───►│ Transform  │───►│  Embedding │───►│   Upsert   │   │
│    │ (文档解析) │    │  (切分器)  │    │ (增强处理) │    │  (向量化)  │    │  (存储)    │   │
│    └────────────┘    └────────────┘    └────────────┘    └────────────┘    └────────────┘   │
│         │                  │                  │                  │                │         │
│         ▼                  ▼                  ▼                  ▼                ▼         │
│    ┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐    ┌────────────┐   │
│    │MarkItDown │    │Recursive   │    │LLM重写     │    │Dense:      │    │Chroma      │   │
│    │PDF→MD     │    │Character   │    │Image       │    │OpenAI/BGE  │    │Upsert      │   │
│    │元数据提取 │    │TextSplitter│    │Captioning  │    │Sparse:BM25 │    │幂等写入    │   │
│    └────────────┘    └────────────┘    └────────────┘    └────────────┘    └────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                Libs 层 (可插拔抽象层)                                        │
│                                                                                             │
│    ┌────────────────────────────────────────────────────────────────────────────────┐       │
│    │                            Factory Pattern (工厂模式)                           │       │
│    └────────────────────────────────────────────────────────────────────────────────┘       │
│                                           │                                                 │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐  │
│  │ LLM Client │ │ Embedding  │ │  Splitter  │ │VectorStore │ │  Reranker  │ │ Evaluator  │  │
│  │  Factory   │ │  Factory   │ │  Factory   │ │  Factory   │ │  Factory   │ │  Factory   │  │
│  ├────────────┤ ├────────────┤ ├────────────┤ ├────────────┤ ├────────────┤ ├────────────┤  │
│  │ · Azure    │ │ · OpenAI   │ │ · Recursive│ │ · Chroma   │ │ · None     │ │ · Ragas    │  │
│  │ · OpenAI   │ │ · BGE      │ │ · Semantic │ │ · Qdrant   │ │ · CrossEnc │ │ · DeepEval │  │
│  │ · Ollama   │ │ · Ollama   │ │ · FixedLen │ │ · Pinecone │ │ · LLM      │ │ · Custom   │  │
│  │ · DeepSeek │ │ · ...      │ │ · ...      │ │ · ...      │ │            │ │            │  │
│  │ · Vision✨ │ │            │ │            │ │            │ │            │ │            │  │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘ └────────────┘ └────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                             Observability 层 (可观测性)                                      │
│                                                                                             │
│    ┌──────────────────────────────────────┐    ┌──────────────────────────────────────┐     │
│    │          Trace Context               │    │         Web Dashboard                │     │
│    │   trace_id | stages[] | metrics      │    │        (Streamlit)                   │     │
│    │   record_stage() | finish()          │    │    请求列表 | 耗时瀑布图 | 详情展开   │     │
│    └──────────────────────────────────────┘    └──────────────────────────────────────┘     │
│                                                                                             │
│    ┌──────────────────────────────────────┐    ┌──────────────────────────────────────┐     │
│    │          Evaluation Module           │    │         Structured Logger            │     │
│    │   Hit Rate | MRR | Faithfulness      │    │    JSON Formatter | File Handler     │     │
│    └──────────────────────────────────────┘    └──────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 目录结构

```
smart-knowledge-hub/
│
├── config/                              # 配置文件目录
│   ├── settings.yaml                    # 主配置文件 (LLM/Embedding/VectorStore 配置)
│   └── prompts/                         # Prompt 模板目录
│       ├── image_captioning.txt         # 图片描述生成 Prompt
│       ├── chunk_refinement.txt         # Chunk 重写 Prompt
│       └── rerank.txt                   # LLM Rerank Prompt
│
├── src/                                 # 源代码主目录
│   │
│   ├── mcp_server/                      # MCP Server 层 (接口层)
│   │   ├── __init__.py
│   │   ├── server.py                    # MCP Server 入口 (Stdio Transport)
│   │   ├── protocol_handler.py          # JSON-RPC 协议处理
│   │   └── tools/                       # MCP Tools 定义
│   │       ├── __init__.py
│   │       ├── query_knowledge_hub.py   # 主检索工具
│   │       ├── list_collections.py      # 列出集合工具
│   │       └── get_document_summary.py  # 文档摘要工具
│   │
│   ├── core/                            # Core 层 (核心业务逻辑)
│   │   ├── __init__.py
│   │   ├── settings.py                   # 配置加载与校验 (Settings：load_settings/validate_settings)
│   │   ├── types.py                      # 核心数据类型/契约（Document/Chunk/ChunkRecord），供 ingestion/retrieval/mcp 复用
│   │   │
│   │   ├── query_engine/                # 查询引擎模块
│   │   │   ├── __init__.py
│   │   │   ├── query_processor.py       # 查询预处理 (关键词提取/查询扩展)
│   │   │   ├── hybrid_search.py         # 混合检索引擎 (Dense + Sparse + RRF)
│   │   │   ├── dense_retriever.py       # 稠密向量检索
│   │   │   ├── sparse_retriever.py      # 稀疏检索 (BM25)
│   │   │   ├── fusion.py                # 结果融合 (RRF 算法)
│   │   │   └── reranker.py              # 重排序模块 (None/CrossEncoder/LLM)
│   │   │
│   │   ├── response/                    # 响应构建模块
│   │   │   ├── __init__.py
│   │   │   ├── response_builder.py      # 响应构建器
│   │   │   ├── citation_generator.py    # 引用生成器
│   │   │   └── multimodal_assembler.py  # 多模态内容组装 (Text + Image)
│   │   │
│   │   └── trace/                       # 追踪模块
│   │       ├── __init__.py
│   │       ├── trace_context.py         # 追踪上下文 (trace_id/stages)
│   │       └── trace_collector.py       # 追踪收集器
│   │
│   ├── ingestion/                       # Ingestion Pipeline (离线数据摄取)
│   │   ├── __init__.py
│   │   ├── pipeline.py                  # Pipeline 主流程编排 (支持 on_progress 回调)
│   │   ├── document_manager.py          # 文档生命周期管理 (list/delete/stats)
│   │   │
│   │   ├── chunking/                    # Chunking 模块 (文档切分)
│   │   │   ├── __init__.py
│   │   │   └── document_chunker.py      # Document → Chunks 转换（调用 libs.splitter）
│   │   │
│   │   ├── transform/                   # Transform 模块 (增强处理)
│   │   │   ├── __init__.py
│   │   │   ├── base_transform.py        # Transform 抽象基类
│   │   │   ├── chunk_refiner.py         # Chunk 智能重组/去噪
│   │   │   ├── metadata_enricher.py     # 语义元数据注入 (Title/Summary/Tags)
│   │   │   └── image_captioner.py       # 图片描述生成 (Vision LLM)
│   │   │
│   │   ├── embedding/                   # Embedding 模块 (向量化)
│   │   │   ├── __init__.py
│   │   │   ├── dense_encoder.py         # 稠密向量编码
│   │   │   ├── sparse_encoder.py        # 稀疏向量编码 (BM25)
│   │   │   └── batch_processor.py       # 批处理优化
│   │   │
│   │   └── storage/                     # Storage 模块 (存储)
│   │       ├── __init__.py
│   │       ├── vector_upserter.py       # 向量库 Upsert
│   │       ├── bm25_indexer.py          # BM25 索引构建
│   │       └── image_storage.py         # 图片文件存储
│   │
│   ├── libs/                            # Libs 层 (可插拔抽象层)
│   │   ├── __init__.py
│   │   │
│   │   ├── loader/                      # Loader 抽象 (文档加载)
│   │   │   ├── __init__.py
│   │   │   ├── base_loader.py           # Loader 抽象基类
│   │   │   ├── pdf_loader.py            # PDF Loader (MarkItDown)
│   │   │   └── file_integrity.py        # 文件完整性检查 (SHA256 哈希)
│   │   │
│   │   ├── llm/                         # LLM 抽象
│   │   │   ├── __init__.py
│   │   │   ├── base_llm.py              # LLM 抽象基类
│   │   │   ├── llm_factory.py           # LLM 工厂
│   │   │   ├── azure_llm.py             # Azure OpenAI 实现
│   │   │   ├── openai_llm.py            # OpenAI 实现
│   │   │   ├── ollama_llm.py            # Ollama 本地模型实现
│   │   │   ├── deepseek_llm.py          # DeepSeek 实现
│   │   │   ├── base_vision_llm.py       # Vision LLM 抽象基类（支持图像输入）
│   │   │   └── azure_vision_llm.py      # Azure Vision 实现 (GPT-4o/GPT-4-Vision)
│   │   │
│   │   ├── embedding/                   # Embedding 抽象
│   │   │   ├── __init__.py
│   │   │   ├── base_embedding.py        # Embedding 抽象基类
│   │   │   ├── embedding_factory.py     # Embedding 工厂
│   │   │   ├── openai_embedding.py      # OpenAI Embedding 实现
│   │   │   ├── azure_embedding.py       # Azure Embedding 实现
│   │   │   └── ollama_embedding.py      # Ollama 本地模型实现
│   │   │
│   │   ├── splitter/                    # Splitter 抽象 (切分策略)
│   │   │   ├── __init__.py
│   │   │   ├── base_splitter.py         # Splitter 抽象基类
│   │   │   ├── splitter_factory.py      # Splitter 工厂
│   │   │   ├── recursive_splitter.py    # RecursiveCharacterTextSplitter 实现
│   │   │   ├── semantic_splitter.py     # 语义切分实现
│   │   │   └── fixed_length_splitter.py # 定长切分实现
│   │   │
│   │   ├── vector_store/                # VectorStore 抽象
│   │   │   ├── __init__.py
│   │   │   ├── base_vector_store.py     # VectorStore 抽象基类
│   │   │   ├── vector_store_factory.py  # VectorStore 工厂
│   │   │   └── chroma_store.py          # Chroma 实现
│   │   │
│   │   ├── reranker/                    # Reranker 抽象
│   │   │   ├── __init__.py
│   │   │   ├── base_reranker.py         # Reranker 抽象基类
│   │   │   ├── reranker_factory.py      # Reranker 工厂
│   │   │   ├── cross_encoder_reranker.py# CrossEncoder 实现
│   │   │   └── llm_reranker.py          # LLM Rerank 实现
│   │   │
│   │   └── evaluator/                   # Evaluator 抽象
│   │       ├── __init__.py
│   │       ├── base_evaluator.py        # Evaluator 抽象基类
│   │       ├── evaluator_factory.py     # Evaluator 工厂
│   │       ├── custom_evaluator.py      # 自定义指标实现
│   │       └── ragas_evaluator.py       # Ragas 评估实现
│   │
│   └── observability/                   # Observability 层 (可观测性)
│       ├── __init__.py
│       ├── logger.py                    # 结构化日志 (JSON Formatter)
│       ├── dashboard/                   # Web Dashboard (可视化管理平台)
│       │   ├── __init__.py
│       │   ├── app.py                   # Streamlit 入口 (页面导航注册)
│       │   ├── pages/                   # 六大功能页面
│       │   │   ├── overview.py          # 系统总览 (组件配置 + 数据统计)
│       │   │   ├── data_browser.py      # 数据浏览器 (文档/Chunk/图片查看)
│       │   │   ├── ingestion_manager.py # Ingestion 管理 (触发摄取/删除文档)
│       │   │   ├── ingestion_traces.py  # Ingestion 追踪 (摄取历史与详情)
│       │   │   ├── query_traces.py      # Query 追踪 (查询历史与详情)
│       │   │   └── evaluation_panel.py  # 评估面板 (运行评估/查看指标)
│       │   └── services/                # Dashboard 数据服务层
│       │       ├── trace_service.py     # Trace 读取服务 (解析 traces.jsonl)
│       │       ├── data_service.py      # 数据浏览服务 (ChromaStore/ImageStorage)
│       │       └── config_service.py    # 配置读取服务 (Settings 展示)
│       └── evaluation/                  # 评估模块
│           ├── __init__.py
│           └── eval_runner.py           # 评估执行器

│
├── data/                                # 数据目录
│   ├── documents/                       # 原始文档存放
│   │   └── {collection}/                # 按集合分类
│   ├── images/                          # 提取的图片存放
│   │   └── {collection}/                # 按集合分类（实际存储在 {doc_hash}/ 子目录下）
│   └── db/                              # 数据库与索引文件目录
│       ├── ingestion_history.db         # 文件完整性历史记录 (SQLite)
│       │                                # 表结构：file_hash, file_path, status, processed_at, error_msg
│       │                                # 用途：增量摄取，避免重复处理未变更文件
│       ├── image_index.db               # 图片索引映射 (SQLite)
│       │                                # 表结构：image_id, file_path, collection, doc_hash, page_num
│       │                                # 用途：快速查询 image_id → 本地文件路径，支持图片检索与引用
│       ├── chroma/                      # Chroma 向量库目录
│       │                                # 存储 Dense Vector、Sparse Vector 与 Chunk Metadata
│       └── bm25/                        # BM25 索引目录
│                                        # 存储倒排索引与 IDF 统计信息（当前使用 pickle）
│
├── cache/                               # 缓存目录
│   ├── embeddings/                      # Embedding 缓存 (按内容哈希)
│   ├── captions/                        # 图片描述缓存
│   └── processing/                      # 处理状态缓存 (文件哈希/Chunk 哈希)
│
├── logs/                                # 日志目录
│   ├── traces.jsonl                     # 追踪日志 (JSON Lines)
│   └── app.log                          # 应用日志
│
├── tests/                               # 测试目录
│   ├── unit/                            # 单元测试
│   │   ├── test_dense_retriever.py      # D2: 稠密检索器测试
│   │   ├── test_sparse_retriever.py     # D3: 稀疏检索器测试
│   │   ├── test_fusion_rrf.py           # D4: RRF 融合测试
│   │   ├── test_reranker_fallback.py    # D6: Reranker 回退测试
│   │   ├── test_protocol_handler.py     # E2: 协议处理器测试
│   │   ├── test_response_builder.py     # E3: 响应构建器测试
│   │   ├── test_list_collections.py     # E4: 集合列表工具测试
│   │   ├── test_get_document_summary.py # E5: 文档摘要工具测试
│   │   ├── test_trace_context.py        # F1: 追踪上下文测试
│   │   ├── test_jsonl_logger.py         # F2: JSON Lines 日志测试
│   │   └── ...                          # 其他已有单元测试
│   ├── integration/                     # 集成测试
│   │   ├── test_ingestion_pipeline.py
│   │   ├── test_hybrid_search.py        # D5: 混合检索集成测试
│   │   └── test_mcp_server.py           # E1-E6: MCP 服务器集成测试
│   ├── e2e/                             # 端到端测试
│   │   ├── test_data_ingestion.py
│   │   ├── test_recall.py               # G2: 召回回归测试
│   │   └── test_mcp_client.py           # G1: MCP Client 模拟测试
│   └── fixtures/                        # 测试数据
│       ├── sample_documents/
│       └── golden_test_set.json         # F5/G2: 黄金测试集
│
├── scripts/                             # 脚本目录
│   ├── ingest.py                        # 数据摄取脚本（离线摄取入口）
│   ├── query.py                         # 查询测试脚本（在线查询入口）
│   ├── evaluate.py                      # 评估运行脚本
│   └── start_dashboard.py               # Dashboard 启动脚本
│
├── main.py                              # MCP Server 启动入口
├── pyproject.toml                       # Python 项目配置
├── requirements.txt                     # 依赖列表
└── README.md                            # 项目说明
```

### 5.3 模块说明

#### 5.3.1 MCP Server 层

| 模块 | 职责 | 关键技术点 |
|-----|-----|----------|
| `server.py` | MCP Server 主入口，处理 Stdio Transport 通信 | Python MCP SDK，JSON-RPC 2.0 |
| `protocol_handler.py` | 协议解析与能力协商 | `initialize`、`tools/list`、`tools/call` |
| `tools/*` | 对外暴露的工具函数实现 | 装饰器定义，参数校验，响应格式化 |

#### 5.3.2 Core 层

| 模块 | 职责 | 关键技术点 |
|-----|-----|----------|
| `settings.py` | 配置加载与校验 | 读取 `config/settings.yaml`，解析为 `Settings`，必填字段校验（fail-fast） |
| `types.py` | 核心数据类型/契约（全链路复用） | 定义 `Document/Chunk/ChunkRecord/ProcessedQuery/RetrievalResult`；序列化稳定；作为 ingestion/retrieval/mcp 的数据契约中心 |
| `query_processor.py` | 查询预处理 | 关键词提取、同义词扩展、Metadata 解析 |
| `query_orchestrator.py` | 查询编排 | Expansion Planner、模式判定、子查询生成、回退策略、Trace 记录 |
| `hybrid_search.py` | 混合检索编排 | 并行 Dense/Sparse 召回，结果融合，Metadata 过滤 |
| `multi_query_merger.py` | 多 Query 结果合并 | 跨子查询去重、RRF 融合、多列表聚合、失败降级 |
| `dense_retriever.py` | 语义向量检索 | Query Embedding + VectorStore 检索，Cosine Similarity |
| `sparse_retriever.py` | BM25 关键词检索 | 倒排索引查询，TF-IDF 打分 |
| `fusion.py` | 结果融合 | RRF 算法，排名倒数加权 |
| `reranker.py` | 精排重排 | CrossEncoder / LLM Rerank / Fallback 回退 |
| `response_builder.py` | 响应构建 | MCP 响应格式化，Markdown 生成 |
| `citation_generator.py` | 引用生成 | 从检索结果生成结构化引用列表 |
| `multimodal_assembler.py` | 多模态组装 | Text + Image Base64 编码，MCP 多内容类型 |
| `trace_context.py` | 追踪上下文 | trace_id 生成，阶段记录，finish 汇总 |
| `trace_collector.py` | 追踪收集器 | 收集 trace 并触发持久化到 JSON Lines |

#### 5.3.3 Scripts 层（命令行入口）

| 脚本 | 职责 | 关键技术点 |
|-----|-----|----------|
| `ingest.py` | 离线数据摄取入口 | CLI 参数解析，调用 Ingestion Pipeline，支持 `--collection`/`--path`/`--force` |
| `query.py` | 在线查询测试入口 | CLI 参数解析，调用 HybridSearch + Reranker，支持 `--query`/`--top-k`/`--verbose` |
| `evaluate.py` | 评估运行入口 | 加载 golden_test_set，运行评估，输出 metrics |
| `start_dashboard.py` | Dashboard 启动入口 | Streamlit 应用启动 |

#### 5.3.4 Ingestion Pipeline 层

| 模块 | 职责 | 关键技术点 |
|-----|-----|----------|
| `pipeline.py` | Pipeline 流程编排 | 串行执行（或分阶段可观测），异常处理，增量更新；支持 `on_progress` 回调；统一使用 `core/types.py` 的数据契约 |
| `document_manager.py` | 文档生命周期管理 | list/delete/stats 操作；跨 4 个存储（Chroma/BM25/ImageStorage/FileIntegrity）的协调删除；供 Dashboard 与 CLI 调用 |

| `chunking/document_chunker.py` | Document→Chunks 转换 | 调用 `libs.splitter` 进行文本切分；生成稳定 Chunk ID（格式：`{doc_id}_{index:04d}_{hash}`）；继承 metadata；建立 source_ref 溯源链接 |
| `transform/base_transform.py` | Transform 抽象 | 原子化、幂等；可独立重试；失败降级不阻塞 |
| `transform/chunk_refiner.py` | Chunk 智能重组 | 规则去噪 + 可选 LLM 二次加工；可回退 |
| `transform/metadata_enricher.py` | 元数据增强 | Title/Summary/Tags 规则生成 + 可选 LLM 增强 |
| `transform/image_captioner.py` | 图片描述生成 | Vision LLM；写回 metadata/text；禁用/失败降级 |
| `embedding/dense_encoder.py` | 稠密向量编码 | 通过 `libs.embedding` 调用具体 provider；批处理 |
| `embedding/sparse_encoder.py` | 稀疏向量编码 | BM25 编码/统计（或替换实现）；批处理 |
| `storage/vector_upserter.py` | 向量存储写入 | 通过 `libs.vector_store` Upsert；幂等；metadata 完整 |

#### 5.3.5 Libs 层 (可插拔抽象)

| 抽象接口 | 当前默认实现 | 可替换选项 |
|---------|------------|----------|
| `LLMClient` | Azure OpenAI | OpenAI / Ollama / DeepSeek |
| `VisionLLMClient` | Azure OpenAI Vision (GPT-4o) | OpenAI Vision / Ollama Vision (LLaVA) |
| `EmbeddingClient` | OpenAI text-embedding-3 | BGE / Ollama 本地模型 |
| `Loader` | PDF Loader（MarkItDown） | Markdown/HTML/Code Loader 等 |
| `FileIntegrity` | SQLite (`data/db/ingestion_history.db`) | Redis（分布式）/ PostgreSQL（企业级）/ JSON文件（测试） |
| `Splitter` | RecursiveCharacterTextSplitter | Semantic / FixedLen |
| `VectorStore` | Chroma | Qdrant / Pinecone / Milvus |
| `Reranker` | CrossEncoder | LLM Rerank / None (关闭) |
| `Evaluator` | Ragas | DeepEval / 自定义指标 |

#### 5.3.6 Observability 层

| 模块 | 职责 | 关键技术点 |
|-----|-----|----------|
| `logger.py` | 结构化日志 | JSON Formatter，JSON Lines 输出 |
| `trace_context.py` | 请求级追踪 | trace_id，trace_type（query/ingestion），阶段耗时记录，`finish()` + `to_dict()` 序列化 |
| `trace_collector.py` | 追踪收集器 | 收集 trace 并触发持久化到 JSON Lines |
| `dashboard/app.py` | Dashboard 入口 | Streamlit 多页面应用，`st.navigation` 页面注册 |
| `dashboard/pages/overview.py` | 系统总览 | 组件配置卡片，数据资产统计 |
| `dashboard/pages/data_browser.py` | 数据浏览器 | 文档列表，Chunk 详情，图片预览 |
| `dashboard/pages/ingestion_manager.py` | Ingestion 管理 | 文件上传，摄取触发（进度条），文档删除 |
| `dashboard/pages/ingestion_traces.py` | Ingestion 追踪 | 摄取历史，阶段耗时瀑布图 |
| `dashboard/pages/query_traces.py` | Query 追踪 | 查询历史，Dense/Sparse 对比，Rerank 变化 |
| `dashboard/pages/evaluation_panel.py` | 评估面板 | 运行评估，指标展示，历史趋势（Phase H 实现） |
| `dashboard/services/trace_service.py` | Trace 数据服务 | 解析 traces.jsonl，按 trace_type 分类 |
| `dashboard/services/data_service.py` | 数据浏览服务 | 封装 ChromaStore/ImageStorage 读取 |
| `dashboard/services/config_service.py` | 配置读取服务 | 封装 Settings 展示 |
| `evaluation/eval_runner.py` | 评估执行 | 黄金测试集，指标计算，报告生成 |
| `evaluation/ragas_evaluator.py` | Ragas 评估 | Faithfulness, Answer Relevancy, Context Precision |


### 5.4 数据流说明

#### 5.4.1 离线数据摄取流 (Ingestion Flow)

```
原始文档 (PDF)
      │
      ▼
┌─────────────────┐     未变更则跳过
│ File Integrity  │───────────────────────────► 结束
│   (SHA256)      │
└────────┬────────┘
         │ 新文件/已变更
         ▼
┌─────────────────┐
│     Loader      │  PDF → Markdown + 图片提取 + 元数据收集
│   (MarkItDown)  │
└────────┬────────┘
         │ Document (text + metadata.images)
         ▼
┌─────────────────┐
│    Splitter     │  按语义边界切分，保留图片引用
│ (Recursive)     │
└────────┬────────┘
         │ Chunks[] (with image_refs)
         ▼
┌─────────────────┐
│   Transform     │  LLM 重写 + 元数据注入 + 图片描述生成
│ (Enrichment)    │
└────────┬────────┘
         │ Enriched Chunks[] (with captions in text)
         ▼
┌─────────────────┐
│   Embedding     │  Dense (OpenAI) + Sparse (BM25) 双路编码
│  (Dual Path)    │
└────────┬────────┘
         │ Vectors + Chunks + Metadata
         ▼
┌─────────────────┐
│    Upsert       │  Chroma Upsert (幂等) + BM25 Index + 图片存储
│   (Storage)     │
└─────────────────┘
```

#### 5.4.2 在线查询流 (Query Flow)

```
用户查询 (via MCP Client)
      │
      ▼
┌─────────────────┐
│  MCP Server     │  JSON-RPC 解析，工具路由
│ (Stdio Transport)│
└────────┬────────┘
         │ query + params
         ▼
┌─────────────────┐
│ Query Processor │  关键词提取 + 同义词扩展 + Metadata 解析
│                 │
└────────┬────────┘
         │ processed_query + filters
         ▼
┌─────────────────────────────────────────────┐
│              Hybrid Search                  │
│  ┌─────────────┐          ┌─────────────┐   │
│  │Dense Retrieval│  并行   │Sparse Retrieval│   │
│  │ (Embedding)  │◄───────►│  (BM25)     │   │
│  └──────┬──────┘          └──────┬──────┘   │
│         │                        │          │
│         └────────┬───────────────┘          │
│                  ▼                          │
│         ┌─────────────┐                     │
│         │   Fusion    │  RRF 融合           │
│         │   (RRF)     │                     │
│         └──────┬──────┘                     │
└────────────────┼────────────────────────────┘
                 │ Top-M 候选
                 ▼
┌─────────────────┐
│    Reranker     │  CrossEncoder / LLM / None
│   (Optional)    │
└────────┬────────┘
         │ Top-K 精排结果
         ▼
┌─────────────────┐
│ Response Builder│  引用生成 + 图片 Base64 编码 + MCP 格式化
│                 │
└────────┬────────┘
         │ MCP Response (TextContent + ImageContent)
         ▼
返回给 MCP Client (Copilot / Claude Desktop)
```

#### 5.4.3 管理操作流 (Management Flow)

```
Dashboard (Streamlit UI)
      │
      ├─── 数据浏览 ──────────────────────────────────────────┐
      │                                                       │
      │    DataService                                        │
      │    ├── ChromaStore.get_by_metadata(source=...)        │
      │    ├── ImageStorage.list_images(collection, doc_hash) │
      │    └── 返回文档列表 / Chunk 详情 / 图片预览            │
      │                                                       │
      ├─── Ingestion 管理 ────────────────────────────────────┤
      │                                                       │
      │    触发摄取：                                          │
      │    ├── IngestionPipeline.run(path, collection,        │
      │    │                         on_progress=callback)    │
      │    └── st.progress() 实时更新进度                      │
      │                                                       │
      │    删除文档：                                          │
      │    ├── DocumentManager.delete_document(source, col)   │
      │    │   ├── ChromaStore.delete_by_metadata(source=...) │
      │    │   ├── BM25Indexer.remove_document(source=...)    │
      │    │   ├── ImageStorage.delete_images(col, doc_hash)  │
      │    │   └── FileIntegrity.remove_record(file_hash)     │
      │    └── 刷新文档列表                                    │
      │                                                       │
      └─── Trace 查看 ───────────────────────────────────────┘
           │
           TraceService
           ├── 读取 logs/traces.jsonl
           ├── 按 trace_type 分类 (query / ingestion)
           └── 返回 Trace 列表与详情
```

### 5.5 配置驱动设计


系统通过 `config/settings.yaml` 统一配置各组件实现，支持零代码切换：

```yaml
# config/settings.yaml 示例

# LLM 配置
llm:
  provider: azure           # azure | openai | ollama | deepseek
  model: gpt-4o
  azure_endpoint: "..."
  api_key: "${AZURE_API_KEY}"

# Embedding 配置
embedding:
  provider: openai          # openai | azure | ollama (本地)
  model: text-embedding-3-small
  
# Vision LLM 配置 (图片描述)
vision_llm:
  provider: azure           # azure | dashscope (Qwen-VL)
  model: gpt-4o
  
# 向量存储配置
vector_store:
  backend: chroma           # chroma | qdrant | pinecone
  persist_path: ./data/db/chroma

# 检索配置
retrieval:
  sparse_backend: bm25      # bm25 | elasticsearch
  fusion_algorithm: rrf     # rrf | weighted_sum
  top_k_dense: 20
  top_k_sparse: 20
  top_k_final: 10

# 重排配置
rerank:
  enabled: false
  provider: none            # none | cross_encoder | llm
  model: cross-encoder/ms-marco-MiniLM-L-6-v2
  top_k: 5

# 评估配置
evaluation:
  enabled: false
  provider: custom          # custom | ragas
  metrics: [hit_rate, mrr]

# 可观测性配置
observability:
  enabled: true
  log_file: ./logs/traces.jsonl

# Dashboard 管理平台配置
dashboard:
  enabled: true
  port: 8501                     # Streamlit 服务端口
  traces_dir: ./logs             # Trace 日志文件目录
  auto_refresh: true             # 是否自动刷新（轮询新 trace）
  refresh_interval: 5            # 自动刷新间隔（秒）
```

**Rerank 配置说明**：

- `enabled`：是否启用重排；为 `false` 时即使填写了其他字段，也会退化为 `NoneReranker`。
- `provider`：可选 `none` / `cross_encoder` / `llm`。
- `model`：
  - 当 `provider: cross_encoder` 时，`rerank.model` 为实际加载的 Cross-Encoder 模型标识。既可以填写 Hugging Face 模型名（例如 `cross-encoder/ms-marco-MiniLM-L-6-v2`），也可以填写本地模型目录绝对路径。
  - 若填写 Hugging Face 模型名，当前实现会直接调用 `sentence-transformers` 的 `CrossEncoder(model_name)`；若本地无缓存，通常会按底层库默认行为自动下载并缓存模型，然后再加载。
  - 若填写本地路径，该路径必须是一个可被 `CrossEncoder(path)` 正常识别的完整模型目录，而不只是随意下载的若干文件。
  - 当 `provider: llm` 时，当前实现会复用主 `llm` 配置创建 `LLMReranker`，真正决定调用哪个云端大模型的是 `llm.provider`、`llm.model` 以及对应的 `api_key` / `base_url` / `azure_endpoint` 等字段；`rerank.model` 在该模式下主要作为占位/兼容字段保留。
- `top_k`：重排后最终保留的结果数量。

**推荐配置示例**：

- 关闭重排：

  ```yaml
  rerank:
    enabled: false
    provider: "none"
    model: "cross-encoder/ms-marco-MiniLM-L-6-v2"
    top_k: 5
  ```

- 使用 Cross-Encoder 重排：

  ```yaml
  rerank:
    enabled: true
    provider: "cross_encoder"
    model: "cross-encoder/ms-marco-MiniLM-L-6-v2"
    top_k: 5
  ```

- 使用 LLM 重排（复用主 `llm` 配置）：

  ```yaml
  llm:
    provider: "deepseek"
    model: "deepseek-v4-pro"
    api_key: "${DEEPSEEK_API_KEY}"
    temperature: 0.0
    max_tokens: 4096
  
  rerank:
    enabled: true
    provider: "llm"
    model: "deepseek-v4-pro"   # 当前实现中实际由上面的 llm 配置决定
    top_k: 5
  ```

### 5.6 扩展性设计要点


1. **新增 LLM Provider**：实现 `BaseLLM` 接口，在 `llm_factory.py` 注册，配置文件指定 `provider` 即可
2. **新增文档格式**：实现 `BaseLoader` 接口，在 Pipeline 中注册对应文件扩展名的处理器
3. **新增检索策略**：实现检索接口，在 `hybrid_search.py` 中组合调用
4. **新增评估指标**：实现 `BaseEvaluator` 接口，并在评估配置中通过 `provider` / `metrics` 暴露使用。


## 6. 项目开发规划

> 本节作为本项目唯一的开发规划基线，统一整合原“阶段总览、进度跟踪、逐阶段任务拆解、阶段 J 增强规划、交付里程碑”等内容，避免信息重复、状态冲突和描述散落。  
> 当前仓库对应的主线阶段 `A-I` 与增强阶段 `J` 已全部收口，可同时用于“回顾实现路径、继续迭代增强、面试/教学/演示复现”。

### 6.1 规划原则

- **严格对齐架构设计**：以第 `5.2` 节目录树和第 `5.4` 节链路设计为交付约束，每个阶段都必须在文件系统、配置、测试或运行入口上留下可见产物。
- **按可验收增量推进**：默认将任务切成约 `1h` 的可验证步长，每一步同时给出“实现目标、交付物、验收标准、测试方法”。
- **先主闭环，后增强项**：优先打通 `Ingestion -> Retrieval -> MCP Tool` 主链路，再补默认后端、Trace、Dashboard、Evaluation 与 Query Orchestration。
- **外部依赖全部可替换**：`LLM`、`Embedding`、`Vision LLM`、`VectorStore`、`Reranker`、`Evaluator` 一律通过抽象接口和工厂接入，单元测试使用 Fake/Mock，集成测试再验证真实后端。
- **规划与实现双向校验**：开发规划不仅描述“应该做什么”，还要反映“当前代码已交付到什么程度”，因此每个阶段都显式记录当前状态。

### 6.2 阶段主线与依赖

```text
阶段 A  工程骨架与测试基座
   -> 阶段 B  Libs 可插拔层
   -> 阶段 C  Ingestion Pipeline
   -> 阶段 D  Retrieval
   -> 阶段 E  MCP Server 与 Tools
   -> 阶段 F  Trace 与结构化日志
   -> 阶段 G  Dashboard 管理平台
   -> 阶段 H  评估体系
   -> 阶段 I  E2E 验收与文档收口

阶段 J  Query Orchestration 增强
   在阶段 D/E 稳定后横向接入，依赖：
   J1 配置与类型契约
      -> J2 Planner
      -> J3 Synonym Expansion
      -> J4 Decomposition Execution
      -> J5 Multi-Query Merge
      -> J6 MCP Tool Integration
      -> J7 Trace + Dashboard 适配
      -> J8 测试矩阵与回归基线
```

### 6.3 阶段总览与当前状态

| 阶段 | 目标 | 关键交付 | 当前状态 |
|------|------|---------|---------|
| 阶段 A | 建立可运行、可配置、可测试的工程骨架 | 目录树、`Settings`、pytest 基座、最小入口 | 已完成 |
| 阶段 B | 将“可替换”落实为代码事实 | `Base*` 抽象、`Factory`、默认 provider 实现、Vision LLM 接入 | 已完成 |
| 阶段 C | 打通离线摄取主链路 | PDF Loader、Chunking、Transform、Embedding、BM25、Vector Upsert、`ingest.py` | 已完成 |
| 阶段 D | 打通在线检索主链路 | QueryProcessor、Dense/Sparse Retriever、RRF、Reranker、`query.py` | 已完成 |
| 阶段 E | 以 MCP 协议暴露检索能力 | `server.py`、协议处理、3 个 MCP Tools、多模态响应组装 | 已完成 |
| 阶段 F | 建立白盒化可观测能力 | `TraceContext`、JSON Lines、Query/Ingestion 双链路打点、进度回调 | 已完成 |
| 阶段 G | 提供可视化管理与追踪入口 | Streamlit 六页面、`DocumentManager`、Trace 可视化 | 已完成 |
| 阶段 H | 建立可量化评估闭环 | `RagasEvaluator`、`EvalRunner`、golden test set、评估面板、Recall 回归 | 已完成 |
| 阶段 I | 完成交付收口与可复现验证 | MCP E2E、Dashboard 冒烟、README、契约测试、全链路验收 | 已完成 |
| 阶段 J | 在不破坏主链路的前提下增强服务端检索编排 | Planner、同义扩展、逻辑拆解、多 Query 合并、MCP/Trace/Dashboard 适配 | 已完成 |

### 6.4 当前进度快照

| 阶段 | 任务位 | 已完成 | 已取消 | 备注 |
|------|-------|--------|--------|------|
| 阶段 A | 3 | 3 | 0 | `2026-01-26` 完成基础骨架 |
| 阶段 B | 16 | 16 | 0 | `2026-01-27 ~ 2026-01-31` 完成抽象层与默认实现 |
| 阶段 C | 15 | 15 | 0 | `2026-01-30 ~ 2026-02-02` 完成摄取主链路 |
| 阶段 D | 7 | 7 | 0 | `2026-02-03 ~ 2026-02-04` 完成混合检索主链路 |
| 阶段 E | 6 | 6 | 0 | `2026-02-04` 完成 MCP 对外能力 |
| 阶段 F | 5 | 5 | 0 | `2026-02-08` 完成 Trace 基础设施 |
| 阶段 G | 6 | 6 | 0 | `2026-02-09` 完成 Dashboard 六页面 |
| 阶段 H | 5 | 4 | 1 | `H2` 经方案收敛后移除，保留 `custom + ragas` 双评估后端 |
| 阶段 I | 5 | 5 | 0 | `2026-02-23 ~ 2026-02-24` 完成交付收口 |
| 阶段 J | 8 | 8 | 0 | 已完成 Query Orchestration 增强 |
| **总计** | **76** | **75** | **1** | **从交付视角已 100% 收口** |

### 6.5 分阶段详细规划

#### 阶段 A：工程骨架与测试基座

**阶段目标**：先可导入，再可测试；建立后续所有模块共享的目录、配置、入口与测试约定。

- `A1` 初始化目录树与最小可运行入口：创建 `main.py`、`pyproject.toml`、`README.md`、`.gitignore`、`config/settings.yaml`、`config/prompts/` 与 `src/**/__init__.py` 等骨架文件，确保关键顶层包可 import；以 `python -m compileall src` 为基础验收。`已完成，2026-01-26`
- `A2` 引入 pytest 并建立测试目录约定：建立 `tests/unit`、`tests/integration`、`tests/e2e`、`tests/fixtures` 结构，在 `pyproject.toml` 中补齐 pytest 配置与 markers，以冒烟 import 测试验证测试基座可用。`已完成，2026-01-26`
- `A3` 配置加载与校验：在 `src/core/settings.py` 中实现 `Settings`、`load_settings()`、`validate_settings()`，由 `main.py` 启动时 fail-fast 校验关键配置，保证缺字段时直接报出可读错误。`已完成，2026-01-26`

**阶段交付物**：项目骨架、配置模型、pytest 约定、最小入口、Prompt 模板目录。  
**退出标准**：关键模块可导入、配置可加载、最小测试可运行。

#### 阶段 B：Libs 可插拔层

**阶段目标**：把“可替换”从设计理念变成代码事实，并补齐主链路必须依赖的默认 provider 实现。

- `B1` LLM 抽象接口与工厂：定义 `BaseLLM` 与 `LLMFactory.create(settings)`，通过 Fake provider 验证路由逻辑。`已完成，2026-01-27`
- `B2` Embedding 抽象接口与工厂：定义 `BaseEmbedding.embed(texts, trace)` 与 `EmbeddingFactory`，保证批量向量化契约稳定。`已完成，2026-01-27`
- `B3` Splitter 抽象接口与工厂：定义 `BaseSplitter` 与 `SplitterFactory`，支持按配置切换分块策略。`已完成，2026-01-27`
- `B4` VectorStore 抽象接口与工厂：定义 `BaseVectorStore.upsert/query` 等基础契约，以 contract tests 锁定输入输出 shape。`已完成，2026-01-27`
- `B5` Reranker 抽象接口与工厂：定义 `BaseReranker` 与 `RerankerFactory`，提供 `NoneReranker` 作为默认回退实现。`已完成，2026-01-27`
- `B6` Evaluator 抽象接口与工厂：定义 `BaseEvaluator` 与 `EvaluatorFactory`，先落地轻量 `CustomEvaluator`。`已完成，2026-01-27`
- `B7.1` OpenAI-Compatible LLM：实现 `OpenAILLM`、`AzureLLM`、`DeepSeekLLM`，统一 OpenAI-compatible chat 调用。`已完成，2026-01-28`
- `B7.2` Ollama LLM：支持本地 HTTP 模型调用与异常降级，确保本地模式可跑通。`已完成，2026-01-28`
- `B7.3` OpenAI 与 Azure Embedding：支持批量 embedding、维度校验和 provider 差异化配置。`已完成，2026-01-28`
- `B7.4` Ollama Embedding：支持本地 embedding 模型与批量向量化。`已完成，2026-01-28`
- `B7.5` Recursive Splitter 默认实现：封装 LangChain 切分逻辑，优先保证 Markdown 与代码块切分体验。`已完成，2026-01-28`
- `B7.6` ChromaStore 默认实现：完成 `upsert -> query` roundtrip、本地持久化与集成测试。`已完成，2026-01-30`
- `B7.7` LLM Reranker：读取 `config/prompts/rerank.txt`，输出结构化排序结果并提供失败信号。`已完成，2026-01-30`
- `B7.8` Cross-Encoder Reranker：支持本地或托管重排模型，提供超时/失败回退信号。`已完成，2026-01-30`
- `B8` Vision LLM 抽象接口与工厂集成：扩展 `LLMFactory.create_vision_llm()`，为图像理解预留独立抽象。`已完成，2026-01-31`
- `B9` Azure Vision LLM 实现：支持图片路径/base64 输入、压缩预处理和 Vision API 调用。`已完成，2026-01-31`

**阶段交付物**：`libs/*` 全部抽象层、工厂层、默认 provider 实现、Vision LLM 接入。  
**退出标准**：核心业务模块只依赖抽象接口，通过配置即可替换 provider。

#### 阶段 C：Ingestion Pipeline

**阶段目标**：打通 `PDF -> Markdown/Text -> Chunk -> Transform -> Embedding -> Store` 离线摄取链路，支持增量跳过与多模态信息保留。

- `C1` 核心数据类型/契约：在 `src/core/types.py` 中定义 `Document`、`Chunk`、`ChunkRecord`，明确 `metadata.images` 与 `[IMAGE: {image_id}]` 占位符规范。`已完成，2026-01-30`
- `C2` 文件完整性检查：实现 `FileIntegrityChecker` / `SQLiteIntegrityChecker`，用 SHA256 与 SQLite WAL 实现增量跳过。`已完成，2026-01-30`
- `C3` Loader 抽象与 PDF Loader：实现 `BaseLoader` 与 `PdfLoader`，支持 PDF 文本提取、图片抽取、占位符插入和失败降级。`已完成，2026-01-30`
- `C4` Splitter 集成：实现 `DocumentChunker`，负责 `Document -> List[Chunk]` 适配、稳定 `chunk_id`、元数据继承、图片引用按需分发和溯源。`已完成，2026-01-31`
- `C5` Transform 基类与 ChunkRefiner：定义 `BaseTransform`，先规则去噪、再可选 LLM 精炼，失败回退到规则结果。`已完成，2026-01-31`
- `C6` MetadataEnricher：为 chunk 生成 `title/summary/tags`，优先支持 LLM 增强，并保留规则兜底。`已完成，2026-01-31`
- `C7` ImageCaptioner：当 chunk 含图片引用且启用 Vision LLM 时生成 caption，否则保留引用并标记未处理图片。`已完成，2026-02-01`
- `C8` DenseEncoder：批量调用 `BaseEmbedding` 生成 dense vectors。`已完成，2026-02-01`
- `C9` SparseEncoder：输出 BM25 所需词项统计与稀疏表示。`已完成，2026-02-01`
- `C10` BatchProcessor：负责批处理编排、顺序稳定性和批次耗时记录。`已完成，2026-02-01`
- `C11` BM25Indexer：计算 IDF、构建倒排索引、支持序列化/加载/增量更新，为稀疏检索提供持久化基础。`已完成，2026-02-01`
- `C12` VectorUpserter：实现稳定 `chunk_id`、幂等 upsert 与批量写入顺序保证。`已完成，2026-02-01`
- `C13` ImageStorage：将图片保存到 `data/images/` 并以 SQLite 维护 `image_id -> path` 索引。`已完成，2026-02-01`
- `C14` Pipeline 编排：在 `src/ingestion/pipeline.py` 中串联 `integrity -> load -> split -> transform -> encode -> store` 全流程，并输出清晰异常。`已完成，2026-02-02`
- `C15` 脚本入口 `ingest.py`：提供 `--collection`、`--path`、`--force` 等离线摄取能力。`已完成，2026-02-02`

**阶段交付物**：完整离线摄取链路、BM25 与向量索引、本地图像索引、CLI 入口。  
**退出标准**：样例文档可被成功摄取到本地存储，重复执行能基于哈希跳过未变更文件。

#### 阶段 D：Retrieval

**阶段目标**：打通在线混合检索链路，返回带文本、分数、元数据与可追踪来源的 Top-K 结果。

- `D1` QueryProcessor：完成 query 预处理、关键词提取与 filters 解析，输出稳定的 `ProcessedQuery` 契约。`已完成，2026-02-03`
- `D2` DenseRetriever：组合 query embedding 与 `VectorStore.query()`，返回包含 `chunk_id/score/text/metadata` 的 `RetrievalResult`。`已完成，2026-02-03`
- `D3` SparseRetriever：基于 `BM25Indexer` 检索 `chunk_id`，再通过 `VectorStore.get_by_ids()` 回填文本与元数据。`已完成，2026-02-04`
- `D4` RRF Fusion：实现可配置 `k` 的 RRF 融合与确定性排序输出。`已完成，2026-02-04`
- `D5` HybridSearch：编排 `QueryProcessor + Dense + Sparse + Fusion + Metadata Filters`，并支持单路失败降级。`已完成，2026-02-04`
- `D6` Core 层 Reranker：接入 `libs.reranker` 后端，失败/超时时回退到 fusion 结果并显式标记 fallback。`已完成，2026-02-04`
- `D7` 脚本入口 `query.py`：提供 `--query`、`--top-k`、`--collection`、`--verbose`、`--no-rerank` 等开发调试能力。`已完成，2026-02-04`

**阶段交付物**：混合检索核心引擎、Reranker 编排、命令行查询入口。  
**退出标准**：可对已摄取数据返回可解释的 Top-K 结果，且 Dense/Sparse 任一路失败都不会让查询链路整体失效。

#### 阶段 E：MCP Server 层与 Tools

**阶段目标**：将检索能力通过标准 MCP 协议对外暴露，让 Copilot / Claude Desktop 等 Client 可直接调用。

- `E1` MCP Server 入口与 stdio 约束：实现 `src/mcp_server/server.py`，保证 stdout 只输出 MCP 消息、日志走 stderr。`已完成，2026-02-04`
- `E2` Protocol Handler：实现 `initialize`、`tools/list`、`tools/call` 三类核心协议方法与标准 JSON-RPC 错误处理。`已完成，2026-02-04`
- `E3` `query_knowledge_hub` Tool：编排 `HybridSearch + Reranker`，通过 `ResponseBuilder` 和 `CitationGenerator` 生成 Markdown + structured citations。`已完成，2026-02-04`
- `E4` `list_collections` Tool：返回集合列表及统计信息，为知识库管理提供基础工具。`已完成，2026-02-04`
- `E5` `get_document_summary` Tool：按 `doc_id` 返回 `title/summary/tags` 等结构化摘要信息。`已完成，2026-02-04`
- `E6` 多模态返回组装：在命中 chunk 含图像引用时，读取图片并组装为 MCP `ImageContent` 返回。`已完成，2026-02-04`

**阶段交付物**：MCP Server、协议层、3 个 MCP Tools、多模态响应构建能力。  
**退出标准**：通过 MCP Client 可直接完成初始化、列工具、调用查询，并获得带引用的稳定响应。

#### 阶段 F：Trace 基础设施与打点

**阶段目标**：让 Ingestion 与 Query 两条主链路都具备白盒化追踪、结构化日志与阶段级可观测能力。

- `F1` TraceContext 增强：为 `TraceContext` 增加 `trace_type`、`finish()`、耗时统计、`to_dict()` 与 `TraceCollector`。`已完成，2026-02-08`
- `F2` 结构化日志：增强 `src/observability/logger.py`，以 JSON Lines 形式将 trace 持久化到 `logs/traces.jsonl`。`已完成，2026-02-08`
- `F3` Query 链路打点：在 `HybridSearch` 与 `Reranker` 中记录 `query_processing`、`dense_retrieval`、`sparse_retrieval`、`fusion`、`rerank` 等阶段。`已完成，2026-02-08`
- `F4` Ingestion 链路打点：在 `IngestionPipeline` 中记录 `load`、`split`、`transform`、`embed`、`upsert` 等阶段。`已完成，2026-02-08`
- `F5` Pipeline 进度回调：在 `IngestionPipeline.run()` 中新增可选 `on_progress`，供 CLI 或 Dashboard 实时展示处理进度。`已完成，2026-02-08`

**阶段交付物**：统一 Trace 数据结构、结构化日志、双链路打点、进度通知接口。  
**退出标准**：任一次摄取或查询都能留下可回放、可分析、可视化的 trace 记录。

#### 阶段 G：可视化管理平台 Dashboard

**阶段目标**：提供“系统总览、数据浏览、摄取管理、链路追踪、评估运行”一体化可视化管理入口。

- `G1` Dashboard 基础架构与系统总览页：搭建 Streamlit 多页面框架，实现配置与数据统计总览。`已完成，2026-02-09`
- `G2` DocumentManager：协调 Chroma、BM25、ImageStorage、IntegrityChecker 等多存储的文档生命周期管理。`已完成，2026-02-09`
- `G3` 数据浏览器页面：支持集合筛选、文档列表、chunk 详情、元数据展开与图片预览。`已完成，2026-02-09`
- `G4` Ingestion 管理页面：支持文件上传、触发摄取、实时进度展示与文档删除。`已完成，2026-02-09`
- `G5` Ingestion 追踪页面：基于 `traces.jsonl` 展示摄取历史、阶段时间线与耗时分布。`已完成，2026-02-09`
- `G6` Query 追踪页面：展示查询历史、Dense/Sparse 对比、Rerank 前后变化与耗时分析。`已完成，2026-02-09`

**阶段交付物**：Streamlit 六页面应用、文档生命周期管理、Trace 可视化。  
**退出标准**：用户可在浏览器中完成数据浏览、摄取管理与链路追踪，不依赖命令行即可理解系统状态。

#### 阶段 H：评估体系

**阶段目标**：建立“可度量、可回归、可比较”的检索评估能力，避免凭主观感觉调整系统。

- `H1` RagasEvaluator：封装 `ragas`，输出 `faithfulness`、`answer_relevancy`、`context_precision` 等指标。`已完成，2026-02-09`
- `H2` CompositeEvaluator：原方案用于并行组合多个 evaluator；后续为保持评估层简洁，决定不单独保留该实现，统一收敛到 `custom + ragas` 双后端工厂模式。`已取消，不再实施`
- `H3` EvalRunner + Golden Test Set：读取 `tests/fixtures/golden_test_set.json` 运行批量评估并输出 `EvalReport`。`已完成，2026-02-09`
- `H4` 评估面板页面：在 Dashboard 中运行评估、查看指标与历史趋势。`已完成，2026-02-09`
- `H5` Recall 回归测试：以 hit@k、MRR 等阈值建立 E2E 回归基线。`已完成，2026-02-09`

**阶段交付物**：Ragas 评估接入、golden set、自动评估脚本、Dashboard 评估面板、Recall 门禁测试。  
**退出标准**：系统可通过固定测试集持续评估检索质量，后续优化具备量化比较基线。

#### 阶段 I：端到端验收与文档收口

**阶段目标**：把项目从“功能可用”推进到“开箱可运行、可演示、可复现、可教学”。

- `I1` MCP Client 侧 E2E：通过子进程启动 Server，模拟 `tools/list` 与 `tools/call`，验证 `query_knowledge_hub` 全链路。`已完成，2026-02-23`
- `I2` Dashboard 冒烟测试：基于 Streamlit `AppTest` 对 6 个页面做自动化冒烟验证。`已完成，2026-02-24`
- `I3` README 收口：补齐快速开始、配置说明、MCP 配置示例、Dashboard 使用、测试命令与 FAQ。`已完成，2026-02-24`
- `I4` 契约测试补齐：为 `VectorStore`、`Reranker`、`Evaluator`、`DocumentManager` 等关键抽象补齐边界测试。`已完成，2026-02-24`
- `I5` 全链路 E2E 验收：完成 `ingest -> query -> MCP -> Dashboard -> evaluate` 全流程人工与自动化验收。`已完成，2026-02-24`

**阶段交付物**：MCP E2E、Dashboard 冒烟、完整 README、契约测试、全链路验收记录。  
**退出标准**：新用户可在短时间内跑通全链路，项目可用于教学、面试讲解与演示复现。

#### 阶段 J：Query Orchestration 增强

**阶段目标**：在不破坏现有主链路与 MCP Tool 入口的前提下，新增服务端检索编排能力，并完整接入 Trace 与 Dashboard。

- `J1` 扩展 `Settings` / `Types` 契约：增加 `retrieval.query_orchestration` 配置块、`QueryPlan` / `SubQueryPlan` 等数据类型，为编排能力提供稳定配置边界。`已完成`
- `J2` Query Expansion Planner：实现独立 Planner，决定当前查询走 `direct`、`synonym` 还是 `decomposition`，并在非法输出或超时时自动回退。`已完成`
- `J3` Synonym Expansion：将扩展词注入稀疏检索路径，同时保持 Dense 路由仍为单次检索，控制成本与复杂度。`已完成`
- `J4` Logical Decomposition：支持复杂 query 拆解为多个子查询，并并行复用既有 `HybridSearch.search()`。`已完成`
- `J5` Multi-Query Merge + 全局 Rerank：对子查询结果做去重、RRF 融合和基于原始 query 的全局精排。`已完成`
- `J6` MCP Tool 集成：在不新增 Tool 的前提下，将编排能力接入 `query_knowledge_hub`，并对返回 metadata 增强 `orchestration_mode`、`sub_query_count`、`used_fallback` 等字段。`已完成`
- `J7` Query Trace 与 Dashboard 适配：为 Query Orchestration 新增 trace stage，并在 Overview / Query Traces 页面展示 Planner 决策、子查询状态与回退原因。`已完成`
- `J8` 测试矩阵与回归基线：补齐单元、集成与 E2E 测试，覆盖 `off / synonym / decomposition` 三条路径及所有关键降级场景。`已完成`

**推荐实现顺序**：`J1 -> J2 -> J3 -> (J4 + J5) -> J6 -> (J7 + J8)`。  
**退出标准**：MCP 入口与主链路兼容不变，但服务端具备可配置的查询编排能力、完整 Trace 与可视化支持。

### 6.6 统一验收与测试策略

- **单元测试**：用于锁定抽象接口、数据类型、纯逻辑模块和降级策略，要求不依赖真实外部服务，主要覆盖 `tests/unit/`。
- **集成测试**：用于验证模块间编排与真实存储/真实 provider 的交互边界，主要覆盖 `tests/integration/`。
- **E2E 测试**：用于验证用户真实使用路径，包括 `ingest.py`、`query.py`、MCP Client 调用、Dashboard 页面加载与 Recall 门禁，主要覆盖 `tests/e2e/`。
- **CLI 验证**：在自动化测试之外，保留 `python scripts/ingest.py`、`python scripts/query.py`、`python scripts/evaluate.py`、`python scripts/start_dashboard.py` 作为人工验收入口。
- **回归原则**：新能力默认不能破坏旧路径，任何增强项都必须有“关闭后行为与历史版本等价”的验证。

### 6.7 关键风险与控制策略

- **风险 1：接口抽象与默认实现脱节**。控制策略：先写 contract tests，再补 provider 实现，确保 `Factory + Base 接口 + 默认后端` 始终同步演进。
- **风险 2：摄取链路多模态信息丢失**。控制策略：在 `Document`、`Chunk`、`ImageStorage` 三层显式定义图片契约，禁止简单整体继承或直接丢弃 `images` 元数据。
- **风险 3：Hybrid Search 任一路径失败导致查询不可用**。控制策略：Dense、Sparse、Rerank 均设计独立回退路径，并在 Trace 中显式记录 fallback。
- **风险 4：真实 LLM/Vision/Embedding 调用成本和不稳定性过高**。控制策略：单元测试统一 Mock，真实 provider 只在集成测试或手工验收时启用，并保留本地 `ollama` 路径作为替代方案。
- **风险 5：Trace 结构演进破坏 Dashboard 页面**。控制策略：Dashboard 读取 trace 时采用“字段可选 + 缺省兼容”，阶段扩展优先新增而非破坏已有字段语义。
- **风险 6：Query Orchestration 带来分支抖动与成本膨胀**。控制策略：Planner 强制结构化输出、限制 `max_sub_queries`、保留 `fallback_to_direct`、对子查询候选数做上限控制，并在 Merge 后统一做全局 rerank。
- **风险 7：文档与实现逐渐偏离**。控制策略：将本节作为唯一开发规划基线，新增阶段或任务时优先更新本节，不再维护多个重复版本的排期内容。

### 6.8 交付里程碑

- `M1` 完成阶段 `A + B`：工程骨架与可插拔抽象层就绪，具备继续纵向开发的稳定基础。
- `M2` 完成阶段 `C`：离线摄取链路可用，可对样例文档建立向量索引、BM25 索引和图像索引。
- `M3` 完成阶段 `D + E`：在线检索能力与 MCP Tool 可用，可被 Copilot / Claude Desktop 直接调用。
- `M4` 完成阶段 `F`：Ingestion 与 Query 双链路具备 Trace 与结构化日志，系统可白盒分析。
- `M5` 完成阶段 `G`：Dashboard 六页面可用，系统配置、数据状态与链路追踪可视化完成。
- `M6` 完成阶段 `H + I`：评估体系、E2E 验收与文档收口完成，形成“面试 / 教学 / 演示”可复现项目。
- `M7` 完成阶段 `J`：服务端 Query Orchestration 增强接入 MCP、Trace 与 Dashboard，系统具备更强的复杂查询处理能力。

## 7. 可扩展性与未来展望

### 7.1 云端部署与后端架构学习
虽然当前阶段我们主要采用“本地运行”模式，但本项目的架构设计完全支持向云端迁移。这也是一个极佳的学习后端工程化的切入点。
- **Server 容器化**：计划编写 Dockerfile，将 MCP Server 打包为容器。这让我们有机会深入理解 Python 环境隔离、依赖管理以及 Docker 的最佳实践。
- **云端接入**：未来可以将 Server 部署至 Azure Container Apps 或 AWS Lambda。
    - **挑战与学习点**：处理网络延时、配置 API Gateway、增加 AuthN/AuthZ 鉴权机制（保护私有数据不被公开访问）。
- **多租户与并发**：从单用户本地服务转变为支持团队共享的服务。
    - **学习点**：在 Chroma 中实现 Namespace 隔离、处理并发请求锁、优化 embedding 缓存策略。

### 7.2 业务深耕：从"通用"到"垂直" (Vertical Domain Adaptation)
RAG 系统的上限取决于其对特定业务数据的理解深度。未来的核心扩展方向是将通用的技术框架与具体的业务场景深度结合。在将本项目应用到实际生产环境时，识别并解决以下“最后一公里”的难题，将是提升系统价值的关键：

- **多源异构数据的复杂适配**：
    - 现实业务中不仅有 PDF，还大量存在 PPTX, DOCX, XLSX 甚至 HTML 数据。
    - **挑战**：如何处理不同格式的特有语义？例如 PPT 中的演讲者备注往往比正文更关键，Excel 中的公式逻辑与跨行关联如何保留？目前的通用处理方式容易丢失这些“隐性知识”，未来需要针对每种格式探索更深度的解析能力。

- **复杂结构化数据的精确理解**：
    - 简单的文本切分（Chunking）在处理表格、层级列表时往往会破坏语义。
    - **挑战**：
        - **表格理解**：如何处理跨页长表格、合并单元格以及含有复杂表头的财务报表？如果切分不当，检索时只能找到数字却不知道对应的列名（指标含义）。
        - **上下文断裂**：当一个完整的逻辑段落（如合同条款）被切分到两个 chunk 时，如何保证检索其中一段时能感知到整体的上下文约束？

- **业务逻辑驱动的生成控制**：
    - 仅仅根据“相似度”召回文档在企业级场景中往往不够。
    - **挑战**：
        - **时效性与版本管理**：当知识库中同时存在“2023版”和“2024版”规章时，如何确保系统不会混淆历史数据与最新标准？
        - **权限与受众适配**：面对内部员工与外部客户，如何控制生成答案的详略程度与敏感信息披露？
        - **拒答机制**：当召回内容的置信度不足时，如何让系统诚实地回答“不知道”而不是基于相关性较低的片段强行拼凑答案（幻觉问题）？

### 7.3 迈向自主智能：Agentic RAG 的演进路径
当前的 RAG 架构主要遵循“一次检索-一次生成”的固有范式，但在面对极其复杂的问题（如跨文档对比、多步推理）时，单一的线性流程往往力不从心。本项目作为标准的 MCP Server，天然具备向 **Agentic RAG（代理式 RAG）** 演进的潜力。这不需要重写现有代码，而是通过在 Server 端提供更细粒度的工具，赋能 Client 端的 Agent 具备更强的自主性：

- **从“单步检索”到“多步决策”**：
    - 目前 Agent 可能只调用一个通用的 `search` 工具。
    - **未来演进**：Server 可以暴露如 `list_directory`（查看目录结构）、`preview_document`（预览摘要）、`verify_fact`（事实核查）等更原子化的工具。Agent 可以像人类研究员一样，先看目录圈定范围，再针对性阅读，最后交叉验证信息，从而解决复杂问题。
- **让 Agent 具备“反思”能力**：
    - **未来演进**：利用现有的评估模块，Server 可以提供一个 `self_check` 接口。Agent 在生成答案后，可以自主调用该接口检测是否存在幻觉，或者检索结果是否真正支撑了论点。如果发现不足，Agent 可以自主决定进行第二轮更深度的搜索。
- **动态策略选择**：
    - **未来演进**：不再硬编码使用混合检索。Server 可以将 `keyword_search` 和 `semantic_search` 作为独立工具暴露。Agent 可以根据用户意图自主判断：如果是搜人名，只用关键词搜；如果是搜概念，通过语义搜。这种工具使用的灵活性正是 Agentic RAG 的核心魅力。

这种演进方向将把本项目从一个“智能搜索引擎”升级为一个“智能研究助理”的基础设施底座。


---

## 8. 项目中所有 LLM 调用点总览

本项目有 **6 个独立 LLM 调用点**，分布在 Ingestion、Query、Evaluation 三大链路上。每个调用点均通过统一的 `LLMFactory`（或等效的 OpenAI 兼容客户端）创建，底层的 API Key 获取逻辑按各 Provider 实现各有差异。

### 8.1 调用点分布

| # | 调用点 | 模块 | 配置段 | 工厂/创建方式 | 调用方法 | 链路 |
|---|--------|------|--------|-------------|---------|------|
| 1 | **Query Orchestrator Planner** | `query_orchestrator.py` | `settings.llm` | `LLMFactory.create(settings)` | `.chat()` | Query |
| 2 | **LLM Reranker** | `llm_reranker.py` | `settings.llm` | `LLMFactory.create(settings)` | `.chat()` | Query |
| 3 | **Chunk Refiner** | `chunk_refiner.py` | `settings.llm` | `LLMFactory.create(settings)` | `.chat()` | Ingestion |
| 4 | **Metadata Enricher** | `metadata_enricher.py` | `settings.llm` | `LLMFactory.create(settings)` | `.chat()` | Ingestion |
| 5 | **Vision LLM / Image Captioner** | `image_captioner.py` | `settings.vision_llm` | `LLMFactory.create_vision_llm(settings)` | `.chat_with_image()` | Ingestion |
| 6 | **Ragas Evaluator** | `ragas_evaluator.py` | `settings.llm` + `settings.embedding` | 直接创建 `AsyncOpenAI` / `AsyncAzureOpenAI` 客户端 | Ragas `InstructorLLM` + `OpenAIEmbeddings` | Evaluation |

### 8.2 各 Provider API Key 获取优先级

项目支持 4 种 LLM Provider，各自 API Key 的读取优先级如下：

| Provider | 优先级 1（最高） | 优先级 2 | 优先级 3（最低） |
|----------|-----------------|---------|-----------------|
| **OpenAI** | 显式参数 `api_key=` | `settings.llm.api_key` | 环境变量 `OPENAI_API_KEY` |
| **Azure** | 显式参数 `api_key=` | `settings.llm.api_key` | 环境变量 `AZURE_OPENAI_API_KEY` |
| **DeepSeek** | 显式参数 `api_key=` | `settings.llm.api_key` | 环境变量 `DEEPSEEK_API_KEY` |
| **Ollama** | 无需 API Key（本地） | — | `OLLAMA_BASE_URL` 环境变量 |

> **注意**：`DeepSeekLLM` 最初**缺失优先级 2**，不读取 `settings.llm.api_key`，导致使用 DeepSeek 时 Reranker 和 Planner 均创建失败并静默降级。此问题已在阶段 J 后期修复。

### 8.3 Ragas Evaluator 的特殊处理

Ragas Evaluator 不使用 `LLMFactory`，而是直接创建 OpenAI 兼容客户端：

- **LLM**：`AsyncOpenAI`（默认 `api.openai.com`）或 `AsyncAzureOpenAI`（Azure 路径）
- **Embedding**：同上
- **支持 Provider**：
  - `azure` 及 `openai` + `azure_endpoint` → `AsyncAzureOpenAI`
  - `openai` → `AsyncOpenAI`（默认 base_url）
  - `deepseek` → `AsyncOpenAI(base_url="https://api.deepseek.com/v1")`
  - `ollama` → `AsyncOpenAI(base_url="http://localhost:11434/v1")`
  - `openai` + 自定义 `base_url`（如 DashScope）→ `AsyncOpenAI(base_url=...)`

### 8.4 关键设计原则

1. **统一工厂入口**：`LLMFactory.create(settings)` 是所有文本 LLM 的唯一创建入口，Provider 选择完全由 `settings.llm.provider` 配置驱动。
2. **懒加载**：所有 LLM 实例均延迟创建（首次调用时才初始化），避免启动时不必要的 API 连接。
3. **静默降级 + 回退**：
   - `CoreReranker`：创建失败 → `NoneReranker`（不重排，返回原始排序）
   - `QueryOrchestrator`：LLM 调用失败 → `fallback_to_direct`（退回直通检索）
4. **热配置支持**（阶段 J 后）：`query_knowledge_hub` 每次查询都从磁盘重新加载 `settings.yaml`，修改配置无需重启 MCP Server。


---
## 9. 阶段 J 后期修复与优化记录

以下为阶段 J 开发完成后的持续修复与改进，按时间倒序排列。

### 9.1 Overview 组件配置语义化重构

**问题**：Overview 页面 `Component Configuration` 所有卡片统一使用 `provider` / `model` 两个字段展示，对于非模型类组件（Vector Store、Retrieval、Query Orchestration、Ingestion）语义严重失真。

**修复内容**：
- 重构 `ConfigService` 数据契约：`ComponentInfo` 从固定 `provider/model` 改为 `summary: list[ComponentField] + status: str | None + extra: dict`
- 每类组件按语义定义专属摘要字段名：
  | 组件 | 字段 1 | 字段 2 | Status |
  |------|--------|--------|--------|
  | LLM | Provider | Model | — |
  | Embedding | Provider | Model | — |
  | Vector Store | Engine | Default Collection | — |
  | Query Orchestration | Planner | Configured Mode | enabled/disabled |
  | Retrieval | Pipeline | Rank Fusion | — |
  | Reranker | Type | Top K | enabled/disabled |
  | Vision LLM | Provider | Model | enabled/disabled |
  | Ingestion | Splitter | Chunking | — |
- `Overview` 页面渲染层改为循环 `card.summary`，不再硬编码 `Provider:` / `Model:` 标签
- `Query Orchestration` 卡片移至 `Retrieval` 前面（编排在检索之前，逻辑更自然）
- `parallel_sub_queries` 仅在 `mode == decomposition` 时显示配置值，其余 mode 显示 `False`
- `merge_fusion` 增加 `(decomposition)` 后缀标注，表明仅作用在 decomposition 合并阶段
- `Retrieval` 卡片明确主检索融合与 `query_orchestration.merge_fusion` 是独立入口

**涉及文件**：[config_service.py](file:///Users/a/Desktop/OH-WorkSpace/ALL/我的Github项目/MODULAR-RAG-MCP-SERVER/src/observability/dashboard/services/config_service.py)、[overview.py](file:///Users/a/Desktop/OH-WorkSpace/ALL/我的Github项目/MODULAR-RAG-MCP-SERVER/src/observability/dashboard/pages/overview.py)

### 9.2 Dashboard 默认 Collection 统一

**问题**：`Data Browser`、`Ingestion Manager`、`Query Traces`、`Evaluation` 多处硬编码 `"default"` 作为 collection 回退值，与配置 `settings.vector_store.collection_name: "knowledge_hub"` 不一致。

**修复内容**：
- `DataService` 新增 `get_default_collection_name()` 方法，读取 `settings.vector_store.collection_name`
- `Data Browser`：初始选中集合改为配置默认名
- `Ingestion Manager`：输入框默认值与空值回退改为配置默认名
- `Query Traces`：重新检索时的 collection 回退改为配置默认名
- `Evaluation Panel`：`_execute_evaluation()` 和 `_try_create_hybrid_search()` 的 collection 回退改为配置默认名

**涉及文件**：[data_service.py](file:///Users/a/Desktop/OH-WorkSpace/ALL/我的Github项目/MODULAR-RAG-MCP-SERVER/src/observability/dashboard/services/data_service.py)、[data_browser.py](file:///Users/a/Desktop/OH-WorkSpace/ALL/我的Github项目/MODULAR-RAG-MCP-SERVER/src/observability/dashboard/pages/data_browser.py)、[ingestion_manager.py](file:///Users/a/Desktop/OH-WorkSpace/ALL/我的Github项目/MODULAR-RAG-MCP-SERVER/src/observability/dashboard/pages/ingestion_manager.py)、[query_traces.py](file:///Users/a/Desktop/OH-WorkSpace/ALL/我的Github项目/MODULAR-RAG-MCP-SERVER/src/observability/dashboard/pages/query_traces.py)、[evaluation_panel.py](file:///Users/a/Desktop/OH-WorkSpace/ALL/我的Github项目/MODULAR-RAG-MCP-SERVER/src/observability/dashboard/pages/evaluation_panel.py)

### 9.3 CustomEvaluator 空知识库容错 + ID 提取修复

**问题**：
1.  `_extract_ids()` 在 `RetrievalResult` 对象上只检查 `hasattr(item, "id")`，但 `RetrievalResult` 的字段是 `chunk_id`，导致每次提取 ID 都抛 `ValueError`，metrics 永远为空 `{}`
2. 空知识库检索返回空列表时，`validate_retrieved_chunks([])` 抛异常导致 metrics 为空

**修复内容**：
- 新增 `_ID_ATTRS = ("id", "chunk_id", "document_id", "doc_id")`，逐个检查对象属性
- 空 chunks 直接返回 `{metric: 0.0}`，不再抛异常
- 对应的 Ragas 侧同步修复

**涉及文件**：[custom_evaluator.py](file:///Users/a/Desktop/OH-WorkSpace/ALL/我的Github项目/MODULAR-RAG-MCP-SERVER/src/libs/evaluator/custom_evaluator.py)、[ragas_evaluator.py](file:///Users/a/Desktop/OH-WorkSpace/ALL/我的Github项目/MODULAR-RAG-MCP-SERVER/src/libs/evaluator/ragas_evaluator.py)

### 9.4 Evaluation History 拆分

**问题**：Custom 和 Ragas 评测的指标维度完全不同（`hit_rate/mrr` vs `faithfulness/answer_relevancy/context_precision`），原来混在同一张 table 里用动态展开 `**aggregate_metrics` 的方式，导致大量交叉空列，用户难以阅读。

**修复内容**：
- `_render_history()` 不再用 `**` 动态展开所有 metrics key
- 改为按 `evaluator_name` 筛选出 `CustomEvaluator` 和 `RagasEvaluator` 两组，各自渲染独立的 `st.dataframe`
- `📊 Custom Evaluator History`：固定列 `Timestamp / Test Set / Queries / Time (ms) / hit_rate / mrr`
- `🤖 Ragas Evaluator History`：固定列 `Timestamp / Test Set / Queries / Time (ms) / faithfulness / answer_relevancy / context_precision`

**涉及文件**：[evaluation_panel.py](file:///Users/a/Desktop/OH-WorkSpace/ALL/我的Github项目/MODULAR-RAG-MCP-SERVER/src/observability/dashboard/pages/evaluation_panel.py#L415-L469)

### 9.5 Ragas Evaluator OpenAI-Compatible Provider 路由

**问题**：Ragas 评估报错 `Unsupported LLM provider for Ragas: 'deepseek'. Supported: azure, openai`

**修复内容**：
- 新增 `_DEFAULT_OPENAI_COMPAT_BASE` 映射（deepseek → `api.deepseek.com/v1`，ollama → `localhost:11434/v1`）
- 新增 `_resolve_base_url()`、`_build_llm_client()` 等 helper 方法
- 新增 `_make_ragas_llm()` / `_make_ragas_embeddings()` 统一客户端路由

**涉及文件**：[ragas_evaluator.py](file:///Users/a/Desktop/OH-WorkSpace/ALL/我的Github项目/MODULAR-RAG-MCP-SERVER/src/libs/evaluator/ragas_evaluator.py)

### 9.6 热配置：Settings / Reranker / Orchestrator 缓存修复

**问题**：MCP Tool 对象长期持有缓存，修改 YAML 后不重启不生效。

**修复内容**：
- `QueryKnowledgeHubTool.settings` 改为每次访问都重新 `load_settings()`
- Reranker 创建逻辑：若当前 reranker 已降级为 `NoneReranker` 但配置已改为启用，则重新创建
- `QueryOrchestrator`：不缓存，每次查询重新创建

**涉及文件**：[query_knowledge_hub.py](file:///Users/a/Desktop/OH-WorkSpace/ALL/我的Github项目/MODULAR-RAG-MCP-SERVER/src/mcp_server/tools/query_knowledge_hub.py)

### 9.7 DeepSeek LLM API Key 优先级修复

**问题**：`DeepSeekLLM` 不读取 `settings.llm.api_key`，导致 DeepSeek 用户 Reranker 和 Planner 均创建失败并静默降级。

**修复内容**：API Key 获取优先级修正为：显式参数 → `settings.llm.api_key` → `DEEPSEEK_API_KEY`

**涉及文件**：[deepseek_llm.py](file:///Users/a/Desktop/OH-WorkSpace/ALL/我的Github项目/MODULAR-RAG-MCP-SERVER/src/libs/llm/deepseek_llm.py)
