import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { PlayerCircle } from './components/PlayerCircle';
import { PlayerSeat } from './components/PlayerSeat';
import { PlayerConfigModal } from './components/PlayerConfigModal';
import { EventLog } from './components/EventLog';
import { PhaseBanner } from './components/PhaseBanner';
import { GameStats } from './components/GameStats';
import { useGameStore } from './store/gameStore';
import { usePolling } from './hooks/usePolling';
import { checkHealth, createRoom, joinRoom, startGame } from './services/api';
import { LLMConfig } from './types/game';

// Provider options for room creation
const PROVIDER_OPTIONS = [
  { value: 'anthropic', label: 'Anthropic (Claude)', icon: '🤖' },
  { value: 'openai', label: 'OpenAI (GPT)', icon: '🧠' },
  { value: 'dashscope', label: 'DashScope (Qwen)', icon: '🦉' },
] as const;

const MODEL_PRESETS = {
  anthropic: ['glm-4', 'glm-4.6', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'],
  openai: ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo'],
  dashscope: ['qwen-max', 'qwen-plus', 'qwen-turbo'],
};

const App: React.FC = () => {
  const [roomId, setRoomId] = useState<string>('');
  const [inputRoomId, setInputRoomId] = useState<string>('');
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  // 房间创建状态
  const [roomName, setRoomName] = useState<string>('');
  const [maxPlayers, setMaxPlayers] = useState<number>(9);
  const [defaultProvider, setDefaultProvider] = useState<'anthropic' | 'openai' | 'dashscope'>('anthropic');
  const [defaultModelName, setDefaultModelName] = useState<string>('glm-4');
  const [defaultApiKey, setDefaultApiKey] = useState<string>('');

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
  } = useGameStore();

  // 使用轮询获取游戏状态
  usePolling(roomId || null, 2000);

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

  const handleConnect = () => {
    if (inputRoomId.trim()) {
      setRoomId(inputRoomId.trim());
    }
  };

  const handleProviderChange = (newProvider: typeof defaultProvider) => {
    setDefaultProvider(newProvider);
    setDefaultModelName(MODEL_PRESETS[newProvider][0]);
  };

  const handleCreateRoom = async () => {
    if (!roomName.trim() || !defaultApiKey.trim()) return;

    try {
      const response = await createRoom(roomName.trim(), maxPlayers, defaultLLMConfig);

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
      await joinRoom(room.id, name, { language: 'zh' }, llmConfig);
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

    try {
      await startGame(room.id);
      setCurrentView('game');
    } catch (error) {
      console.error('Failed to start game:', error);
      alert('开始游戏失败，请重试');
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

                  {/* 模型选择 */}
                  <select
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
                  >
                    {MODEL_PRESETS[defaultProvider].map((model) => (
                      <option key={model} value={model}>
                        {model}
                      </option>
                    ))}
                  </select>

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
                      transition: 'border-color 0.2s',
                    }}
                    onFocus={(e) => e.target.style.borderColor = '#6366f1'}
                    onBlur={(e) => e.target.style.borderColor = '#334155'}
                  />
                </div>
              </div>

              <button
                onClick={handleCreateRoom}
                disabled={!roomName.trim() || !defaultApiKey.trim() || backendStatus !== 'online'}
                style={{
                  width: '100%',
                  padding: '14px',
                  borderRadius: '10px',
                  border: 'none',
                  background: (!roomName.trim() || !defaultLLMConfig.apiKey.trim() || backendStatus !== 'online')
                    ? '#475569'
                    : 'linear-gradient(135deg, #10b981, #059669)',
                  color: '#fff',
                  fontSize: '16px',
                  fontWeight: 600,
                  cursor: (!roomName.trim() || !defaultLLMConfig.apiKey.trim() || backendStatus !== 'online')
                    ? 'not-allowed'
                    : 'pointer',
                  transition: 'transform 0.2s, box-shadow 0.2s',
                }}
                onMouseEnter={(e) => {
                  if (roomName.trim() && defaultApiKey.trim() && backendStatus === 'online') {
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

          {/* 提示 */}
          <p style={{ 
            marginTop: '24px', 
            fontSize: '13px', 
            color: '#64748b',
            lineHeight: 1.6,
          }}>
            💡 先在后端运行 <code style={{ 
              background: '#1e293b', 
              padding: '2px 6px', 
              borderRadius: '4px',
              fontSize: '12px',
            }}>python start_game.py</code> 创建游戏，<br/>
            然后输入返回的房间 ID 连接观战
          </p>

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
          padding: '40px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          minHeight: 'calc(100vh - 81px)',
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
            width: '600px',
            height: '600px',
            margin: '0 auto',
          }}>
            {/* 中心桌 */}
            <motion.div
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                width: '200px',
                height: '200px',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.1))',
                border: '2px solid rgba(99, 102, 241, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: 'inset 0 0 50px rgba(99, 102, 241, 0.1)',
              }}
            >
              <div style={{
                textAlign: 'center',
                color: '#94a3b8',
              }}>
                <div style={{ fontSize: '48px', marginBottom: '8px' }}>🎯</div>
                <div style={{ fontSize: '14px', fontWeight: 600 }}>狼人杀</div>
                <div style={{ fontSize: '12px' }}>房间 {room.id.slice(0, 8)}</div>
              </div>
            </motion.div>

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

  if (!gameState) {
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
        <div style={{ textAlign: 'center' }}>
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            style={{ fontSize: '48px', marginBottom: '16px' }}
          >
            ⏳
          </motion.div>
          <h2 style={{ margin: '0 0 8px', fontSize: '24px' }}>正在加载游戏...</h2>
          <p style={{ margin: 0, color: '#94a3b8' }}>请稍候</p>
        </div>
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

        <GameStats players={gameState.players} />
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
        </div>

        {/* 右侧：事件日志 */}
        <div style={{
          width: '420px',
          borderLeft: '1px solid #334155',
          background: 'rgba(15, 23, 42, 0.6)',
        }}>
          <EventLog
            events={gameState.events}
            filters={eventFilters}
            autoScroll={autoScroll}
            onFilterToggle={toggleEventFilter}
          />
        </div>
      </div>
    </div>
  );
};

export default App;

