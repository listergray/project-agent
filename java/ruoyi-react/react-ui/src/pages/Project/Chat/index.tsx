import React, { useEffect, useMemo, useRef } from 'react';
import { useModel } from '@umijs/max';
import { resolveAgentOrigin } from '@/utils/subsystemOrigin';

/** 原 python-frontend 智能对话页（完整样式） */
const ChatEmbed: React.FC = () => {
  const origin = useMemo(() => resolveAgentOrigin(), []);
  const { initialState } = useModel('@@initialState');
  const isSuperAdmin = useMemo(() => {
    const roles = initialState?.currentUser?.roles || [];
    return roles.includes('admin');
  }, [initialState?.currentUser?.roles]);
  const frameRef = useRef<HTMLIFrameElement>(null);

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

  return (
    <div style={{ margin: '-24px', background: 'transparent' }}>
      <iframe
        ref={frameRef}
        title="智能对话"
        src={`${origin}/chat?admin=${isSuperAdmin ? '1' : '0'}`}
        style={{ width: '100%', border: 0, display: 'block', minHeight: 480 }}
        allow="clipboard-read; clipboard-write"
      />
    </div>
  );
};

export default ChatEmbed;
