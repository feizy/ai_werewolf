// API 服务 - 连接后端 localhost:8001

const API_BASE = ''; // 使用 Vite 代理，不需要前缀

export interface RoomInfo {
  id: string;
  name: string;
  current_players: number;
  max_players: number;
  is_full: boolean;
  can_start_game: boolean;
  players: Array<{
    id: string;
    name: string;
    position: number;
    is_ai: boolean;
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
export async function createRoom(name: string, playerName: string): Promise<{ room_id: string; player_id: string }> {
  const response = await fetch(`${API_BASE}/rooms`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, player_name: playerName }),
  });
  if (!response.ok) {
    throw new Error(`Failed to create room: ${response.statusText}`);
  }
  return response.json();
}

// 开始游戏
export async function startGame(roomId: string): Promise<GameInfo> {
  const response = await fetch(`${API_BASE}/games/${roomId}/start`, {
    method: 'POST',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to start game: ${response.statusText}`);
  }
  return response.json();
}

// 获取游戏状态
export async function getGameState(gameId: string): Promise<unknown> {
  const response = await fetch(`${API_BASE}/games/${gameId}`);
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


