# Quickstart Guide: Werewolf Game Backend

**Created**: 2025-12-01
**Feature**: 002-werewolf-backend
**Purpose**: Quick start guide for implementing the werewolf game backend with AgentScope

## Overview

这是一个基于AgentScope框架的狼人杀游戏后端系统，支持9个AI玩家进行完整的狼人杀游戏。

### Game Configuration
- **Players**: 9 AI players
- **Roles**: 3 Werewolves, 3 Villagers, 1 Seer, 1 Witch, 1 Hunter
- **Language**: Chinese (with support for English)
- **All Players**: AI-controlled (no human players)

## Core Architecture

### 1. AgentScope Integration
```typescript
// AI Player Configuration
interface AIPlayerConfig {
  agentType: string;             // AgentScope agent type
  personality: PersonalityType;    // AI性格类型
  skillLevel: SkillLevel;          // 技能等级
  responseTime: ResponseTime;     // 响应时间
  strategy: StrategyType;         // 策略类型
  language: 'zh' | 'en';         // 语言偏好
}

// Example AI Player Setup
const werewolfAI: AIPlayerConfig = {
  agentType: 'werewolf_agent',
  personality: PersonalityType.AGGRESSIVE,
  skillLevel: SkillLevel.ADVANCED,
  responseTime: ResponseTime.NORMAL,
  strategy: StrategyType.LOGICAL,
  language: 'zh',
  creativityLevel: 0.7,
  aggressiveness: 0.8,
  cooperation: 0.3
};
```

### 2. Game Flow Management
```typescript
// Game Session Initialization
async function initializeGameSession(roomId: string): Promise<GameSession> {
  const players = await generateAIPlayers(9);
  const roles = assignRoles(players);
  const session = createGameSession(roomId, players, roles);

  // 初始化AgentScope代理
  await initializeAgentScopeAgents(session.players);

  return session;
}

// Night Phase Processing
async function processNightPhase(session: GameSession): Promise<NightActions> {
  const werewolfActions = await processWerewolfActions(session);
  const seerAction = await processSeerAction(session);
  const witchAction = await processWitchAction(session);

  return resolveNightActions(werewolfActions, seerAction, witchAction);
}
```

### 3. Real-time Communication
```typescript
// WebSocket Event Broadcasting
class GameEventBroadcaster {
  async broadcastGameEvent(event: GameEvent): Promise<void> {
    const visibility = calculateEventVisibility(event);
    const recipients = await determineEventRecipients(event, visibility);

    for (const recipient of recipients) {
      await this.sendToPlayer(recipient, event);
    }
  }

  async broadcastPhaseChange(phase: GamePhase, gameState: GameState): Promise<void> {
    const event = createPhaseChangeEvent(phase, gameState);
    await this.broadcastGameEvent(event);
  }
}
```

## Implementation Steps

### Phase 1: Core Game Logic
1. **数据模型实现**
   - 实现所有entity interfaces
   - 设置数据库schema
   - 创建validation rules

2. **AgentScope集成**
   - 配置AI代理类型
   - 实现消息传递机制
   - 设置agent通信协议

3. **游戏流程引擎**
   - 实现阶段转换逻辑
   - 添加游戏规则验证
   - 实现胜利条件检测

### Phase 2: AI Player Implementation
1. **角色特定的AI代理**
   - 预言家：基于信息推理的查验策略
   - 女巫：基于局势判断的用药策略
   - 猎人：死亡目标的快速决策策略
   - 狼人：协调击杀和伪装策略
   - 平民：逻辑推理和投票策略

2. **决策引擎**
   - 实现AI决策树
   - 添加记忆和学习机制
   - 设置响应时间控制

### Phase 3: WebSocket API
1. **实时通信**
   - 实现WebSocket服务器
   - 添加事件广播机制
   - 实现可见性控制

2. **前端集成接口**
   - 游戏状态同步
   - 事件通知系统
   - 回放功能API

### Phase 4: Advanced Features
1. **游戏回放系统**
   - 每日状态快照
   - 事件序列回放
   - 多维度分析工具

2. **性能优化**
   - AI决策缓存
   - 连接池管理
   - 负载均衡

## Technology Stack

### Core Framework
- **AgentScope**: AI代理管理和决策引擎
- **Node.js + TypeScript**: 后端服务
- **Socket.IO**: 实时WebSocket通信
- **Redis**: 缓存和会话管理

### Data Storage
- **PostgreSQL**: 主数据库（游戏历史、用户数据）
- **Redis**: 实时游戏状态缓存
- **MongoDB**: 游戏事件日志（可选）

### AI/ML
- **AgentScope**: 多智能体协调框架
- **OpenAI API**: 高级AI玩家（可选）
- **Claude API**: 复杂决策支持（可选）

## Key Configuration

### Game Rules
```typescript
const GAME_CONFIG = {
  maxPlayers: 9,
  roleDistribution: {
    werewolf: 3,
    villager: 3,
    seer: 1,
    witch: 1,
    hunter: 1
  },
  phaseDurations: {
    night: 30,        // 秒
    dayDiscussion: 180, // 秒
    voting: 60,        // 秒
    sheriffElection: 120 // 秒
  }
};
```

### AI Player Templates
```typescript
// 预言家AI配置
const SEER_AI_TEMPLATE: AIPlayerConfig = {
  agentType: 'seer_agent',
  personality: PersonalityType.ANALYTICAL,
  skillLevel: SkillLevel.EXPERT,
  responseTime: ResponseTime.NORMAL,
  strategy: StrategyType.LOGICAL,
  language: 'zh',
  creativityLevel: 0.4,
  aggressiveness: 0.3,
  cooperation: 0.8
};

// 狼人AI配置
const WEREWOLF_AI_TEMPLATE: AIPlayerConfig = {
  agentType: 'werewolf_agent',
  personality: PersonalityType.DECEPTIVE,
  skillLevel: SkillLevel.ADVANCED,
  responseTime: ResponseTime.FAST,
  strategy: StrategyType.EMOTIONAL,
  language: 'zh',
  creativityLevel: 0.8,
  aggressiveness: 0.9,
  cooperation: 0.9 // 狼人团队合作
};
```

## Development Environment Setup

### Prerequisites
- Node.js 18+
- TypeScript 5.0+
- Redis Server
- PostgreSQL 14+
- AgentScope Framework

### Installation
```bash
# 克隆项目
git clone https://github.com/feizy/ai_werewolf.git
cd ai_werewolf/backend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件配置数据库和API密钥

# 启动数据库
docker-compose up -d

# 运行迁移
npm run migrate

# 启动开发服务器
npm run dev
```

### Environment Variables
```env
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/werewolf
REDIS_URL=redis://localhost:6379

# AgentScope配置
AGENTSCOPE_API_KEY=your_agent_scope_key
AGENTSCOPE_BASE_URL=http://localhost:8080

# WebSocket配置
WS_PORT=3001
WS_CORS_ORIGIN=http://localhost:3000

# AI配置
OPENAI_API_KEY=your_openai_key
CLAUDE_API_KEY=your_claude_key

# 游戏配置
GAME_DURATION_LIMIT=3600  # 游戏最长1小时
MAX_CONCURRENT_GAMES=100
```

## API Testing

### WebSocket连接测试
```javascript
const io = require('socket.io-client');

const socket = io('ws://localhost:3001');

// 创建新游戏房间
socket.emit('create_room', {
  playerName: 'AI-Game-1',
  roomName: 'AI测试房间'
});

// 监听游戏事件
socket.on('game_started', (data) => {
  console.log('游戏开始:', data);
});

socket.on('phase_change', (data) => {
  console.log('阶段变化:', data.phase);
});
```

### REST API测试
```bash
# 获取房间列表
curl http://localhost:3001/api/rooms

# 创建新房间
curl -X POST http://localhost:3001/api/rooms \
  -H "Content-Type: application/json" \
  -d '{"playerName": "AI-Game-1", "roomName": "测试房间"}'

# 获取游戏状态
curl http://localhost:3001/api/games/{gameId}/state
```

## Monitoring and Debugging

### 日志配置
```typescript
import winston from 'winston';

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.File({ filename: 'logs/game.log' }),
    new winston.transports.Console()
  ]
});
```

### 性能监控
- 游戏会话数量监控
- AI决策时间统计
- WebSocket连接数监控
- 数据库查询性能监控
- AgentScope代理状态监控

### Debugging Tools
- AgentScope调试界面
- 游戏状态可视化
- 事件流监控面板
- AI决策过程追踪

## Deployment

### Docker部署
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY dist ./dist
EXPOSE 3001
CMD ["npm", "start"]
```

### Kubernetes部署
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: werewolf-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: werewolf-backend
  template:
    metadata:
      labels:
        app: werewolf-backend
    spec:
      containers:
      - name: backend
        image: werewolf-backend:latest
        ports:
        - containerPort: 3001
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: werewolf-secrets
              key: database-url
```

## Security Considerations

### 输入验证
- 所有玩家输入验证
- AI决策结果验证
- WebSocket消息验证
- API参数验证

### 权限控制
- 基于角色的可见性控制
- 阶段特定的操作权限
- 资源访问限制
- 速率限制

### 数据保护
- 游戏数据加密存储
- 通信加密
- 敏感信息脱敏
- 审计日志记录

## Testing Strategy

### 单元测试
- 游戏逻辑测试
- AI决策算法测试
- 数据模型验证测试
- 工具函数测试

### 集成测试
- AgentScope集成测试
- WebSocket通信测试
- 数据库操作测试
- 端到端游戏流程测试

### 性能测试
- 并发游戏负载测试
- AI决策性能测试
- 内存使用优化测试
- 网络延迟测试

## Troubleshooting

### 常见问题
1. **AgentScope连接失败**
   - 检查API密钥配置
   - 验证AgentScope服务状态
   - 检查网络连接

2. **AI决策超时**
   - 调整responseTime配置
   - 增加超时处理机制
   - 优化决策算法

3. **游戏状态不同步**
   - 检查事件广播逻辑
   - 验证状态转换规则
   - 增加状态校验机制

4. **性能问题**
   - 监控数据库查询
   - 优化AI决策缓存
   - 检查内存泄漏

## Next Steps

1. **完成Phase 1**: 实现核心游戏逻辑和数据模型
2. **集成AgentScope**: 配置AI代理和决策引擎
3. **开发WebSocket API**: 实现实时通信和事件广播
4. **添加高级功能**: 游戏回放、性能监控、部署配置
5. **测试和优化**: 全面测试和性能调优

---

## Documentation Links

- [游戏规则文档](game-rules.md)
- [详细规范文档](spec.md)
- [数据模型文档](data-model.md)
- [WebSocket API文档](contracts/websocket-api.md)
- [AgentScope文档](https://agentscope.readthedocs.io/)

## Support

如有问题或建议，请：
1. 查看本文档的故障排除部分
2. 检查项目GitHub Issues
3. 联系开发团队