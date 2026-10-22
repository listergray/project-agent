import React, { useEffect, useRef } from 'react';
import { Button, Space, Typography } from 'antd';
import { ArrowLeftOutlined, ExportOutlined } from '@ant-design/icons';
import { xuzao } from '@/theme/xuzao';

const TOOLBAR_H = 48;

type Props = {
  title: string;
  iconSrc: string;
  iframeSrc: string;
  iframeTitle?: string;
  openOrigin: string;
};

/** ??? iframe ????? paper / ink ?? */
const SubsystemChrome: React.FC<Props> = ({
  title,
  iconSrc,
  iframeSrc,
  iframeTitle,
  openOrigin,
}) => {
  const frameRef = useRef<HTMLIFrameElement>(null);

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
    <div style={{ height: '100vh', overflow: 'hidden', background: xuzao.paper, fontFamily: xuzao.sans }}>
      <div
        style={{
          height: TOOLBAR_H,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 16px',
          borderBottom: `1px solid ${xuzao.line}`,
          background: xuzao.paper,
        }}
      >
        <Space>
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            style={{ color: xuzao.ink }}
            onClick={() => window.location.assign('/portal/home')}
          >
            {'\u5b50\u7cfb\u7edf\u4e2d\u5fc3'}
          </Button>
          <img src={iconSrc} alt="" width={22} height={22} style={{ borderRadius: xuzao.radius }} />
          <Typography.Text style={{ color: xuzao.muted }}>{title}</Typography.Text>
        </Space>
        <Button
          type="link"
          icon={<ExportOutlined />}
          href={openOrigin}
          target="_blank"
          rel="noreferrer"
          style={{ color: xuzao.ink }}
        >
          {'\u65b0\u7a97\u53e3\u6253\u5f00'}
        </Button>
      </div>
      <iframe
        ref={frameRef}
        title={iframeTitle || title}
        src={iframeSrc}
        style={{ width: '100%', border: 0, display: 'block', background: xuzao.white }}
        allow="clipboard-read; clipboard-write"
      />
    </div>
  );
};

export default SubsystemChrome;
