import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { PlayerCircle } from './components/PlayerCircle';
import { EventLog } from './components/EventLog';
import { PhaseBanner } from './components/PhaseBanner';
import { GameStats } from './components/GameStats';
import { useGameStore } from './store/gameStore';
import { usePolling } from './hooks/usePolling';
import { checkHealth } from './services/api';

const App: React.FC = () => {
  const [roomId, setRoomId] = useState<string>('');
  const [inputRoomId, setInputRoomId] = useState<string>('');
  const [backendStatus, setBackendStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  
  const { 
    gameState, 
    selectedPlayerId,
    setSelectedPlayerId,
    eventFilters,
    toggleEventFilter,
    autoScroll,
    connectionStatus
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

  // 连接界面
  if (!roomId || !gameState) {
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

