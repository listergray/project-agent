import React, { useMemo } from 'react';
import { useModel, history } from '@umijs/max';
import { Button, Col, Row, Space, Typography, message } from 'antd';
import { ArrowUpOutlined, LogoutOutlined } from '@ant-design/icons';
import { clearSessionToken } from '@/access';
import { PageEnum } from '@/enums/pagesEnums';
import { setRemoteMenu } from '@/services/session';
import { xuzao } from '@/theme/xuzao';

const { Title, Paragraph, Text } = Typography;

type SubsystemCard = {
  key: string;
  title: string;
  desc: string;
  iconSrc: string;
  path: string;
  /** 可进入的角色；未配置则所有人可进。卡片始终展示，无权限点击时提示。 */
  roles?: string[];
};

const SUBSYSTEMS: SubsystemCard[] = [
  {
    key: 'project',
    title: '\u9879\u76ee\u7ba1\u7406 Agent',
    desc: '\u667a\u80fd\u5bf9\u8bdd\u3001\u6587\u4ef6\u89e3\u6790\u5f55\u5165\u3001\u7acb\u9879\u4e0e\u5ba1\u6279\u5de5\u4f5c\u6d41',
    iconSrc: '/brand-mark.svg',
    path: '/project/chat',
    roles: ['admin', 'guest', 'project_admin'],
  },
  {
    key: 'xianyu',
    title: '\u95f2\u9c7c\u81ea\u52a8\u53d1\u8d27',
    desc: '\u591a\u8d26\u53f7\u7ba1\u7406\u3001\u81ea\u52a8\u53d1\u8d27\u3001\u5e93\u5b58\u4e0e AI \u667a\u80fd\u56de\u590d',
    iconSrc: '/brand-xianyu.svg',
    path: '/subsystem/xianyu',
    roles: ['admin'],
  },
  {
    key: 'douyin',
    title: '\u6296\u97f3\u76ee\u5f55\u53d1\u89c6\u9891',
    desc: '\u626b\u63cf\u76ee\u5f55 mp4\u3001\u626b\u7801\u767b\u5f55\u521b\u4f5c\u8005\u4e2d\u5fc3\u5e76\u4e00\u952e\u53d1\u5e03',
    iconSrc: '/brand-douyin.svg',
    path: '/subsystem/douyin',
    roles: ['admin'],
  },
  {
    key: 'myhome',
    title: '\u4eba\u751f\u6307\u5357',
    desc: '\u8d44\u4ea7\u3001\u5c0f\u5c45\u3001\u5f85\u529e\u4e0e\u8d26\u672c\uff1b\u4e2a\u4eba\u751f\u6d3b\u4e0e\u623f\u5c4b\u7ba1\u7406',
    iconSrc: '/brand-myhome.svg',
    path: '/subsystem/myhome',
    roles: ['admin'],
  },
  {
    key: 'system',
    title: '\u52a9\u624b\u7cfb\u7edf',
    desc: '\u7528\u6237\u3001\u89d2\u8272\u3001\u83dc\u5355\u3001\u5b57\u5178\u4e0e\u76d1\u63a7\u5de5\u5177',
    iconSrc: '/brand-assistant.svg',
    path: '/system/user',
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
  const isGuest = roleKeys.includes('guest');
  const nick =
    initialState?.currentUser?.nickName ||
    initialState?.currentUser?.userName ||
    '\u7528\u6237';

  const canEnter = (item: SubsystemCard) => {
    if (!item.roles?.length) return true;
    return item.roles.some((r) => roleKeys.includes(r));
  };

  const enter = (item: SubsystemCard) => {
    if (!canEnter(item)) {
      message.warning(
        isGuest
          ? '\u6e38\u5ba2\u8eab\u4efd\u65e0\u6743\u9650\uff0c\u8bf7\u4f7f\u7528\u6388\u6743\u8d26\u53f7\u767b\u5f55'
          : '\u5f53\u524d\u8d26\u53f7\u65e0\u6743\u9650\u8bbf\u95ee\u8be5\u5b50\u7cfb\u7edf',
      );
      return;
    }
    window.location.assign(item.path);
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
        background: xuzao.paper,
        color: xuzao.ink,
        fontFamily: xuzao.sans,
        padding: 'clamp(28px, 4vh, 48px) clamp(20px, 4vw, 40px) 64px',
      }}
    >
      <div style={{ maxWidth: 1080, margin: '0 auto' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            marginBottom: 48,
            gap: 16,
            flexWrap: 'wrap',
          }}
        >
          <div>
            <Space align="center" size={12} style={{ marginBottom: 12 }}>
              <img src="/brand-assistant.svg" alt="" width={28} height={28} style={{ borderRadius: xuzao.radius }} />
              <Text
                style={{
                  color: xuzao.muted,
                  letterSpacing: 2,
                  fontSize: 12,
                  textTransform: 'uppercase',
                }}
              >
                PROJECT AGENT PLATFORM
              </Text>
            </Space>
            <Title
              level={2}
              style={{
                color: xuzao.ink,
                margin: '0 0 10px',
                fontWeight: 700,
                letterSpacing: '-0.02em',
              }}
            >
              {'\u5b50\u7cfb\u7edf\u4e2d\u5fc3'}
            </Title>
            <Paragraph style={{ color: xuzao.muted, margin: 0, fontSize: 16, lineHeight: 1.6 }}>
              {'\u4f60\u597d\uff0c'}
              {nick}
              {'\u3002\u9009\u62e9\u4e0b\u65b9\u5b50\u7cfb\u7edf\u8fdb\u5165\u5bf9\u5e94\u4e1a\u52a1\u7cfb\u7edf\u3002'}
            </Paragraph>
          </div>
          <Button
            icon={<LogoutOutlined />}
            onClick={logout}
            style={{
              background: xuzao.ink,
              borderColor: xuzao.ink,
              color: xuzao.white,
              borderRadius: xuzao.radius,
              height: 40,
            }}
          >
            {'\u9000\u51fa\u767b\u5f55'}
          </Button>
        </div>

        <Row gutter={[20, 20]}>
          {SUBSYSTEMS.map((item, index) => {
            const allowed = canEnter(item);
            return (
              <Col xs={24} sm={12} lg={8} key={item.key}>
                <div
                  role="button"
                  tabIndex={0}
                  onClick={() => enter(item)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      enter(item);
                    }
                  }}
                  style={{
                    height: '100%',
                    minHeight: 240,
                    padding: 28,
                    background: xuzao.white,
                    border: `1px solid ${xuzao.line}`,
                    borderRadius: xuzao.radius,
                    cursor: 'pointer',
                    opacity: allowed ? 1 : 0.72,
                    display: 'flex',
                    flexDirection: 'column',
                    transition: 'border-color 0.2s, box-shadow 0.2s',
                    boxShadow: 'none',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = xuzao.ink;
                    e.currentTarget.style.boxShadow = '0 8px 24px rgba(28,33,29,0.06)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = xuzao.line;
                    e.currentTarget.style.boxShadow = 'none';
                  }}
                >
                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start',
                      marginBottom: 20,
                    }}
                  >
                    <div
                      style={{
                        width: 56,
                        height: 56,
                        borderRadius: xuzao.radius,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        overflow: 'hidden',
                        border: `1px solid ${xuzao.line}`,
                      }}
                    >
                      <img
                        src={item.iconSrc}
                        alt=""
                        width={56}
                        height={56}
                        style={{ display: 'block', borderRadius: xuzao.radius }}
                      />
                    </div>
                    <Text style={{ color: xuzao.muted, fontSize: 12, letterSpacing: 1 }}>
                      {String(index + 1).padStart(2, '0')}
                    </Text>
                  </div>
                  <Title level={4} style={{ color: xuzao.ink, margin: '0 0 8px', fontWeight: 700 }}>
                    {item.title}
                  </Title>
                  <Paragraph style={{ color: xuzao.muted, minHeight: 48, flex: 1, marginBottom: 20 }}>
                    {item.desc}
                  </Paragraph>
                  <div
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      background: allowed ? xuzao.ink : xuzao.muted,
                      color: xuzao.white,
                      borderRadius: xuzao.radius,
                      padding: '10px 14px',
                      fontSize: 14,
                      fontWeight: 600,
                    }}
                  >
                    <span>{allowed ? '\u8fdb\u5165\u7cfb\u7edf' : '\u65e0\u6743\u9650'}</span>
                    <span
                      style={{
                        width: 28,
                        height: 28,
                        borderRadius: xuzao.radius,
                        background: allowed ? xuzao.lime : xuzao.line,
                        color: xuzao.ink,
                        display: 'inline-flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}
                    >
                      <ArrowUpOutlined style={{ transform: 'rotate(45deg)', fontSize: 12 }} />
                    </span>
                  </div>
                </div>
              </Col>
            );
          })}
        </Row>

        <div
          style={{
            marginTop: 48,
            paddingTop: 20,
            borderTop: `1px solid ${xuzao.line}`,
            color: xuzao.muted,
            fontSize: 13,
            textAlign: 'center',
          }}
        >
          {'\u8ba9\u4e1a\u52a1\u60f3\u6cd5\uff0c\u6210\u4e3a\u597d\u7528\u7684\u4ea7\u54c1\u3002'}
        </div>
      </div>
    </div>
  );
};

export default PortalHome;
