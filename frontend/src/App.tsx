import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { PlayerCircle } from './components/PlayerCircle';
import { PlayerSeat } from './components/PlayerSeat';
import { PlayerConfigModal } from './components/PlayerConfigModal';
import { EventLog } from './components/EventLog';
import { PhaseBanner } from './components/PhaseBanner';
import { GameStats } from './components/GameStats';
import { useGameStore } from './store/gameStore';
import { usePolling, convertGameState, convertPhase, convertEventType } from './hooks/usePolling';
import { checkHealth, createRoom, joinRoom, startGame, cleanupGame, getRoom, getFullGameData, getGameEvents, API_BASE } from './services/api';
import { LLMConfig } from './types/game';

// Provider options for room creation
const PROVIDER_OPTIONS = [
  { value: 'anthropic', label: 'Anthropic格式API', icon: '🤖' },
  { value: 'openai', label: 'OpenAI格式API', icon: '🧠' },
  { value: 'dashscope', label: 'DashScope', icon: '🦉' },
] as const;

const App: React.FC = () => {
  const [roomId, setRoomId] = useState<string>('');
  const [inputRoomId, setInputRoomId] = useState<string>('');
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  // 房间创建状态
  const [roomName, setRoomName] = useState<string>('');
  const [maxPlayers, setMaxPlayers] = useState<number>(9);
  const [defaultProvider, setDefaultProvider] = useState<'anthropic' | 'openai' | 'dashscope'>('anthropic');
  const [defaultModelName, setDefaultModelName] = useState<string>('');
  const [defaultApiKey, setDefaultApiKey] = useState<string>('');
  const [defaultApiBaseUrl, setDefaultApiBaseUrl] = useState<string>('');

  const defaultLLMConfig: LLMConfig = {
    provider: defaultProvider,
    modelName: defaultModelName,
    apiKey: defaultApiKey,
    temperature: 0.7,
    stream: false,
    enableThinking: false,
    clientKwargs: {},
  };

  // 玩家配置模态框
  const [showPlayerConfig, setShowPlayerConfig] = useState<boolean>(false);
  const [configPosition, setConfigPosition] = useState<number>(-1);

  const {
    room,
    currentView,
    gameState,
    selectedPlayerId,
    setSelectedPlayerId,
    eventFilters,
    toggleEventFilter,
    autoScroll,
    connectionStatus,
    setRoom,
    setCurrentView,
    addPlayerToRoom,
    setGameState,
  } = useGameStore();

  // 检查后端状态
  useEffect(() => {
    const check = async () => {
      const isHealthy = await checkHealth();
      setBackendStatus(isHealthy ? 'online' : 'offline');
    };
    check();
    const interval = setInterval(check, 10000);
    return () => clearInterval(interval);
  }, []);

  // 在点击开始游戏后开始轮询
  const [isGameStarting, setIsGameStarting] = React.useState(false);
  const [currentGameId, setCurrentGameId] = React.useState<string | null>(null);

  // 调试：监听 gameState 变化
  React.useEffect(() => {
    if (gameState === null) {
      console.log('🚨 gameState 被重置为 null! 当前视图:', currentView);
    } else {
      console.log('📊 gameState 更新:', {
        id: gameState.id,
        phase: gameState.phase,
        day: gameState.day,
        isRunning: gameState.isRunning,
        playerCount: gameState.players?.length
      });
    }
  }, [gameState, currentView]);

  // 当游戏开始请求发送后，或者游戏页面持续轮询
  const shouldPoll = isGameStarting || currentView === 'game';
  const pollingRoomId = shouldPoll ? (gameState?.id || currentGameId || roomId || null) : null;
  console.log('🤖 轮询参数设置:', { isGameStarting, currentView, roomId, currentGameId, gameId: gameState?.id, pollingRoomId, shouldPoll });
  usePolling(pollingRoomId, 2000);

  // 监听游戏状态变化，自动切换到游戏页面
  useEffect(() => {
    console.log('👀 监听游戏状态变化:', { gameState, currentView });
    if (gameState && currentView === 'room-setup') {
      console.log('🎯 检测到游戏状态，准备切换到游戏页面');
      setCurrentView('game');
      setIsGameStarting(false); // 停止轮询标记

      // 更新游戏ID
      if (gameState.id && gameState.id !== currentGameId) {
        setCurrentGameId(gameState.id);
        console.log('✅ 更新游戏ID:', gameState.id);
      }
      console.log('✅ 已切换到游戏页面');
    }
  }, [gameState, currentView, setCurrentView, currentGameId]);

  const handleConnect = async () => {
    if (!inputRoomId.trim()) return;

    try {
      const roomId = inputRoomId.trim();
      setRoomId(roomId);

      // 获取房间信息
      console.log('🔍 获取房间信息:', roomId);
      const roomData = await getRoom(roomId);
      setRoom(roomData);

      // 检查是否已经有游戏在进行
      console.log('🎮 检查游戏状态:', roomId);
      try {
        const gameData = await getFullGameData(roomId);
        const eventsData = await getGameEvents(roomId);
        console.log('✅ 发现正在进行的游戏:', gameData);

        if (gameData) {
          console.log('🎯 发现游戏数据，进入游戏页面（进行中或已结束）');
          // 设置游戏状态并直接进入游戏页面（支持进行中和已结束的游戏）
          const gameState: GameState = {
            id: gameData.session_id,
            roomId: gameData.room_id,
            day: gameData.day_count,
            phase: convertPhase(gameData.current_phase),
            players: gameData.players.map((p: any): Player => ({
              id: p.id,
              name: p.name,
              position: p.position,
              role: p.role,
              status: p.status === 'alive' ? 'alive' : 'dead',
              isSheriff: p.is_sheriff,
              votingWeight: p.voting_weight,
              abilities: p.role_abilities ? {
                witchHasAntidote: p.role_abilities.witch_has_antidote,
                witchHasPoison: p.role_abilities.witch_has_poison,
                hunterCanShoot: p.role_abilities.hunter_can_shoot,
              } : undefined,
            })),
            events: eventsData.map((e: any): GameEvent => ({
              id: e.id,
              timestamp: e.timestamp,
              day: e.day_count,
              phase: convertPhase(e.phase),
              category: convertEventType(e.type || e.event_type),
              content: e.content,
              actorId: e.actor_id,
              actorName: e.actor_name,
              targetId: e.target_id,
              targetName: e.target_name,
            })),
            winner: gameData.winner ? (gameData.winner === 'werewolf' ? 'werewolf' : 'villager' as const) : undefined,
            isRunning: gameData.is_running,
          };

          setGameState(gameState);
          setCurrentView('game');
          setCurrentGameId(gameData.session_id);

          if (gameData.is_running) {
            console.log('✅ 游戏正在进行中');
          } else if (gameData.winner) {
            console.log('🏆 游戏已结束，获胜者:', gameData.winner);
          }
        } else {
          // 没有游戏在进行，进入房间设置页面
          setCurrentView('room-setup');
        }
      } catch (gameError) {
        console.log('📝 没有正在进行的游戏，进入房间设置页面');
        setCurrentView('room-setup');
      }

      console.log('✅ 成功连接到房间:', roomData.name);
    } catch (error) {
      console.error('❌ 连接房间失败:', error);
      alert(`连接房间失败: ${error instanceof Error ? error.message : '房间ID不存在'}`);
      // 清空无效的房间ID
      setRoomId('');
      setInputRoomId('');
    }
  };

  const handleProviderChange = (newProvider: typeof defaultProvider) => {
    setDefaultProvider(newProvider);
    setDefaultModelName('');
  };

  const handleCreateRoom = async () => {
    if (!roomName.trim() || !defaultApiKey.trim() || !defaultModelName.trim()) return;

    try {
      const response = await createRoom(roomName.trim(), maxPlayers, defaultLLMConfig, defaultApiBaseUrl);

      const newRoom = {
        id: response.room_id,
        name: response.room_name,
        currentPlayers: response.current_players,
        maxPlayers: response.max_players,
        isFull: response.current_players >= response.max_players,
        canStartGame: response.current_players >= 4,
        status: response.status as any,
        players: [],
      };

      // 按正确顺序设置状态
      setCurrentView('room-setup');
      setRoom(newRoom);
      setRoomId(response.room_id);
    } catch (error) {
      console.error('Failed to create room:', error);
      alert(`创建房间失败: ${error instanceof Error ? error.message : '未知错误'}`);
    }
  };

  const handleAddPlayer = (position: number) => {
    setConfigPosition(position);
    setShowPlayerConfig(true);
  };

  const handlePlayerConfigConfirm = async (name: string, llmConfig: LLMConfig) => {
    if (!room) return;

    try {
      // 从llmConfig.clientKwargs中获取base_url
      const apiBaseUrl = llmConfig.clientKwargs?.base_url || '';
      await joinRoom(room.id, name, { language: 'zh' }, llmConfig, apiBaseUrl);
      const newPlayer = {
        id: `player-${Date.now()}`,
        name,
        position: configPosition,
        isAI: true,
        llmConfig,
      };
      addPlayerToRoom(newPlayer);
      setShowPlayerConfig(false);
      setConfigPosition(-1);
    } catch (error) {
      console.error('Failed to add player:', error);
      alert('添加玩家失败，请重试');
    }
  };

  const handleStartGame = async () => {
    if (!room) return;

    console.log('🎮 开始游戏，房间ID:', room.id);
    console.log('📋 startGame函数:', typeof startGame);

    try {
      console.log('📤 正在发送游戏开始请求...');
      const result = await startGame(room.id);
      console.log('✅ 游戏开始请求发送成功，结果:', result);

      // 保存游戏ID（响应中的game_id就是sessionId）
      if (result.game_id) {
        setCurrentGameId(result.game_id);
        console.log('✅ 设置游戏ID:', result.game_id);
      }

      // 开始轮询游戏状态
      console.log('🔄 准备设置isGameStarting为true');
      setIsGameStarting(true);
      console.log('✅ 已设置isGameStarting为true，gameId:', result.game_id);
    } catch (error) {
      console.error('❌ 开始游戏失败 - 详细错误:', error);
      console.error('❌ 错误类型:', typeof error);
      console.error('❌ 错误消息:', error instanceof Error ? error.message : String(error));
      console.error('❌ 错误堆栈:', error instanceof Error ? error.stack : 'No stack');

      alert(`开始游戏失败: ${error instanceof Error ? error.message : String(error)}`);
      setIsGameStarting(false);
    }
  };

  const handleExitRoom = async () => {
    if (!room && !gameState) return;

    const gameId = gameState?.id || room?.id;
    if (!gameId) return;

    try {
      // 强制清理游戏资源
      await cleanupGame(gameId, true);

      // 重置状态
      setGameState(null as any);
      setRoom(null as any);
      setCurrentView('home');
      setIsGameStarting(false);
    } catch (error) {
      console.error('退出房间失败:', error);
      alert(`退出房间失败: ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  // 首页 - 连接或创建房间
  if (currentView === 'home' || currentView === 'create-room') {
    return (
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#f1f5f9',
        fontFamily: "'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif",
      }}>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          style={{
            background: 'rgba(30, 41, 59, 0.8)',
            borderRadius: '20px',
            padding: '40px',
            width: '400px',
            textAlign: 'center',
            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5)',
            border: '1px solid #334155',
          }}
        >
          {/* Logo */}
          <motion.div
            animate={{ rotate: [0, 10, -10, 0] }}
            transition={{ duration: 3, repeat: Infinity }}
            style={{ fontSize: '64px', marginBottom: '16px' }}
          >
            🐺
          </motion.div>
          
          <h1 style={{
            fontSize: '28px',
            fontWeight: 700,
            marginBottom: '8px',
            background: 'linear-gradient(135deg, #818cf8, #c084fc)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>
            狼人杀 AI 对战
          </h1>
          
          <p style={{ color: '#94a3b8', marginBottom: '32px' }}>
            观看 AI 玩家进行狼人杀对战
          </p>

          {/* 后端状态 */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '8px',
            marginBottom: '24px',
            padding: '8px 16px',
            borderRadius: '8px',
            background: backendStatus === 'online' ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
          }}>
            <div style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              background: backendStatus === 'online' ? '#22c55e' : backendStatus === 'checking' ? '#f59e0b' : '#ef4444',
            }} />
            <span style={{ fontSize: '14px', color: '#94a3b8' }}>
              后端服务: {backendStatus === 'online' ? '已连接' : backendStatus === 'checking' ? '检查中...' : '未连接'}
            </span>
          </div>

          {/* 选项卡式选择 */}
          <div style={{
            display: 'flex',
            background: '#0f172a',
            borderRadius: '10px',
            padding: '4px',
            marginBottom: '20px',
          }}>
            <button
              onClick={() => setCurrentView('home')}
              style={{
                flex: 1,
                padding: '10px 16px',
                borderRadius: '8px',
                border: 'none',
                background: currentView === 'home' ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : 'transparent',
                color: currentView === 'home' ? '#fff' : '#94a3b8',
                fontSize: '14px',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
            >
              连接房间
            </button>
            <button
              onClick={() => setCurrentView('create-room')}
              style={{
                flex: 1,
                padding: '10px 16px',
                borderRadius: '8px',
                border: 'none',
                background: currentView === 'create-room' ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : 'transparent',
                color: currentView === 'create-room' ? '#fff' : '#94a3b8',
                fontSize: '14px',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.2s',
              }}
            >
              创建房间
            </button>
          </div>

          {currentView === 'home' ? (
            <>
              {/* 房间 ID 输入 */}
              <div style={{ marginBottom: '16px' }}>
                <input
                  type="text"
                  placeholder="输入房间 ID"
                  value={inputRoomId}
                  onChange={(e) => setInputRoomId(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleConnect()}
                  style={{
                    width: '100%',
                    padding: '14px 18px',
                    borderRadius: '10px',
                    border: '2px solid #334155',
                    background: '#0f172a',
                    color: '#f1f5f9',
                    fontSize: '15px',
                    outline: 'none',
                    transition: 'border-color 0.2s',
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#6366f1'}
                  onBlur={(e) => e.target.style.borderColor = '#334155'}
                />
              </div>

              <button
                onClick={handleConnect}
                disabled={!inputRoomId.trim() || backendStatus !== 'online'}
                style={{
                  width: '100%',
                  padding: '14px',
                  borderRadius: '10px',
                  border: 'none',
                  background: backendStatus === 'online' ? 'linear-gradient(135deg, #6366f1, #8b5cf6)' : '#475569',
                  color: '#fff',
                  fontSize: '16px',
                  fontWeight: 600,
                  cursor: backendStatus === 'online' ? 'pointer' : 'not-allowed',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                }}
                onMouseEnter={(e) => {
                  if (backendStatus === 'online') {
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = '0 10px 30px rgba(99, 102, 241, 0.4)';
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                连接游戏
              </button>
            </>
          ) : (
            <>
              {/* 创建房间表单 */}
              <div style={{ marginBottom: '20px' }}>
                <div style={{ marginBottom: '16px' }}>
                  <input
                    type="text"
                    placeholder="房间名称"
                    value={roomName}
                    onChange={(e) => setRoomName(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '14px 18px',
                      borderRadius: '10px',
                      border: '2px solid #334155',
                      background: '#0f172a',
                      color: '#f1f5f9',
                      fontSize: '15px',
                      outline: 'none',
                      marginBottom: '12px',
                      transition: 'border-color 0.2s',
                    }}
                    onFocus={(e) => e.target.style.borderColor = '#6366f1'}
                    onBlur={(e) => e.target.style.borderColor = '#334155'}
                  />

                  <select
                    value={maxPlayers}
                    onChange={(e) => setMaxPlayers(Number(e.target.value))}
                    style={{
                      width: '100%',
                      padding: '14px 18px',
                      borderRadius: '10px',
                      border: '2px solid #334155',
                      background: '#0f172a',
                      color: '#f1f5f9',
                      fontSize: '15px',
                      outline: 'none',
                      marginBottom: '12px',
                    }}
                  >
                    {[4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20].map(num => (
                      <option key={num} value={num}>{num} 人房间</option>
                    ))}
                  </select>

                  {/* AI 服务商选择 */}
                  <div style={{ marginBottom: '12px' }}>
                    <label style={{
                      display: 'block',
                      marginBottom: '8px',
                      color: '#94a3b8',
                      fontSize: '14px',
                      fontWeight: 600,
                    }}>
                      AI 服务商
                    </label>
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))',
                      gap: '6px',
                    }}>
                      {PROVIDER_OPTIONS.map((option) => (
                        <button
                          key={option.value}
                          type="button"
                          onClick={() => handleProviderChange(option.value as typeof defaultProvider)}
                          style={{
                            padding: '8px 12px',
                            borderRadius: '6px',
                            border: defaultProvider === option.value ? '2px solid #6366f1' : '2px solid #334155',
                            background: defaultProvider === option.value ? 'rgba(99, 102, 241, 0.1)' : '#0f172a',
                            color: '#f1f5f9',
                            fontSize: '12px',
                            cursor: 'pointer',
                            transition: 'all 0.2s',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px',
                          }}
                        >
                          <span>{option.icon}</span>
                          <span>{option.label}</span>
                        </button>
                      ))}
                    </div>
                  </div>

                  <input
                    type="text"
                    placeholder="模型名称 (如: gpt-4, claude-3-sonnet-20240229)"
                    value={defaultModelName}
                    onChange={(e) => setDefaultModelName(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '14px 18px',
                      borderRadius: '10px',
                      border: '2px solid #334155',
                      background: '#0f172a',
                      color: '#f1f5f9',
                      fontSize: '15px',
                      outline: 'none',
                      marginBottom: '12px',
                    }}
                    onFocus={(e) => e.target.style.borderColor = '#6366f1'}
                    onBlur={(e) => e.target.style.borderColor = '#334155'}
                  />

                  <input
                    type="password"
                    placeholder="API Key"
                    value={defaultApiKey}
                    onChange={(e) => setDefaultApiKey(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '14px 18px',
                      borderRadius: '10px',
                      border: '2px solid #334155',
                      background: '#0f172a',
                      color: '#f1f5f9',
                      fontSize: '15px',
                      outline: 'none',
                      fontFamily: 'monospace',
                      marginBottom: '12px',
                      transition: 'border-color 0.2s',
                    }}
                    onFocus={(e) => e.target.style.borderColor = '#6366f1'}
                    onBlur={(e) => e.target.style.borderColor = '#334155'}
                  />

                  <input
                    type="url"
                    placeholder="API Base URL (可选，如: https://api.openai.com/v1)"
                    value={defaultApiBaseUrl}
                    onChange={(e) => setDefaultApiBaseUrl(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '14px 18px',
                      borderRadius: '10px',
                      border: '2px solid #334155',
                      background: '#0f172a',
                      color: '#f1f5f9',
                      fontSize: '15px',
                      outline: 'none',
                      fontFamily: 'monospace',
                      transition: 'border-color 0.2s',
                    }}
                    onFocus={(e) => e.target.style.borderColor = '#6366f1'}
                    onBlur={(e) => e.target.style.borderColor = '#334155'}
                  />
                </div>
              </div>

              <button
                onClick={handleCreateRoom}
                disabled={!roomName.trim() || !defaultApiKey.trim() || !defaultModelName.trim() || backendStatus !== 'online'}
                style={{
                  width: '100%',
                  padding: '14px',
                  borderRadius: '10px',
                  border: 'none',
                  background: (!roomName.trim() || !defaultApiKey.trim() || !defaultModelName.trim() || backendStatus !== 'online')
                    ? '#475569'
                    : 'linear-gradient(135deg, #10b981, #059669)',
                  color: '#fff',
                  fontSize: '16px',
                  fontWeight: 600,
                  cursor: (!roomName.trim() || !defaultApiKey.trim() || !defaultModelName.trim() || backendStatus !== 'online')
                    ? 'not-allowed'
                    : 'pointer',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                }}
                onMouseEnter={(e) => {
                  if (roomName.trim() && defaultApiKey.trim() && defaultModelName.trim() && backendStatus === 'online') {
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = '0 10px 30px rgba(16, 185, 129, 0.4)';
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                创建房间
              </button>
            </>
          )}

          
          {/* 加载状态 */}
          {roomId && !gameState && (
            <div style={{ marginTop: '24px' }}>
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                style={{ fontSize: '24px', display: 'inline-block' }}
              >
                ⏳
              </motion.div>
              <p style={{ color: '#94a3b8', marginTop: '8px' }}>
                正在获取游戏状态...
              </p>
            </div>
          )}
        </motion.div>
      </div>
    );
  }

  // 房间设置界面
  if (currentView === 'room-setup' && room) {

    return (
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
        color: '#f1f5f9',
        fontFamily: "'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif",
      }}>
        {/* 顶部导航 */}
        <header style={{
          padding: '20px 32px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid #334155',
          background: 'rgba(15, 23, 42, 0.8)',
          backdropFilter: 'blur(12px)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <h1 style={{
              margin: 0,
              fontSize: '24px',
              fontWeight: 700,
              background: 'linear-gradient(135deg, #818cf8, #c084fc)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}>
              🏠 {room.name}
            </h1>
            <div style={{
              background: 'rgba(34, 197, 94, 0.1)',
              color: '#22c55e',
              padding: '4px 12px',
              borderRadius: '20px',
              fontSize: '12px',
            }}>
              {room.currentPlayers}/{room.maxPlayers} 玩家
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <button
              onClick={() => setCurrentView('home')}
              style={{
                padding: '8px 16px',
                borderRadius: '8px',
                border: '1px solid #475569',
                background: 'transparent',
                color: '#94a3b8',
                fontSize: '14px',
                cursor: 'pointer',
              }}
            >
              返回
            </button>
            <button
              onClick={handleStartGame}
              disabled={!room.canStartGame}
              style={{
                padding: '8px 16px',
                borderRadius: '8px',
                border: 'none',
                background: room.canStartGame ? 'linear-gradient(135deg, #f59e0b, #d97706)' : '#475569',
                color: '#fff',
                fontSize: '14px',
                fontWeight: 600,
                cursor: room.canStartGame ? 'pointer' : 'not-allowed',
              }}
            >
              开始游戏
            </button>
          </div>
        </header>

        {/* 主内容区 */}
        <div style={{
          height: 'calc(100vh - 81px)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '20px',
        }}>
          {/* 房间信息 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            style={{
              textAlign: 'center',
              marginBottom: '40px',
            }}
          >
            <h2 style={{
              margin: '0 0 8px',
              fontSize: '28px',
              fontWeight: 700,
              color: '#f1f5f9',
            }}>
              房间设置
            </h2>
            <p style={{
              margin: 0,
              color: '#94a3b8',
              fontSize: '16px',
            }}>
              点击空座位添加AI玩家，最少需要4个玩家才能开始游戏
            </p>
          </motion.div>

          {/* 玩家座位圆桌 */}
          <div style={{
            position: 'relative',
            width: '700px',
            height: '700px',
            margin: '0 auto',
          }}>
            {/* 圆桌背景 */}
            <div style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              width: '360px',
              height: '360px',
              borderRadius: '50%',
              background: 'radial-gradient(circle, #1e3a5f 0%, #0f172a 100%)',
              border: '3px solid #334155',
              boxShadow: 'inset 0 0 60px rgba(0,0,0,0.5), 0 0 40px rgba(30, 58, 95, 0.3)',
              zIndex: 0,
            }}>
              {/* 中心logo */}
              <div style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                textAlign: 'center',
                color: '#64748b',
              }}>
                <div style={{ fontSize: '48px', marginBottom: '8px' }}>🐺</div>
                <div style={{ fontSize: '14px', fontWeight: 500 }}>狼人杀</div>
                <div style={{ fontSize: '10px', color: '#94a3b8', marginTop: '4px' }}>房间 {room.id.slice(0, 8)}</div>
              </div>
            </div>

            {/* 9个座位 */}
            {Array.from({ length: room.maxPlayers }, (_, i) => {
              const player = room.players.find(p => p.position === i);
              return (
                <PlayerSeat
                  key={i}
                  position={i}
                  player={player}
                  onAddPlayer={handleAddPlayer}
                  isSelected={configPosition === i}
                />
              );
            })}
          </div>

          {/* 玩家列表 */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            style={{
              marginTop: '40px',
              padding: '24px',
              background: 'rgba(30, 41, 59, 0.6)',
              borderRadius: '12px',
              border: '1px solid #334155',
              width: '100%',
              maxWidth: '600px',
            }}
          >
            <h3 style={{
              margin: '0 0 16px',
              fontSize: '18px',
              fontWeight: 600,
              color: '#f1f5f9',
            }}>
              已添加玩家 ({room.currentPlayers}/{room.maxPlayers})
            </h3>

            {room.players.length === 0 ? (
              <p style={{
                margin: 0,
                color: '#64748b',
                textAlign: 'center',
                padding: '20px',
              }}>
                还没有添加任何玩家，点击上面的座位来添加AI玩家
              </p>
            ) : (
              <div style={{
                display: 'grid',
                gap: '8px',
              }}>
                {room.players.map((player) => (
                  <div
                    key={player.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '12px 16px',
                      background: 'rgba(15, 23, 42, 0.6)',
                      borderRadius: '8px',
                      border: '1px solid #334155',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div style={{
                        width: '32px',
                        height: '32px',
                        borderRadius: '50%',
                        background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                        fontSize: '14px',
                        fontWeight: 'bold',
                      }}>
                        {player.name.charAt(0).toUpperCase()}
                      </div>
                      <div>
                        <div style={{ fontWeight: 600, color: '#f1f5f9' }}>
                          {player.name}
                        </div>
                        <div style={{ fontSize: '12px', color: '#64748b' }}>
                          位置 {player.position + 1} • {player.llmConfig?.provider.toUpperCase()}
                        </div>
                      </div>
                    </div>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                    }}>
                      <span style={{
                        fontSize: '12px',
                        color: '#22c55e',
                        fontWeight: 600,
                      }}>
                        🤖 AI
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        </div>

        {/* 玩家配置模态框 */}
        <PlayerConfigModal
          isOpen={showPlayerConfig}
          position={configPosition}
          onClose={() => {
            setShowPlayerConfig(false);
            setConfigPosition(-1);
          }}
          onConfirm={handlePlayerConfigConfirm}
        />
      </div>
    );
  }


  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%)',
      color: '#f1f5f9',
      fontFamily: "'Noto Sans SC', -apple-system, BlinkMacSystemFont, sans-serif",
    }}>
      {/* 顶部横幅 */}
      <header style={{
        padding: '20px 32px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '1px solid #334155',
        background: 'rgba(15, 23, 42, 0.8)',
        backdropFilter: 'blur(12px)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <h1 style={{
            margin: 0,
            fontSize: '24px',
            fontWeight: 700,
            background: 'linear-gradient(135deg, #818cf8, #c084fc)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}>
            🐺 狼人杀 AI 对战
          </h1>

          {/* 连接状态 */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            padding: '4px 12px',
            borderRadius: '20px',
            background: connectionStatus === 'connected' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)',
            fontSize: '12px',
          }}>
            <div style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: connectionStatus === 'connected' ? '#22c55e' : '#ef4444',
            }} />
            {connectionStatus === 'connected' ? '已连接' : '未连接'}
          </div>
        </div>

        {gameState && <GameStats players={gameState.players} />}

        {/* 退出房间按钮 */}
        {gameState && (
          <button
            onClick={handleExitRoom}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              border: '1px solid #ef4444',
              background: 'rgba(239, 68, 68, 0.1)',
              color: '#ef4444',
              fontSize: '12px',
              fontWeight: 500,
              cursor: 'pointer',
              transition: 'all 0.2s',
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.2)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
            }}
          >
            退出房间
          </button>
        )}
      </header>

      {/* 主内容区 */}
      <div style={{
        display: 'flex',
        height: 'calc(100vh - 81px)',
      }}>

        {/* 左侧：游戏区域 */}
        <div style={{
          flex: 1,
          padding: '24px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: '24px',
          overflowY: 'auto',
        }}>
          {gameState && gameState.phase && gameState.players ? (
            <>
              {/* 阶段横幅 */}
              <PhaseBanner
                phase={gameState.phase}
                day={gameState.day}
                isRunning={gameState.isRunning}
                winner={gameState.winner}
              />

              {/* 玩家圆桌 */}
              <PlayerCircle
                players={gameState.players}
                selectedPlayerId={selectedPlayerId}
                onPlayerClick={setSelectedPlayerId}
              />
            </>
          ) : (
            /* 房间设置界面 */
            <div style={{
              maxWidth: '800px',
              width: '100%',
              textAlign: 'center',
            }}>
              <div style={{
                background: 'rgba(30, 41, 59, 0.8)',
                borderRadius: '16px',
                padding: '32px',
                boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
              }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>🎯</div>
                <h2 style={{
                  margin: '0 0 16px 0',
                  fontSize: '28px',
                  fontWeight: 700,
                  background: 'linear-gradient(135deg, #818cf8, #c084fc)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                }}>
                  房间设置完成
                </h2>
                <p style={{
                  margin: '0 0 24px 0',
                  color: '#94a3b8',
                  fontSize: '16px',
                  lineHeight: 1.6,
                }}>
                  房间已创建，所有玩家已就位。请在后端使用 <code>python start_game.py</code> 开始游戏。
                </p>

                {/* 房间信息 */}
                <div style={{
                  background: 'rgba(15, 23, 42, 0.6)',
                  borderRadius: '8px',
                  padding: '16px',
                  marginBottom: '24px',
                  textAlign: 'left',
                }}>
                  <h3 style={{ margin: '0 0 12px 0', color: '#f1f5f9' }}>房间信息</h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '14px' }}>
                    <div>房间ID: <span style={{ color: '#818cf8' }}>{room!.id}</span></div>
                    <div>房间名: <span style={{ color: '#818cf8' }}>{room!.name}</span></div>
                    <div>玩家数: <span style={{ color: '#818cf8' }}>{room!.currentPlayers}/{room!.maxPlayers}</span></div>
                    <div>状态: <span style={{ color: room!.canStartGame ? '#22c55e' : '#f59e0b' }}>
                      {room!.canStartGame ? '可开始' : '等待中'}
                    </span></div>
                  </div>
                </div>

                {/* 玩家列表 */}
                <div style={{
                  background: 'rgba(15, 23, 42, 0.6)',
                  borderRadius: '8px',
                  padding: '16px',
                  textAlign: 'left',
                }}>
                  <h3 style={{ margin: '0 0 12px 0', color: '#f1f5f9' }}>玩家列表 ({room!.players.length})</h3>
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))',
                    gap: '8px',
                  }}>
                    {room!.players.map(player => (
                      <div key={player.id} style={{
                        background: 'rgba(71, 85, 105, 0.3)',
                        padding: '8px',
                        borderRadius: '6px',
                        fontSize: '13px',
                        textAlign: 'center',
                      }}>
                        <div style={{ fontWeight: 600, color: '#f1f5f9' }}>{player.name}</div>
                        <div style={{ color: '#94a3b8', fontSize: '11px' }}>位置 {player.position}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 右侧：信息栏 */}
        <div style={{
          width: '350px',
          display: 'flex',
          flexDirection: 'column',
          gap: '20px',
          padding: '24px 24px 24px 0',
          overflowY: 'auto',
        }}>

          {gameState ? (
            <>
              {/* 游戏统计 */}
              <GameStats players={gameState.players} />

              {/* 事件日志 */}
              <div style={{ flex: 1, minHeight: 0 }}>
                <EventLog
                  events={gameState.events}
                  filters={eventFilters}
                  autoScroll={autoScroll}
                  onFilterToggle={toggleEventFilter}
                />
              </div>
            </>
          ) : (
            /* 等待游戏开始的界面 */
            <div style={{
              padding: '20px',
              background: 'rgba(30, 41, 59, 0.6)',
              borderRadius: '12px',
              textAlign: 'center',
            }}>
              <div style={{ fontSize: '48px', marginBottom: '16px' }}>⏳</div>
              <h3 style={{
                margin: '0 0 12px 0',
                fontSize: '18px',
                fontWeight: 600,
                color: '#f1f5f9',
              }}>
                等待游戏开始
              </h3>
              <p style={{
                margin: 0,
                color: '#94a3b8',
                fontSize: '14px',
                lineHeight: 1.6,
              }}>
                游戏正在后台准备中，<br/>
                请稍候或联系管理员启动游戏。
              </p>

              {room && (
                <div style={{
                  marginTop: '20px',
                  padding: '12px',
                  background: 'rgba(15, 23, 42, 0.4)',
                  borderRadius: '8px',
                  fontSize: '12px',
                  color: '#64748b',
                }}>
                  <div>房间ID: {room.id.slice(0, 8)}...</div>
                  <div>玩家: {room.currentPlayers}/{room.maxPlayers}</div>
                  <div>状态: {room.canStartGame ? '可开始' : '等待中'}</div>
                </div>
              )}
            </div>
          )}
        </div>

      </div>
    </div>
  );
};

export default App;

