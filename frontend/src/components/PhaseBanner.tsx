import React from 'react';
import { motion } from 'framer-motion';
import { GamePhaseType, PHASE_CONFIG } from '@/types/game';

interface PhaseBannerProps {
  phase: GamePhaseType;
  day: number;
  isRunning: boolean;
  winner?: 'werewolf' | 'villager';
}

export const PhaseBanner: React.FC<PhaseBannerProps> = ({
  phase,
  day,
  isRunning,
  winner,
}) => {
  const phaseConfig = PHASE_CONFIG[phase];

  return (
    <motion.div
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      style={{
        background: `linear-gradient(135deg, ${phaseConfig.color} 0%, ${phaseConfig.color}cc 100%)`,
        padding: '16px 32px',
        borderRadius: '12px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '16px',
        boxShadow: `0 4px 20px ${phaseConfig.color}40`,
      }}
    >
      {/* 阶段图标 */}
      <motion.span
        animate={{ 
          rotate: phase === 'night' ? [0, 10, -10, 0] : 0,
          scale: [1, 1.1, 1]
        }}
        transition={{ 
          duration: 2,
          repeat: Infinity,
          ease: 'easeInOut'
        }}
        style={{ fontSize: '36px' }}
      >
        {phaseConfig.icon}
      </motion.span>

      <div style={{ textAlign: 'center' }}>
        {/* 天数 */}
        <div style={{
          fontSize: '13px',
          color: 'rgba(255,255,255,0.8)',
          marginBottom: '2px',
        }}>
          第 {day} 天
        </div>

        {/* 阶段名称 */}
        <div style={{
          fontSize: '24px',
          fontWeight: 700,
          color: '#fff',
          textShadow: '0 2px 4px rgba(0,0,0,0.2)',
        }}>
          {phaseConfig.name}
        </div>

        {/* 游戏状态 */}
        {!isRunning && winner && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            style={{
              marginTop: '8px',
              fontSize: '16px',
              fontWeight: 600,
              color: winner === 'werewolf' ? '#fca5a5' : '#86efac',
            }}
          >
            {winner === 'werewolf' ? '🐺 狼人阵营获胜!' : '👥 好人阵营获胜!'}
          </motion.div>
        )}
      </div>

      {/* 状态指示器 */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '6px',
      }}>
        <motion.div
          animate={{
            scale: isRunning ? [1, 1.2, 1] : 1,
            opacity: isRunning ? [1, 0.5, 1] : 0.5,
          }}
          transition={{
            duration: 1,
            repeat: isRunning ? Infinity : 0,
          }}
          style={{
            width: '10px',
            height: '10px',
            borderRadius: '50%',
            background: isRunning ? '#4ade80' : '#94a3b8',
          }}
        />
        <span style={{
          fontSize: '12px',
          color: 'rgba(255,255,255,0.7)',
        }}>
          {isRunning ? '进行中' : '已结束'}
        </span>
      </div>
    </motion.div>
  );
};


