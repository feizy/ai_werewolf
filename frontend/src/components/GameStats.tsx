import React from 'react';
import { Player, ROLE_CONFIG } from '@/types/game';

interface GameStatsProps {
  players?: Player[];
}

export const GameStats: React.FC<GameStatsProps> = ({ players }) => {
  // 确保players是一个数组
  const safePlayers = players || [];

  const alivePlayers = safePlayers.filter(p => p.status === 'alive');
  const deadPlayers = safePlayers.filter(p => p.status === 'dead');
  
  const aliveWerewolves = alivePlayers.filter(p => p.role === 'werewolf').length;
  const aliveVillagers = alivePlayers.filter(p => {
    return p.role &&
           p.role !== 'werewolf' &&
           p.role in ROLE_CONFIG &&
           ROLE_CONFIG[p.role as keyof typeof ROLE_CONFIG].team === 'villager';
  }).length;

  return (
    <div style={{
      display: 'flex',
      gap: '16px',
      padding: '12px 20px',
      background: 'rgba(15, 23, 42, 0.6)',
      borderRadius: '10px',
      backdropFilter: 'blur(8px)',
    }}>
      {/* 存活统计 */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
      }}>
        <span style={{ fontSize: '18px' }}>👥</span>
        <div>
          <div style={{ fontSize: '11px', color: '#64748b' }}>存活</div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: '#4ade80' }}>
            {alivePlayers.length}
          </div>
        </div>
      </div>

      <div style={{ width: '1px', background: '#334155' }} />

      {/* 狼人统计 */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
      }}>
        <span style={{ fontSize: '18px' }}>🐺</span>
        <div>
          <div style={{ fontSize: '11px', color: '#64748b' }}>狼人</div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: '#ef4444' }}>
            {aliveWerewolves}
          </div>
        </div>
      </div>

      <div style={{ width: '1px', background: '#334155' }} />

      {/* 好人统计 */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
      }}>
        <span style={{ fontSize: '18px' }}>🛡️</span>
        <div>
          <div style={{ fontSize: '11px', color: '#64748b' }}>好人</div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: '#3b82f6' }}>
            {aliveVillagers}
          </div>
        </div>
      </div>

      <div style={{ width: '1px', background: '#334155' }} />

      {/* 死亡统计 */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
      }}>
        <span style={{ fontSize: '18px' }}>💀</span>
        <div>
          <div style={{ fontSize: '11px', color: '#64748b' }}>死亡</div>
          <div style={{ fontSize: '18px', fontWeight: 700, color: '#94a3b8' }}>
            {deadPlayers.length}
          </div>
        </div>
      </div>
    </div>
  );
};


