import React, { useEffect, useMemo, useRef, useState } from 'react';
import { useModel } from '@umijs/max';
import { Button, Drawer, Space, Tooltip, Typography } from 'antd';
import { CloseOutlined, HistoryOutlined, PlusOutlined } from '@ant-design/icons';
import './parse.less';

/** 原 python-frontend 立项/文件解析页（完整样式） */
const PA_ORIGIN = process.env.PA_PORTAL_ORIGIN || 'http://127.0.0.1:8080';

const ParseEmbed: React.FC = () => {
  const { initialState } = useModel('@@initialState');
  const isSuperAdmin = useMemo(() => {
    const roles = initialState?.currentUser?.roles || [];
    return roles.includes('admin');
  }, [initialState?.currentUser?.roles]);
  const frameRef = useRef<HTMLIFrameElement>(null);
  const chatRef = useRef<HTMLIFrameElement>(null);
  const [aiOpen, setAiOpen] = useState(false);
  const [hint, setHint] = useState(true);
  const [chatKey, setChatKey] = useState(0);

  const postToChat = (type: 'pa-ai-new' | 'pa-ai-history' | 'pa-parse-seed', extra?: Record<string, unknown>) => {
    try {
      chatRef.current?.contentWindow?.postMessage(
        { type, source: 'pa-parse', ...(extra || {}) },
        '*',
      );
    } catch {
      /* ignore */
    }
  };

  const postToProjects = (payload: Record<string, unknown>) => {
    try {
      frameRef.current?.contentWindow?.postMessage({ source: 'pa-parse', ...payload }, '*');
    } catch {
      /* ignore */
    }
  };

  useEffect(() => {
    const onMsg = (ev: MessageEvent) => {
      const data = ev.data;
      if (!data || typeof data !== 'object') return;

      // 立项 iframe：解析完成 → 打开助手并种子注入对话
      if (data.source === 'pa-projects' && data.type === 'pa-parse-to-chat') {
        setAiOpen(true);
        setHint(false);
        const seed = () =>
          postToChat('pa-parse-seed', {
            filename: data.filename,
            method: data.method,
            confidence: data.confidence,
            fields: data.fields,
            gaps: data.gaps,
            warnings: data.warnings,
          });
        // Drawer/iframe 可能尚未就绪，短暂重试
        window.setTimeout(seed, 120);
        window.setTimeout(seed, 480);
        return;
      }

      // 对话 iframe：补全字段 → 回写立项 iframe
      if (data.source === 'pa-chat' && data.type === 'pa-fields-from-chat') {
        postToProjects({ type: 'pa-fields-patch', fields: data.fields || {} });
      }
    };
    window.addEventListener('message', onMsg);
    return () => window.removeEventListener('message', onMsg);
  }, []);

  useEffect(() => {
    const resize = () => {
      const frame = frameRef.current;
      if (!frame) return;
      const h = document.documentElement.clientHeight;
      frame.style.height = `${Math.max(h - 110, 480)}px`;
    };
    resize();
    window.addEventListener('resize', resize);
    return () => window.removeEventListener('resize', resize);
  }, []);

  useEffect(() => {
    if (!hint) return;
    const t = window.setTimeout(() => setHint(false), 5600);
    return () => window.clearTimeout(t);
  }, [hint]);

  useEffect(() => {
    const root = document.querySelector('.ant-pro-page-container') as HTMLElement | null;
    if (root) {
      if (aiOpen) root.classList.add('pa-ai-open');
      else root.classList.remove('pa-ai-open');
    }
    document.body.classList.toggle('pa-parse-ai-open', aiOpen);
    return () => {
      root?.classList.remove('pa-ai-open');
      document.body.classList.remove('pa-parse-ai-open');
    };
  }, [aiOpen]);

  return (
    <div className={`pa-parse-page${aiOpen ? ' pa-parse-page--ai' : ''}`}>
      <div className="pa-parse-main" style={{ margin: '-24px', background: 'transparent' }}>
        <iframe
          ref={frameRef}
          title="文件解析录入"
          src={`${PA_ORIGIN}/projects?embed=1&tab=create&_=${__APP_VERSION__ || 'dev'}`}
          style={{ width: '100%', border: 0, display: 'block', minHeight: 480 }}
          allow="clipboard-read; clipboard-write"
        />
      </div>

      {!aiOpen && (
        <div className="pa-ai-launcher">
          {hint && (
            <div className="pa-ai-hint" role="status">
              {'您好，我是 AI 助手 ～'}
              <button type="button" className="pa-ai-hint-x" onClick={() => setHint(false)} aria-label="close">
                {'×'}
              </button>
            </div>
          )}
          <button
            type="button"
            className="pa-ai-fab"
            title="AI"
            aria-label="open-ai"
            onClick={() => {
              setHint(false);
              setAiOpen(true);
            }}
          >
            <RobotIcon />
          </button>
        </div>
      )}

      <Drawer
        open={aiOpen}
        onClose={() => setAiOpen(false)}
        width={Math.min(440, typeof window !== 'undefined' ? window.innerWidth - 24 : 440)}
        placement="right"
        mask={false}
        destroyOnClose={false}
        rootClassName="pa-ai-drawer"
        styles={{
          body: { padding: 0, display: 'flex', flexDirection: 'column', height: '100%' },
          header: { display: 'none' },
        }}
      >
        <div className="pa-ai-panel-head">
          <Typography.Text strong>{'项目 AI 助手'}</Typography.Text>
          <Space size={2} className="pa-ai-head-actions">
            <Tooltip title="新建对话">
              <Button
                type="text"
                size="small"
                className="pa-ai-icon-btn"
                icon={<PlusOutlined />}
                onClick={() => {
                  postToChat('pa-ai-new');
                  window.setTimeout(() => {
                    if (!chatRef.current?.contentWindow) setChatKey((k) => k + 1);
                  }, 80);
                }}
              />
            </Tooltip>
            <Tooltip title="历史对话">
              <Button
                type="text"
                size="small"
                className="pa-ai-icon-btn"
                icon={<HistoryOutlined />}
                onClick={() => postToChat('pa-ai-history')}
              />
            </Tooltip>
            <Tooltip title="关闭">
              <Button
                type="text"
                size="small"
                className="pa-ai-icon-btn"
                icon={<CloseOutlined />}
                onClick={() => setAiOpen(false)}
              />
            </Tooltip>
          </Space>
        </div>
        <iframe
          key={chatKey}
          ref={chatRef}
          title="chat"
          className="pa-ai-chat-frame"
          src={`${PA_ORIGIN}/chat?embed=1&panel=1&admin=${isSuperAdmin ? '1' : '0'}`}
          allow="clipboard-read; clipboard-write"
        />
        <div className="pa-ai-panel-foot">
          {'内容由 AI 生成，仅供参考，您据此所作判断及操作均由您自行承担责任。'}
        </div>
      </Drawer>
    </div>
  );
};

function RobotIcon() {
  return (
    <svg viewBox="0 0 64 64" width="40" height="40" aria-hidden>
      <circle cx="32" cy="32" r="32" fill="#2563eb" />
      <ellipse cx="32" cy="36" rx="18" ry="15" fill="#fff" />
      <rect x="18" y="28" width="28" height="12" rx="6" fill="#0f172a" />
      <rect x="22" y="31.5" width="20" height="5" rx="2.5" fill="#38bdf8" />
      <circle cx="22" cy="22" r="3.2" fill="#bfdbfe" />
      <circle cx="42" cy="22" r="3.2" fill="#bfdbfe" />
    </svg>
  );
}

export default ParseEmbed;
