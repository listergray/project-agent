import React, { useMemo } from 'react';
import { useModel, history } from '@umijs/max';
import { Button, Card, Col, Row, Space, Typography } from 'antd';
import { ApartmentOutlined, LogoutOutlined } from '@ant-design/icons';
import { clearSessionToken } from '@/access';
import { PageEnum } from '@/enums/pagesEnums';
import { setRemoteMenu } from '@/services/session';

const { Title, Paragraph, Text } = Typography;

type SubsystemCard = {
  key: string;
  title: string;
  desc: string;
  iconSrc: string;
  path: string;
  accent: string;
  roles?: string[];
};

const SUBSYSTEMS: SubsystemCard[] = [
  {
    key: 'project',
    title: '\u9879\u76ee\u7ba1\u7406 Agent',
    desc: '\u667a\u80fd\u5bf9\u8bdd\u3001\u6587\u4ef6\u89e3\u6790\u5f55\u5165\u3001\u7acb\u9879\u4e0e\u5ba1\u6279\u5de5\u4f5c\u6d41',
    iconSrc: '/brand-mark.svg',
    path: '/project/chat',
    accent: '#1677ff',
    // admin / guest / project_admin ??
    roles: ['admin', 'guest', 'project_admin'],
  },
  {
    key: 'xianyu',
    title: '\u95f2\u9c7c\u81ea\u52a8\u53d1\u8d27',
    desc: '\u591a\u8d26\u53f7\u7ba1\u7406\u3001\u81ea\u52a8\u53d1\u8d27\u3001\u5e93\u5b58\u4e0e AI \u667a\u80fd\u56de\u590d',
    iconSrc: '/brand-xianyu.svg',
    path: '/subsystem/xianyu',
    accent: '#fa8c16',
    roles: ['admin'],
  },
  {
    key: 'douyin',
    title: '\u6296\u97f3\u76ee\u5f55\u53d1\u89c6\u9891',
    desc: '\u626b\u63cf\u76ee\u5f55 mp4\u3001\u626b\u7801\u767b\u5f55\u521b\u4f5c\u8005\u4e2d\u5fc3\u5e76\u4e00\u952e\u53d1\u5e03',
    iconSrc: '/brand-douyin.svg',
    path: '/subsystem/douyin',
    accent: '#fe2c55',
    roles: ['admin'],
  },
  {
    key: 'myhome',
    title: '\u6211\u7684\u6240\u6709',
    desc: '\u8d44\u4ea7\u3001\u5c0f\u5c45\u3001\u5f85\u529e\u4e0e\u8d26\u672c\uff1b\u4e2a\u4eba\u751f\u6d3b\u4e0e\u623f\u5c4b\u7ba1\u7406',
    iconSrc: '/brand-myhome.svg',
    path: '/subsystem/myhome',
    accent: '#9a3b32',
    roles: ['admin'],
  },
  {
    key: 'system',
    title: '\u52a9\u624b\u7cfb\u7edf',
    desc: '\u7528\u6237\u3001\u89d2\u8272\u3001\u83dc\u5355\u3001\u5b57\u5178\u4e0e\u76d1\u63a7\u5de5\u5177',
    iconSrc: '/brand-assistant.svg',
    path: '/system/user',
    accent: '#0f766e',
    roles: ['admin'],
  },
];

const PortalHome: React.FC = () => {
  const { initialState, setInitialState } = useModel('@@initialState');
  const roleKeys = useMemo(() => {
    const raw = initialState?.currentUser?.roles || [];
    return (raw as any[])
      .map((r) => (typeof r === 'string' ? r : r?.roleKey || r?.role_key))
      .filter(Boolean) as string[];
  }, [initialState?.currentUser?.roles]);
  const nick =
    initialState?.currentUser?.nickName ||
    initialState?.currentUser?.userName ||
    '\u7528\u6237';

  const cards = useMemo(() => {
    return SUBSYSTEMS.filter((s) => {
      if (!s.roles?.length) return true;
      return s.roles.some((r) => roleKeys.includes(r));
    });
  }, [roleKeys]);

  const enter = (path: string) => {
    window.location.assign(path);
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
              <img src="/brand-assistant.svg" alt="" width={32} height={32} style={{ borderRadius: 8 }} />
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
                styles={{ body: { padding: 28, minHeight: 220 } }}
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
                    marginBottom: 20,
                    overflow: 'hidden',
                  }}
                >
                  <img src={item.iconSrc} alt="" width={64} height={64} style={{ display: 'block' }} />
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
