# 狼人杀 AI 对战前端

一个美观的狼人杀游戏展示界面，用于观看 AI 玩家对战。

## 功能特性

### 房间管理
- 🏠 **创建房间**：设置房间名称、最大玩家数、默认LLM配置
- 👥 **玩家管理**：9个座位可视化，支持添加AI玩家
- ⚙️ **LLM配置**：为每个玩家配置不同的AI服务商和模型

### 游戏展示
- 🎮 **玩家圆桌展示**：9名玩家围坐成圆形，展示位置、角色、存活状态
- 📜 **实时事件日志**：记录所有游戏事件（主持人发言、玩家发言、投票等）
- 🎖️ **游戏状态展示**：当前阶段、天数、存活统计
- ⚡ **实时更新**：轮询后端获取最新游戏状态
- 🎨 **精美 UI**：深色主题，动画效果

## 快速开始

### 1. 启动后端服务

```bash
cd backend_py
python -m uvicorn src.werewolf.main:create_app --host 0.0.0.0 --port 8001
```

### 2. 安装前端依赖

```bash
cd frontend
npm install
```

### 3. 启动前端开发服务器

```bash
npm run dev
```

访问 http://localhost:3000

### 4. 创建或连接游戏

**创建新游戏：**
1. 点击"创建房间"选项卡
2. 输入房间名称（例如："AI对战房间"）
3. 选择最大玩家数（默认9人）
4. 输入默认API Key（用于房间创建）
5. 点击"创建房间"

**配置玩家：**
1. 在房间设置界面，点击空座位上的"+"按钮
2. 输入玩家名称
3. 选择AI服务商（Anthropic/OpenAI/DashScope）
4. 选择模型名称
5. 输入API Key
6. 可选：调整温度、流式输出等高级设置
7. 点击"添加玩家"

**开始游戏：**
1. 添加至少4个玩家后，"开始游戏"按钮变为可用
2. 点击"开始游戏"启动对战
3. 观战界面将实时显示游戏进程

**连接现有游戏：**
1. 点击"连接房间"选项卡
2. 输入房间ID
3. 点击"连接游戏"

## 后端连接配置

前端默认连接 `http://localhost:8001`，可在以下文件修改：

- `vite.config.ts` - 开发代理配置
- `src/services/api.ts` - API 基础地址
- `src/hooks/useWebSocket.ts` - WebSocket 地址
- `src/hooks/usePolling.ts` - 轮询 API 地址

### 构建生产版本

```bash
npm run build
```

## 项目结构

```
frontend/
├── src/
│   ├── components/       # React 组件
│   │   ├── PlayerCard.tsx     # 玩家卡片
│   │   ├── PlayerCircle.tsx   # 玩家圆桌
│   │   ├── EventLog.tsx       # 事件日志
│   │   ├── PhaseBanner.tsx    # 阶段横幅
│   │   └── GameStats.tsx      # 游戏统计
│   ├── hooks/            # React Hooks
│   │   └── useWebSocket.ts    # WebSocket 连接
│   ├── store/            # 状态管理
│   │   └── gameStore.ts       # Zustand store
│   ├── types/            # TypeScript 类型
│   │   └── game.ts            # 游戏相关类型
│   ├── App.tsx           # 主应用组件
│   ├── main.tsx          # 入口文件
│   └── index.css         # 全局样式
├── public/               # 静态资源
├── package.json
├── vite.config.ts        # Vite 配置
└── tsconfig.json         # TypeScript 配置
```

## 技术栈

- **React 18** - UI 框架
- **TypeScript** - 类型安全
- **Vite** - 构建工具
- **Zustand** - 状态管理
- **Framer Motion** - 动画效果

## 与后端集成

前端通过 WebSocket 连接后端获取游戏状态更新：

```typescript
// WebSocket 消息类型
type MessageType = 
  | 'GAME_STATE'      // 完整游戏状态
  | 'GAME_EVENT'      // 单个事件
  | 'PLAYER_UPDATE'   // 玩家状态更新
  | 'PHASE_CHANGE';   // 阶段变化
```

## 角色说明

| 角色 | 图标 | 阵营 | 说明 |
|------|------|------|------|
| 狼人 | 🐺 | 狼人 | 每晚可以击杀一人 |
| 平民 | 👤 | 好人 | 无特殊技能 |
| 预言家 | 🔮 | 好人 | 每晚可查验一人身份 |
| 女巫 | 🧪 | 好人 | 有解药和毒药各一瓶 |
| 猎人 | 🎯 | 好人 | 死亡时可开枪带走一人 |

## 游戏阶段

- 🌙 **夜晚**：狼人击杀、预言家查验、女巫用药
- 🎖️ **警长竞选**：仅第一天，选举警长
- ☀️ **白天讨论**：玩家轮流发言
- 🗳️ **投票放逐**：投票选出放逐者
- 🏆 **游戏结束**：一方获胜

