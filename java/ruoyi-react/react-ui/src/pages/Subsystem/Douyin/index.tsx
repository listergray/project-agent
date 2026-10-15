import React, { useEffect, useRef } from 'react';
import { Button, Space, Typography } from 'antd';
import { ArrowLeftOutlined, ExportOutlined } from '@ant-design/icons';
import { history, useModel } from '@umijs/max';
import { PageEnum } from '@/enums/pagesEnums';
import { getAccessToken } from '@/access';

function getAccessTokenSafe() {
  try {
    return !!getAccessToken();
  } catch {
    return false;
  }
}

const DOUYIN_ORIGIN = process.env.DOUYIN_PORTAL_ORIGIN || 'http://127.0.0.1:12500';
const TOOLBAR_H = 48;

const DouyinEmbed: React.FC = () => {
  const frameRef = useRef<HTMLIFrameElement>(null);
  const { initialState } = useModel('@@initialState');

  useEffect(() => {
    if (!initialState) return;
    if (!initialState.currentUser && !getAccessTokenSafe()) {
      history.replace(PageEnum.LOGIN);
    }
  }, [initialState]);

  useEffect(() => {
    const resize = () => {
      const frame = frameRef.current;
      if (!frame) return;
      frame.style.height = `${Math.max(window.innerHeight - TOOLBAR_H, 480)}px`;
    };
    resize();
    window.addEventListener('resize', resize);
    return () => window.removeEventListener('resize', resize);
  }, []);

  return (
    <div style={{ height: '100vh', overflow: 'hidden', background: '#0f172a' }}>
      <div
        style={{
          height: TOOLBAR_H,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 16px',
          borderBottom: '1px solid rgba(148,163,184,0.2)',
          background: '#111827',
        }}
      >
        <Space>
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            style={{ color: '#e2e8f0' }}
            onClick={() => window.location.assign('/portal/home')}
          >
            {'\u5b50\u7cfb\u7edf\u4e2d\u5fc3'}
          </Button>
          <img src="/brand-douyin.svg" alt="" width={22} height={22} style={{ borderRadius: 5 }} />
          <Typography.Text style={{ color: '#94a3b8' }}>
            {'\u6296\u97f3\u76ee\u5f55\u53d1\u89c6\u9891'}
          </Typography.Text>
        </Space>
        <Button type="link" icon={<ExportOutlined />} href={DOUYIN_ORIGIN} target="_blank" rel="noreferrer">
          {'\u65b0\u7a97\u53e3\u6253\u5f00'}
        </Button>
      </div>
      <iframe
        ref={frameRef}
        title={'\u6296\u97f3\u76ee\u5f55\u53d1\u89c6\u9891'}
        src={`${DOUYIN_ORIGIN}/`}
        style={{ width: '100%', border: 0, display: 'block', background: '#0f1419' }}
        allow="clipboard-read; clipboard-write"
      />
    </div>
  );
};

export default DouyinEmbed;
