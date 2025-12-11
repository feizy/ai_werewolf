// API 服务 - 连接后端 localhost:8001

export const API_BASE = ''; // 使用 Vite 代理，不需要前缀

export interface RoomInfo {
  id: string;
  name: string;
  current_players: number;
  max_players: number;
  is_full: boolean;
  can_start_game: boolean;
  status: string;
  players: Array<{
    id: string;
    name: string;
    position: number;
    is_ai: boolean;
    role?: string;
  }>;
}

export interface GameInfo {
  game_id: string;
  room_id: string;
  status: string;
  message: string;
}

// 健康检查
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/health`);
    return response.ok;
  } catch {
    return false;
  }
}

// 获取房间信息
export async function getRoom(roomId: string): Promise<RoomInfo> {
  const response = await fetch(`${API_BASE}/rooms/${roomId}`);
  if (!response.ok) {
    throw new Error(`Failed to get room: ${response.statusText}`);
  }
  return response.json();
}

// 获取房间列表
export async function listRooms(): Promise<RoomInfo[]> {
  const response = await fetch(`${API_BASE}/rooms`);
  if (!response.ok) {
    throw new Error(`Failed to list rooms: ${response.statusText}`);
  }
  return response.json();
}

// 创建房间
export async function createRoom(name: string, maxPlayers: number, llmConfig: any): Promise<{ room_id: string; room_name: string; current_players: number; max_players: number; status: string }> {
  // 转换前端字段名到后端期望的格式
  const backendLLMConfig = {
    model_name: llmConfig.modelName,
    api_key: llmConfig.apiKey,
    provider: llmConfig.provider,
    stream: llmConfig.stream || false,
    enable_thinking: llmConfig.enableThinking || false,
    client_kwargs: llmConfig.clientKwargs || {},
  };

  const response = await fetch(`${API_BASE}/rooms`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      room_name: name,
      max_players: maxPlayers,
      llm_config: backendLLMConfig
    }),
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to create room: ${response.status} - ${errorText}`);
  }
  return response.json();
}

// 添加玩家到房间
export async function joinRoom(roomId: string, playerName: string, aiConfig?: any, modelConfig?: any): Promise<RoomInfo> {
  // 转换前端字段名到后端期望的格式
  let backendModelConfig;
  if (modelConfig) {
    backendModelConfig = {
      model_name: modelConfig.modelName,
      api_key: modelConfig.apiKey,
      provider: modelConfig.provider,
      stream: modelConfig.stream || false,
      enable_thinking: modelConfig.enableThinking || false,
      client_kwargs: modelConfig.clientKwargs || {},
    };
  }

  const response = await fetch(`${API_BASE}/rooms/${roomId}/join`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      room_id: roomId,
      player_name: playerName,
      ai_config: aiConfig,
      model_configuration: backendModelConfig
    }),
  });
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Failed to join room: ${response.status} - ${errorText}`);
  }
  return response.json();
}

// 开始游戏
export async function startGame(roomId: string): Promise<GameInfo> {
  console.log(`🚀 发送开始游戏请求到: ${API_BASE}/games/${roomId}/start`);

  // 添加超时处理
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 10000); // 10秒超时

  try {
    const response = await fetch(`${API_BASE}/games/${roomId}/start`, {
      method: 'POST',
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    console.log(`📡 开始游戏API响应状态: ${response.status}`);

    if (!response.ok) {
      const error = await response.json();
      console.log(`❌ 开始游戏失败:`, error);
      throw new Error(error.detail || `Failed to start game: ${response.statusText}`);
    }

    const result = await response.json();
    console.log(`✅ 开始游戏成功:`, result);
    return result;
  } catch (error) {
    clearTimeout(timeoutId);

    if ((error as any).name === 'AbortError') {
      console.log(`⏰ 开始游戏请求超时`);
      throw new Error('Start game request timed out');
    }

    console.log(`❌ 开始游戏请求异常:`, error);
    throw error;
  }
}

// 停止游戏
export async function stopGame(gameId: string): Promise<any> {
  console.log(`🛑 发送停止游戏请求到: ${API_BASE}/games/${gameId}/stop`);

  const response = await fetch(`${API_BASE}/games/${gameId}/stop`, {
    method: 'POST',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to stop game: ${response.statusText}`);
  }

  const result = await response.json();
  console.log(`✅ 停止游戏成功:`, result);
  return result;
}

// 清理游戏资源
export async function cleanupGame(gameId: string, force: boolean = false): Promise<any> {
  const url = new URL(`${API_BASE}/games/${gameId}`);
  if (force) {
    url.searchParams.append('force', 'true');
  }

  const response = await fetch(url.toString(), {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to cleanup game: ${response.statusText}`);
  }

  return response.json();
}

// 获取完整游戏数据（包含所有事件）
export async function getFullGameData(gameId: string): Promise<any> {
  const response = await fetch(`${API_BASE}/games/${gameId}`);
  if (!response.ok) {
    throw new Error(`Failed to get game data: ${response.statusText}`);
  }
  return response.json();
}

// 获取游戏状态（当前状态，不包含完整事件）
export async function getGameState(gameId: string): Promise<unknown> {
  const response = await fetch(`${API_BASE}/games/${gameId}/state`);
  if (!response.ok) {
    throw new Error(`Failed to get game state: ${response.statusText}`);
  }
  return response.json();
}

// 获取游戏事件
export async function getGameEvents(gameId: string, since?: string): Promise<unknown[]> {
  const url = since 
    ? `${API_BASE}/games/${gameId}/events?since=${since}`
    : `${API_BASE}/games/${gameId}/events`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to get game events: ${response.statusText}`);
  }
  return response.json();
}


