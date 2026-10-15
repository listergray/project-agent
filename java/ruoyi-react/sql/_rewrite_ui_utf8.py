# -*- coding: utf-8 -*-
from pathlib import Path

def w(path: str, text: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    print("wrote", p, "bytes", p.stat().st_size)

portal = """import React, { useMemo } from 'react';
import { history, useModel } from '@umijs/max';
import { Button, Card, Col, Row, Space, Typography } from 'antd';
import {
  ApartmentOutlined,
  MessageOutlined,
  SettingOutlined,
  ShopOutlined,
  LogoutOutlined,
} from '@ant-design/icons';
import { clearSessionToken } from '@/access';
import { PageEnum } from '@/enums/pagesEnums';
import { setRemoteMenu } from '@/services/session';

const { Title, Paragraph, Text } = Typography;

type SubsystemCard = {
  key: string;
  title: string;
  desc: string;
  icon: React.ReactNode;
  path: string;
  accent: string;
  roles?: string[];
};

const SUBSYSTEMS: SubsystemCard[] = [
  {
    key: 'project',
    title: '\u9879\u76ee\u7ba1\u7406 Agent',
    desc: '\u667a\u80fd\u5bf9\u8bdd\u3001\u6587\u4ef6\u89e3\u6790\u5f55\u5165\u3001\u7acb\u9879\u4e0e\u5ba1\u6279\u5de5\u4f5c\u6d41',
    icon: <MessageOutlined style={{ fontSize: 36 }} />,
    path: '/project/chat',
    accent: '#1677ff',
  },
  {
    key: 'xianyu',
    title: '\u95f2\u9c7c\u81ea\u52a8\u53d1\u8d27',
    desc: '\u591a\u8d26\u53f7\u7ba1\u7406\u3001\u81ea\u52a8\u53d1\u8d27\u3001\u5e93\u5b58\u4e0e AI \u667a\u80fd\u56de\u590d',
    icon: <ShopOutlined style={{ fontSize: 36 }} />,
    path: '/subsystem/xianyu',
    accent: '#fa8c16',
    roles: ['admin'],
  },
  {
    key: 'system',
    title: '\u7cfb\u7edf\u7ba1\u7406',
    desc: '\u7528\u6237\u3001\u89d2\u8272\u3001\u83dc\u5355\u3001\u5b57\u5178\u4e0e\u76d1\u63a7\u5de5\u5177',
    icon: <SettingOutlined style={{ fontSize: 36 }} />,
    path: '/system/user',
    accent: '#52c41a',
    roles: ['admin'],
  },
];

const PortalHome: React.FC = () => {
  const { initialState, setInitialState } = useModel('@@initialState');
  const roles = (initialState?.currentUser?.roles || []) as string[];
  const nick =
    initialState?.currentUser?.nickName ||
    initialState?.currentUser?.userName ||
    '\u7528\u6237';

  const cards = useMemo(() => {
    return SUBSYSTEMS.filter((s) => {
      if (!s.roles?.length) return true;
      return s.roles.some((r) => roles.includes(r));
    });
  }, [roles]);

  const enter = (path: string) => {
    history.push(path);
  };

  const logout = async () => {
    clearSessionToken();
    setRemoteMenu(undefined);
    await setInitialState((s) => ({ ...s, currentUser: undefined }));
    history.replace(PageEnum.LOGIN);
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'linear-gradient(160deg, #0f172a 0%, #1e293b 45%, #0f172a 100%)',
        padding: '48px 24px 64px',
      }}
    >
      <div style={{ maxWidth: 1080, margin: '0 auto' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            marginBottom: 40,
            gap: 16,
            flexWrap: 'wrap',
          }}
        >
          <div>
            <Space align="center" size={12} style={{ marginBottom: 8 }}>
              <ApartmentOutlined style={{ fontSize: 28, color: '#93c5fd' }} />
              <Text style={{ color: '#93c5fd', letterSpacing: 2 }}>PROJECT AGENT PLATFORM</Text>
            </Space>
            <Title level={2} style={{ color: '#f8fafc', margin: '0 0 8px' }}>
              {'\u5b50\u7cfb\u7edf\u4e2d\u5fc3'}
            </Title>
            <Paragraph style={{ color: '#94a3b8', margin: 0, fontSize: 16 }}>
              {'\u4f60\u597d\uff0c'}
              {nick}
              {'\u3002\u9009\u62e9\u4e0b\u65b9\u5b50\u7cfb\u7edf\u8fdb\u5165\u5bf9\u5e94\u4e1a\u52a1\u7cfb\u7edf\u3002'}
            </Paragraph>
          </div>
          <Button icon={<LogoutOutlined />} onClick={logout}>
            {'\u9000\u51fa\u767b\u5f55'}
          </Button>
        </div>

        <Row gutter={[20, 20]}>
          {cards.map((item) => (
            <Col xs={24} sm={12} lg={8} key={item.key}>
              <Card
                hoverable
                onClick={() => enter(item.path)}
                styles={{
                  body: { padding: 28, minHeight: 220 },
                }}
                style={{
                  borderRadius: 16,
                  border: '1px solid rgba(148,163,184,0.25)',
                  background: 'rgba(15,23,42,0.65)',
                  backdropFilter: 'blur(8px)',
                  height: '100%',
                }}
              >
                <div
                  style={{
                    width: 64,
                    height: 64,
                    borderRadius: 16,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: `${item.accent}22`,
                    color: item.accent,
                    marginBottom: 20,
                  }}
                >
                  {item.icon}
                </div>
                <Title level={4} style={{ color: '#f1f5f9', marginTop: 0 }}>
                  {item.title}
                </Title>
                <Paragraph style={{ color: '#94a3b8', minHeight: 48 }}>{item.desc}</Paragraph>
                <Button type="primary" style={{ background: item.accent, borderColor: item.accent }}>
                  {'\u8fdb\u5165\u7cfb\u7edf'}
                </Button>
              </Card>
            </Col>
          ))}
        </Row>
      </div>
    </div>
  );
};

export default PortalHome;
"""

xianyu = """import React, { useEffect, useRef } from 'react';
import { Button, Space, Typography } from 'antd';
import { ArrowLeftOutlined, ExportOutlined } from '@ant-design/icons';
import { history } from '@umijs/max';

/** xianyu-auto subsystem (Spring Boot + Vue, default :12400) */
const XIANYU_ORIGIN = process.env.XIANYU_PORTAL_ORIGIN || 'http://127.0.0.1:12400';

const XianyuEmbed: React.FC = () => {
  const frameRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    const resize = () => {
      const frame = frameRef.current;
      if (!frame) return;
      const h = document.documentElement.clientHeight;
      frame.style.height = `${Math.max(h - 56, 480)}px`;
    };
    resize();
    window.addEventListener('resize', resize);
    return () => window.removeEventListener('resize', resize);
  }, []);

  return (
    <div style={{ margin: '-24px', background: '#0f172a' }}>
      <div
        style={{
          height: 48,
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
            onClick={() => history.push('/portal/home')}
          >
            {'\u5b50\u7cfb\u7edf\u4e2d\u5fc3'}
          </Button>
          <Typography.Text style={{ color: '#94a3b8' }}>
            {'\u95f2\u9c7c\u81ea\u52a8\u53d1\u8d27'}
          </Typography.Text>
        </Space>
        <Button
          type="link"
          icon={<ExportOutlined />}
          href={XIANYU_ORIGIN}
          target="_blank"
          rel="noreferrer"
        >
          {'\u65b0\u7a97\u53e3\u6253\u5f00'}
        </Button>
      </div>
      <iframe
        ref={frameRef}
        title={'\u95f2\u9c7c\u81ea\u52a8\u53d1\u8d27'}
        src={`${XIANYU_ORIGIN}/`}
        style={{ width: '100%', border: 0, display: 'block', minHeight: 480, background: '#fff' }}
        allow="clipboard-read; clipboard-write"
      />
    </div>
  );
};

export default XianyuEmbed;
"""

integration = """# Integration into project_agent

Migrated from `E:\\\\java\\\\xianyu-auto` as an independent subsystem under RuoYi.

## Infra (twlmac)

| Item | Value |
|---|---|
| MySQL | `twlmac:3306` / db `xx_erp` / root / root123456 |
| Port | `12400` |
| Config | `.env` (do not commit secrets) |

Do not start local Docker DB; use twlmac like the rest of project_agent.

## Start

```powershell
cd E:\\\\ai-pro\\\\project_agent\\\\java\\\\xianyu-auto
mvn spring-boot:run "-Dfrontend.phase=none"
```

Or package with frontend static assets:

```powershell
mvn clean package -DskipTests
java -jar target/xianyu-auto-1.0.0-SNAPSHOT.jar
```

First boot creates `xx_erp` and runs `schema.sql`.

## RuoYi entry

1. admin login -> `/portal/home`
2. click xianyu card -> `/subsystem/xianyu` (iframe -> `http://127.0.0.1:12400`)
3. xianyu own login: `admin` / `admin123`

Override iframe origin with `XIANYU_PORTAL_ORIGIN` at react-ui build time.
"""

w(r"E:\ai-pro\project_agent\java\ruoyi-react\react-ui\src\pages\Portal\Home\index.tsx", portal)
w(r"E:\ai-pro\project_agent\java\ruoyi-react\react-ui\src\pages\Subsystem\Xianyu\index.tsx", xianyu)
w(r"E:\ai-pro\project_agent\java\xianyu-auto\INTEGRATION.md", integration)

# fix AvatarDropdown label if corrupted
avatar = Path(r"E:\ai-pro\project_agent\java\ruoyi-react\react-ui\src\components\RightContent\AvatarDropdown.tsx")
text = avatar.read_text(encoding="utf-8")
text2 = text.replace("label: '?????'", "label: '\u5b50\u7cfb\u7edf\u4e2d\u5fc3'")
text2 = text2.replace("label: '子系统中心'", "label: '\u5b50\u7cfb\u7edf\u4e2d\u5fc3'")
if "子系统中心" not in text2 and "\\u5b50\\u7cfb\\u7edf\\u4e2d\\u5fc3" not in text2 and "\u5b50\u7cfb\u7edf\u4e2d\u5fc3" not in text2:
    # try find portal key block
    if "key: 'portal'" in text2:
        import re
        text2 = re.sub(
            r"(key: 'portal',\s*icon: <AppstoreOutlined />,\s*label: ')([^']*)(')",
            r"\1\u5b50\u7cfb\u7edf\u4e2d\u5fc3\3",
            text2,
        )
avatar.write_text(text2, encoding="utf-8")
print("avatar portal label ok")
print("sample portal title bytes:", "\u5b50\u7cfb\u7edf\u4e2d\u5fc3".encode("utf-8"))