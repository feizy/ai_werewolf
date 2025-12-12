import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { Player } from '@/types/game';
import { PlayerCard } from './PlayerCard';

interface PlayerCircleProps {
  players?: Player[];
  selectedPlayerId: string | null;
  onPlayerClick: (playerId: string) => void;
}

export const PlayerCircle: React.FC<PlayerCircleProps> = ({
  players = [],
  selectedPlayerId,
  onPlayerClick,
}) => {
  const radius = 280;
  const centerX = 350;
  const centerY = 320;

  const sortedPlayers = useMemo(() => {
    if (!players || !Array.isArray(players)) return [];
    return [...players].sort((a, b) => (a.position || 0) - (b.position || 0));
  }, [players]);

  const playerPositions = useMemo(() => {
    const count = sortedPlayers.length;
    return sortedPlayers.map((player, index) => {
      // 从顶部开始，顺时针排列
      const angle = (index / count) * 2 * Math.PI - Math.PI / 2;
      const x = centerX + Math.cos(angle) * radius;
      const y = centerY + Math.sin(angle) * radius;
      return { player, x, y };
    });
  }, [sortedPlayers, radius, centerX, centerY]);

  return (
    <div style={{
      position: 'relative',
      width: '700px',
      height: '640px',
    }}>
      {/* 圆桌背景 */}
      <div style={{
        position: 'absolute',
        left: centerX - 180,
        top: centerY - 180,
        width: '360px',
        height: '360px',
        borderRadius: '50%',
        background: 'radial-gradient(circle, #1e3a5f 0%, #0f172a 100%)',
        border: '3px solid #334155',
        boxShadow: 'inset 0 0 60px rgba(0,0,0,0.5), 0 0 40px rgba(30, 58, 95, 0.3)',
      }}>
        {/* 中心文字 */}
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
        </div>
      </div>

      {/* 玩家卡片 */}
      {playerPositions.map(({ player, x, y }, index) => (
        <motion.div
          key={player.id}
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ 
            delay: index * 0.08,
            type: 'spring',
            stiffness: 200,
            damping: 20
          }}
          style={{
            position: 'absolute',
            left: x,
            top: y,
            transform: 'translate(-50%, -50%)',
          }}
        >
          <PlayerCard
            player={player}
            isSelected={selectedPlayerId === player.id}
            onClick={() => onPlayerClick(player.id)}
          />
        </motion.div>
      ))}
    </div>
  );
};


