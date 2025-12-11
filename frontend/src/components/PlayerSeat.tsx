import React from 'react';
import { motion } from 'framer-motion';
import { RoomPlayer } from '@/types/game';

interface PlayerSeatProps {
  position: number;
  player?: RoomPlayer;
  onAddPlayer: (position: number) => void;
  isSelected?: boolean;
}

export const PlayerSeat: React.FC<PlayerSeatProps> = ({
  position,
  player,
  onAddPlayer,
  isSelected = false,
}) => {
  const angle = (position * 360) / 9 - 90; // 9个座位，起始角度-90度
  const radius = 180; // 圆桌半径

  const x = Math.cos((angle * Math.PI) / 180) * radius;
  const y = Math.sin((angle * Math.PI) / 180) * radius;

  return (
    <motion.div
      initial={{ scale: 0, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ delay: position * 0.1 }}
      style={{
        position: 'absolute',
        left: `calc(50% + ${x}px - 50px)`,
        top: `calc(50% + ${y}px - 50px)`,
        width: '100px',
        height: '100px',
        zIndex: 2, // 确保在圆桌背景之上
      }}
    >
      <motion.div
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        style={{
          width: '100%',
          height: '100%',
          borderRadius: '50%',
          border: isSelected ? '3px solid #6366f1' : '2px solid #334155',
          background: player ? 'rgba(99, 102, 241, 0.1)' : 'rgba(71, 85, 105, 0.3)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: player ? 'pointer' : 'pointer',
          boxShadow: isSelected
            ? '0 0 20px rgba(99, 102, 241, 0.4)'
            : '0 4px 12px rgba(0, 0, 0, 0.2)',
          backdropFilter: 'blur(8px)',
        }}
        onClick={() => !player && onAddPlayer(position)}
      >
        {player ? (
          <>
            {/* 玩家头像 */}
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
              fontSize: '18px',
              fontWeight: 'bold',
              marginBottom: '4px',
            }}>
              {player.name.charAt(0).toUpperCase()}
            </div>

            {/* 玩家信息 */}
            <div style={{
              textAlign: 'center',
              color: '#f1f5f9',
              fontSize: '12px',
            }}>
              <div style={{ fontWeight: 'bold', marginBottom: '2px' }}>
                {player.name}
              </div>
              <div style={{
                color: '#94a3b8',
                fontSize: '10px',
              }}>
                位置 {player.position + 1}
              </div>
            </div>

            {/* AI 标识 */}
            {player.isAI && (
              <div style={{
                position: 'absolute',
                top: '-5px',
                right: '-5px',
                width: '20px',
                height: '20px',
                borderRadius: '50%',
                background: '#22c55e',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '10px',
              }}>
                🤖
              </div>
            )}
          </>
        ) : (
          <>
            {/* 空座位 */}
            <motion.div
              animate={{ rotate: [0, 10, -10, 0] }}
              transition={{ duration: 2, repeat: Infinity }}
              style={{
                fontSize: '32px',
                color: '#64748b',
                marginBottom: '4px',
              }}
            >
              ➕
            </motion.div>
            <div style={{
              color: '#94a3b8',
              fontSize: '11px',
              textAlign: 'center',
            }}>
              点击添加<br/>玩家
            </div>
            <div style={{
              color: '#64748b',
              fontSize: '10px',
              marginTop: '2px',
            }}>
              位置 {position + 1}
            </div>
          </>
        )}
      </motion.div>
    </motion.div>
  );
};
