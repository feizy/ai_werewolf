import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { LLMConfig } from '@/types/game';

interface PlayerConfigModalProps {
  isOpen: boolean;
  position: number;
  onClose: () => void;
  onConfirm: (name: string, llmConfig: LLMConfig) => void;
}

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

export const PlayerConfigModal: React.FC<PlayerConfigModalProps> = ({
  isOpen,
  position,
  onClose,
  onConfirm,
}) => {
  const [playerName, setPlayerName] = useState('');
  const [provider, setProvider] = useState<'anthropic' | 'openai' | 'dashscope'>('anthropic');
  const [modelName, setModelName] = useState('glm-4');
  const [apiKey, setApiKey] = useState('');
  const [temperature, setTemperature] = useState(0.7);
  const [stream, setStream] = useState(false);
  const [enableThinking, setEnableThinking] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!playerName.trim() || !apiKey.trim()) return;

    const llmConfig: LLMConfig = {
      provider,
      modelName,
      apiKey,
      temperature,
      stream,
      enableThinking,
      clientKwargs: {},
    };

    onConfirm(playerName.trim(), llmConfig);
  };

  const handleProviderChange = (newProvider: typeof provider) => {
    setProvider(newProvider);
    setModelName(MODEL_PRESETS[newProvider][0]);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* 背景遮罩 */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              background: 'rgba(0, 0, 0, 0.6)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              zIndex: 1000,
            }}
            onClick={onClose}
          />

          {/* 模态框 */}
          <motion.div
            initial={{ scale: 0.8, opacity: 0, y: 20 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.8, opacity: 0, y: 20 }}
            style={{
              position: 'fixed',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
              borderRadius: '20px',
              padding: '32px',
              width: '500px',
              maxWidth: '90vw',
              maxHeight: '90vh',
              overflow: 'auto',
              zIndex: 1001,
              border: '1px solid #334155',
              boxShadow: '0 25px 50px rgba(0, 0, 0, 0.5)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* 标题 */}
            <div style={{
              textAlign: 'center',
              marginBottom: '24px',
            }}>
              <h2 style={{
                margin: 0,
                fontSize: '24px',
                fontWeight: 700,
                background: 'linear-gradient(135deg, #818cf8, #c084fc)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}>
                添加玩家 - 位置 {position + 1}
              </h2>
              <p style={{
                margin: '8px 0 0',
                color: '#94a3b8',
                fontSize: '14px',
              }}>
                配置AI玩家的名称和LLM设置
              </p>
            </div>

            <form onSubmit={handleSubmit}>
              {/* 玩家名称 */}
              <div style={{ marginBottom: '20px' }}>
                <label style={{
                  display: 'block',
                  marginBottom: '8px',
                  color: '#f1f5f9',
                  fontSize: '14px',
                  fontWeight: 600,
                }}>
                  玩家名称 *
                </label>
                <input
                  type="text"
                  value={playerName}
                  onChange={(e) => setPlayerName(e.target.value)}
                  placeholder="输入玩家名称"
                  required
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    borderRadius: '8px',
                    border: '2px solid #334155',
                    background: '#0f172a',
                    color: '#f1f5f9',
                    fontSize: '14px',
                    outline: 'none',
                    transition: 'border-color 0.2s',
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#6366f1'}
                  onBlur={(e) => e.target.style.borderColor = '#334155'}
                />
              </div>

              {/* 服务商选择 */}
              <div style={{ marginBottom: '20px' }}>
                <label style={{
                  display: 'block',
                  marginBottom: '12px',
                  color: '#f1f5f9',
                  fontSize: '14px',
                  fontWeight: 600,
                }}>
                  AI服务商 *
                </label>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                  gap: '8px',
                }}>
                  {PROVIDER_OPTIONS.map((option) => (
                    <motion.button
                      key={option.value}
                      type="button"
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => handleProviderChange(option.value as typeof provider)}
                      style={{
                        padding: '12px 16px',
                        borderRadius: '8px',
                        border: provider === option.value ? '2px solid #6366f1' : '2px solid #334155',
                        background: provider === option.value ? 'rgba(99, 102, 241, 0.1)' : '#0f172a',
                        color: '#f1f5f9',
                        fontSize: '14px',
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                      }}
                    >
                      <span>{option.icon}</span>
                      <span>{option.label}</span>
                    </motion.button>
                  ))}
                </div>
              </div>

              {/* 模型选择 */}
              <div style={{ marginBottom: '20px' }}>
                <label style={{
                  display: 'block',
                  marginBottom: '8px',
                  color: '#f1f5f9',
                  fontSize: '14px',
                  fontWeight: 600,
                }}>
                  模型名称 *
                </label>
                <select
                  value={modelName}
                  onChange={(e) => setModelName(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    borderRadius: '8px',
                    border: '2px solid #334155',
                    background: '#0f172a',
                    color: '#f1f5f9',
                    fontSize: '14px',
                    outline: 'none',
                  }}
                >
                  {MODEL_PRESETS[provider].map((model) => (
                    <option key={model} value={model}>
                      {model}
                    </option>
                  ))}
                </select>
              </div>

              {/* API Key */}
              <div style={{ marginBottom: '20px' }}>
                <label style={{
                  display: 'block',
                  marginBottom: '8px',
                  color: '#f1f5f9',
                  fontSize: '14px',
                  fontWeight: 600,
                }}>
                  API Key *
                </label>
                <input
                  type="password"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  placeholder="输入API密钥"
                  required
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    borderRadius: '8px',
                    border: '2px solid #334155',
                    background: '#0f172a',
                    color: '#f1f5f9',
                    fontSize: '14px',
                    outline: 'none',
                    fontFamily: 'monospace',
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#6366f1'}
                  onBlur={(e) => e.target.style.borderColor = '#334155'}
                />
              </div>

              {/* 高级设置 */}
              <div style={{ marginBottom: '24px' }}>
                <details style={{
                  background: 'rgba(30, 41, 59, 0.5)',
                  borderRadius: '8px',
                  padding: '16px',
                }}>
                  <summary style={{
                    color: '#f1f5f9',
                    fontSize: '14px',
                    fontWeight: 600,
                    cursor: 'pointer',
                    marginBottom: '12px',
                  }}>
                    高级设置 (可选)
                  </summary>

                  <div style={{ display: 'grid', gap: '12px' }}>
                    {/* Temperature */}
                    <div>
                      <label style={{
                        display: 'block',
                        marginBottom: '4px',
                        color: '#94a3b8',
                        fontSize: '12px',
                      }}>
                        Temperature: {temperature}
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="2"
                        step="0.1"
                        value={temperature}
                        onChange={(e) => setTemperature(parseFloat(e.target.value))}
                        style={{
                          width: '100%',
                          accentColor: '#6366f1',
                        }}
                      />
                    </div>

                    {/* 其他选项 */}
                    <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#94a3b8', fontSize: '12px' }}>
                        <input
                          type="checkbox"
                          checked={stream}
                          onChange={(e) => setStream(e.target.checked)}
                          style={{ accentColor: '#6366f1' }}
                        />
                        流式输出
                      </label>
                      <label style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#94a3b8', fontSize: '12px' }}>
                        <input
                          type="checkbox"
                          checked={enableThinking}
                          onChange={(e) => setEnableThinking(e.target.checked)}
                          style={{ accentColor: '#6366f1' }}
                        />
                        启用思考
                      </label>
                    </div>
                  </div>
                </details>
              </div>

              {/* 按钮 */}
              <div style={{
                display: 'flex',
                gap: '12px',
                justifyContent: 'flex-end',
              }}>
                <motion.button
                  type="button"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={onClose}
                  style={{
                    padding: '12px 24px',
                    borderRadius: '8px',
                    border: '1px solid #475569',
                    background: 'transparent',
                    color: '#94a3b8',
                    fontSize: '14px',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}
                >
                  取消
                </motion.button>
                <motion.button
                  type="submit"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  disabled={!playerName.trim() || !apiKey.trim()}
                  style={{
                    padding: '12px 24px',
                    borderRadius: '8px',
                    border: 'none',
                    background: (!playerName.trim() || !apiKey.trim()) ? '#475569' : 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                    color: '#fff',
                    fontSize: '14px',
                    fontWeight: 600,
                    cursor: (!playerName.trim() || !apiKey.trim()) ? 'not-allowed' : 'pointer',
                    transition: 'all 0.2s',
                  }}
                >
                  添加玩家
                </motion.button>
              </div>
            </form>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};
