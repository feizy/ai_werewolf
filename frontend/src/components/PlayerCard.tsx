import React from 'react';
import { motion } from 'framer-motion';
import { Player, ROLE_CONFIG, RoleType } from '@/types/game';

interface PlayerCardProps {
  player: Player;
  isSelected: boolean;
  onClick: () => void;
}

export const PlayerCard: React.FC<PlayerCardProps> = ({ player, isSelected, onClick }) => {
  const roleConfig = player.role ? ROLE_CONFIG[player.role] : null;
  const isDead = player.status === 'dead';

  return (
    <motion.div
      onClick={onClick}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      style={{
        width: '100px',
        height: '130px',
        borderRadius: '12px',
        background: isDead 
          ? 'linear-gradient(135deg, #374151 0%, #1f2937 100%)'
          : isSelected
            ? 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)'
            : 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
        border: `2px solid ${isSelected ? '#818cf8' : isDead ? '#4b5563' : '#334155'}`,
        cursor: 'pointer',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        padding: '10px',
        position: 'relative',
        boxShadow: isSelected 
          ? '0 0 20px rgba(99, 102, 241, 0.4)' 
          : '0 4px 12px rgba(0, 0, 0, 0.3)',
        opacity: isDead ? 0.6 : 1,
        transition: 'all 0.2s ease',
      }}
    >
      {/* 警长徽章 */}
      {player.isSheriff && (
        <div style={{
          position: 'absolute',
          top: '-8px',
          right: '-8px',
          fontSize: '20px',
          filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.3))',
        }}>
          🎖️
        </div>
      )}

      {/* 位置编号 */}
      <div style={{
        position: 'absolute',
        top: '4px',
        left: '8px',
        fontSize: '11px',
        color: '#94a3b8',
        fontWeight: 600,
      }}>
        {player.position}号
      </div>

      {/* 角色图标 */}
      <div style={{
        fontSize: '32px',
        marginTop: '8px',
        filter: isDead ? 'grayscale(1)' : 'none',
      }}>
        {roleConfig?.icon || '❓'}
      </div>

      {/* 玩家名 */}
      <div style={{
        fontSize: '13px',
        fontWeight: 600,
        color: isDead ? '#9ca3af' : '#f1f5f9',
        marginTop: '6px',
        textAlign: 'center',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
        width: '100%',
      }}>
        {player.name}
      </div>

      {/* 角色名 */}
      {roleConfig && (
        <div style={{
          fontSize: '11px',
          color: isDead ? '#6b7280' : roleConfig.color,
          marginTop: '2px',
          fontWeight: 500,
        }}>
          {roleConfig.name}
        </div>
      )}

      {/* 状态指示 */}
      <div style={{
        display: 'flex',
        gap: '4px',
        marginTop: 'auto',
        fontSize: '11px',
      }}>
        {isDead && (
          <span style={{ color: '#ef4444' }}>💀 死亡</span>
        )}
        {!isDead && player.abilities && (
          <>
            {player.role === 'witch' && (
              <>
                {player.abilities.witchHasAntidote && <span title="解药">💊</span>}
                {player.abilities.witchHasPoison && <span title="毒药">☠️</span>}
              </>
            )}
            {player.role === 'hunter' && player.abilities.hunterCanShoot && (
              <span title="可开枪">🔫</span>
            )}
          </>
        )}
      </div>
    </motion.div>
  );
};


