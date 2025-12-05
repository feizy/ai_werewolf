# AI Werewolf Game Backend (Python)

基于AgentScope框架的AI狼人杀游戏后端系统，使用Python + FastAPI + Socket.IO实现。

## 功能特性

### 🐺 完整的狼人杀游戏实现
- **3狼3民1预言家1女巫1猎人** 9人局配置
- 完整的游戏流程控制（夜晚→白天→投票→夜晚）
- 角色技能系统（预言家查验、女巫解药毒药、猎人开枪）
- 警长竞选和投票系统
- 游戏胜负判定逻辑

### 🤖 AI代理系统集成
- 基于AgentScope框架的智能AI代理
- 角色特定的AI行为和决策逻辑
- 可配置的AI性格和技能等级
- 支持多种AI模型（OpenAI、Anthropic等）

### 🌐 实时通信
- FastAPI + Socket.IO实时WebSocket通信
- 房间管理和玩家匹配
- 实时游戏事件广播
- 断线重连支持

### 🗄️ 数据持久化
- SQLAlchemy ORM数据库支持
- PostgreSQL/SQLite数据库适配
- Alembic数据库迁移工具
- 完整的CRUD操作

### 📊 游戏回放系统
- 完整的游戏历史记录
- 按日回放功能
- 事件可见性控制
- 游戏统计分析

## 技术架构

```
backend_py/
├── src/werewolf/           # 核心业务代码
│   ├── models/            # 数据模型
│   │   ├── player.py      # 玩家模型
│   │   ├── room.py        # 房间模型
│   │   ├── game.py        # 游戏模型
│   │   └── events.py      # 事件模型
│   ├── services/          # 业务服务
│   │   ├── ai_manager.py  # AI管理器
│   │   ├── game_engine.py # 游戏引擎
│   │   └── event_service.py # 事件服务
│   ├── web/               # Web层
│   │   ├── api.py         # REST API
│   │   └── websocket.py   # WebSocket
│   ├── database/          # 数据库
│   │   ├── models.py      # SQLAlchemy模型
│   │   ├── crud.py        # CRUD操作
│   │   └── manager.py     # 数据库管理
│   └── config.py          # 配置管理
├── tests/                 # 测试代码
├── migrations/            # 数据库迁移
└── requirements.txt       # 依赖包
```

## 快速开始

### 环境要求
- Python 3.9+
- PostgreSQL 12+ (或SQLite用于开发)
- Redis 6+ (可选，用于缓存)
- Node.js 16+ (用于前端，如果需要)

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/feizy/ai_werewolf.git
cd ai_werewolf/backend_py
```

2. **创建虚拟环境**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接和API密钥
```

5. **初始化数据库**
```bash
# 创建数据库迁移
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head
```

6. **启动服务**
```bash
# 开发模式
python -m werewolf

# 或使用uvicorn
uvicorn werewolf.main:app --reload --host 0.0.0.0 --port 8000
```

### API文档
启动服务后，访问以下地址查看API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### WebSocket连接
- WebSocket地址: `ws://localhost:8000/socket.io`

## 配置说明

### 环境变量配置
主要配置项在 `.env` 文件中：

```env
# 服务器配置
HOST=0.0.0.0
PORT=8000
DEBUG=true

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/werewolf_db

# AgentScope配置
AGENTSCOPE_API_KEY=your_agentscope_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# WebSocket配置
WEBSOCKET_CORS_ORIGINS=http://localhost:3000,http://localhost:3001

# 游戏配置
DEFAULT_MAX_PLAYERS=9
MIN_PLAYERS_TO_START=4
```

### AI配置
支持多种AI提供商：
- AgentScope (推荐)
- OpenAI GPT系列
- Anthropic Claude

## API接口

### 房间管理
- `GET /rooms` - 获取所有房间
- `POST /rooms` - 创建房间
- `GET /rooms/{room_id}` - 获取房间信息
- `POST /rooms/{room_id}/join` - 加入房间

### 游戏管理
- `GET /games/{game_id}` - 获取游戏信息
- `POST /games/{game_id}/start` - 开始游戏
- `GET /games/{game_id}/state` - 获取游戏状态

### 回放系统
- `POST /replays` - 访问游戏回放
- `POST /replays/days` - 获取可用回放天数
- `POST /replays/day` - 获取特定日期回放

### 系统状态
- `GET /health` - 健康检查
- `GET /status` - 系统状态
- `GET /metrics` - 系统指标

## WebSocket事件

### 客户端发送事件
- `create_room` - 创建房间
- `join_room` - 加入房间
- `start_game` - 开始游戏
- `leave_room` - 离开房间
- `heartbeat` - 心跳检测
- `reconnect` - 重连

### 服务器广播事件
- `room_created` - 房间创建成功
- `room_joined` - 成功加入房间
- `player_joined` - 玩家加入房间
- `player_left` - 玩家离开房间
- `game_started` - 游戏开始
- `game_phase_change` - 游戏阶段变化
- `player_action` - 玩家行动
- `game_ended` - 游戏结束

## 测试

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_models.py

# 运行测试并生成覆盖率报告
pytest --cov=werewolf --cov-report=html
```

### 测试类型
- `tests/test_models.py` - 数据模型测试
- `tests/test_api.py` - API接口测试
- `tests/test_ai_manager.py` - AI管理器测试
- `tests/test_game_engine.py` - 游戏引擎测试
- `tests/test_database.py` - 数据库测试

## 部署

### Docker部署
```bash
# 构建镜像
docker build -t werewolf-backend .

# 运行容器
docker run -p 8000:8000 --env-file .env werewolf-backend
```

### 生产部署
推荐使用Gunicorn + Nginx：

```bash
# 安装生产依赖
pip install gunicorn

# 启动服务
gunicorn werewolf.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 开发指南

### 代码规范
- 使用Black进行代码格式化
- 使用flake8进行代码检查
- 使用mypy进行类型检查

```bash
# 格式化代码
black src/ tests/

# 代码检查
flake8 src/ tests/

# 类型检查
mypy src/
```

### 添加新功能
1. 在相应的模型文件中定义数据模型
2. 在service层实现业务逻辑
3. 在API层添加接口
4. 编写对应的测试

### 调试模式
```bash
# 启动调试模式
DEBUG=true python -m werewolf
```

## 性能优化

### 数据库优化
- 使用连接池
- 添加适当索引
- 定期清理过期数据

### AI优化
- 使用缓存存储AI响应
- 并行处理AI请求
- 配置合理的超时时间

## 故障排除

### 常见问题
1. **数据库连接失败**
   - 检查数据库服务是否启动
   - 验证连接字符串配置

2. **AI服务不可用**
   - 检查API密钥配置
   - 验证网络连接

3. **WebSocket连接问题**
   - 检查CORS配置
   - 验证防火墙设置

### 日志查看
```bash
# 查看应用日志
tail -f logs/werewolf_backend.log
```

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交代码
4. 创建Pull Request

## 许可证
MIT License

## 联系方式
- 项目地址: https://github.com/feizy/ai_werewolf
- 问题反馈: https://github.com/feizy/ai_werewolf/issues

## 更新日志

### v1.0.0 (2025-12-04)
- 完整的Python后端实现
- AgentScope AI框架集成
- WebSocket实时通信
- 数据库持久化支持
- 完整的测试覆盖