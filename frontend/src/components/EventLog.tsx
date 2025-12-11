import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { GameEvent, EventCategory, EVENT_CATEGORY_CONFIG, PHASE_CONFIG } from '@/types/game';

interface EventLogProps {
  events: GameEvent[];
  filters: EventCategory[];
  autoScroll: boolean;
  onFilterToggle: (category: EventCategory) => void;
}

const EventItem: React.FC<{ event: GameEvent }> = ({ event }) => {
  const categoryConfig = EVENT_CATEGORY_CONFIG[event.category];
  const phaseConfig = PHASE_CONFIG[event.phase];

  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      style={{
        padding: '12px 16px',
        borderBottom: '1px solid rgba(71, 85, 105, 0.3)',
        background: 'rgba(15, 23, 42, 0.4)',
      }}
    >
      {/* 头部信息 */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        marginBottom: '6px',
      }}>
        {/* 类别标签 */}
        <span style={{
          fontSize: '11px',
          padding: '2px 8px',
          borderRadius: '4px',
          background: `${categoryConfig.color}20`,
          color: categoryConfig.color,
          fontWeight: 600,
        }}>
          {categoryConfig.icon} {categoryConfig.name}
        </span>

        {/* 阶段 */}
        <span style={{
          fontSize: '10px',
          color: '#64748b',
        }}>
          第{event.day}天 {phaseConfig.name}
        </span>

        {/* 时间 */}
        <span style={{
          fontSize: '10px',
          color: '#475569',
          marginLeft: 'auto',
        }}>
          {new Date(event.timestamp).toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
          })}
        </span>
      </div>

      {/* 发言者 */}
      {event.actorName && (
        <div style={{
          fontSize: '12px',
          color: '#94a3b8',
          marginBottom: '4px',
        }}>
          <span style={{ fontWeight: 600, color: '#e2e8f0' }}>{event.actorName}</span>
          {event.targetName && (
            <span> → <span style={{ color: '#f59e0b' }}>{event.targetName}</span></span>
          )}
        </div>
      )}

      {/* 内容 */}
      <div style={{
        fontSize: '13px',
        color: '#e2e8f0',
        lineHeight: 1.6,
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
      }}>
        {event.content}
      </div>
    </motion.div>
  );
};

export const EventLog: React.FC<EventLogProps> = ({
  events,
  filters,
  autoScroll,
  onFilterToggle,
}) => {
  const listRef = useRef<HTMLDivElement>(null);

  // 调试信息
  console.log('📝 EventLog组件接收到的事件数量:', events.length);
  console.log('📝 事件列表:', events);

  // 过滤事件
  const filteredEvents = filters.length === 0
    ? events
    : events.filter(e => filters.includes(e.category));

  // 自动滚动
  useEffect(() => {
    if (autoScroll && listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [filteredEvents.length, autoScroll]);

  const categories: EventCategory[] = ['MODERATOR', 'SPEECH', 'ACTION', 'VOTE', 'DEATH', 'SYSTEM'];

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      background: 'linear-gradient(180deg, #1e293b 0%, #0f172a 100%)',
      borderRadius: '12px',
      overflow: 'hidden',
    }}>
      {/* 标题 */}
      <div style={{
        padding: '16px 20px',
        borderBottom: '1px solid #334155',
        background: 'rgba(30, 41, 59, 0.8)',
      }}>
        <h3 style={{
          margin: 0,
          fontSize: '16px',
          fontWeight: 600,
          color: '#f1f5f9',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}>
          📜 游戏日志
          <span style={{
            fontSize: '12px',
            color: '#64748b',
            fontWeight: 400,
          }}>
            ({filteredEvents.length} 条)
          </span>
        </h3>
      </div>

      {/* 过滤器 */}
      <div style={{
        padding: '12px 16px',
        borderBottom: '1px solid #334155',
        display: 'flex',
        flexWrap: 'wrap',
        gap: '6px',
      }}>
        {categories.map(category => {
          const config = EVENT_CATEGORY_CONFIG[category];
          const isActive = filters.length === 0 || filters.includes(category);
          return (
            <button
              key={category}
              onClick={() => onFilterToggle(category)}
              style={{
                padding: '4px 10px',
                fontSize: '11px',
                borderRadius: '4px',
                border: 'none',
                cursor: 'pointer',
                background: isActive ? `${config.color}30` : 'transparent',
                color: isActive ? config.color : '#64748b',
                fontWeight: 500,
                transition: 'all 0.2s ease',
              }}
            >
              {config.icon} {config.name}
            </button>
          );
        })}
      </div>

      {/* 事件列表 */}
      <div
        ref={listRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          overflowX: 'hidden',
        }}
      >
        <AnimatePresence>
          {filteredEvents.length === 0 ? (
            <div style={{
              padding: '40px 20px',
              textAlign: 'center',
              color: '#64748b',
            }}>
              <div style={{ fontSize: '32px', marginBottom: '12px' }}>📭</div>
              <div>暂无事件</div>
            </div>
          ) : (
            filteredEvents.map(event => (
              <EventItem key={event.id} event={event} />
            ))
          )}
        </AnimatePresence>
      </div>
    </div>
  );
};


