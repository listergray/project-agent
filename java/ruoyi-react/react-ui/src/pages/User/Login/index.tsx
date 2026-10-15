import Footer from '@/components/Footer';
import { getCaptchaImg, login, loginGuest } from '@/services/system/auth';
import { getFakeCaptcha } from '@/services/ant-design-pro/login';
import {
  AlipayCircleOutlined,
  LockOutlined,
  MobileOutlined,
  TaobaoCircleOutlined,
  UserOutlined,
  WeiboCircleOutlined,
} from '@ant-design/icons';
import {
  LoginForm,
  ProFormCaptcha,
  ProFormCheckbox,
  ProFormText,
} from '@ant-design/pro-components';
import { createStyles } from 'antd-style';
import { FormattedMessage, history, SelectLang, useIntl, useModel, Helmet } from '@umijs/max';
import { Alert, Button, Col, Row, Tabs, Image, message } from 'antd';
import Settings from '../../../../config/defaultSettings';
import React, { useEffect, useState } from 'react';
import { flushSync } from 'react-dom';
import { clearSessionToken, setSessionToken } from '@/access';
import { getRoutersInfo, setRemoteMenu, getFirstMenuPath } from '@/services/session';

function wantsPortalHome(roles: string[]) {
  return roles.includes('admin') || roles.includes('guest');
}

const useActionStyles = createStyles(({ token }) => ({
  icon: {
    marginLeft: '8px',
    color: 'rgba(0, 0, 0, 0.2)',
    fontSize: '24px',
    verticalAlign: 'middle',
    cursor: 'pointer',
    transition: 'color 0.3s',
    '&:hover': {
      color: token.colorPrimaryActive,
    },
  },
}));

const ActionIcons = () => {
  const { styles } = useActionStyles();
  return (
    <>
      <AlipayCircleOutlined key="AlipayCircleOutlined" className={styles.icon} />
      <TaobaoCircleOutlined key="TaobaoCircleOutlined" className={styles.icon} />
      <WeiboCircleOutlined key="WeiboCircleOutlined" className={styles.icon} />
    </>
  );
};

const useLangStyles = createStyles(({ token }) => ({
  lang: {
    width: 42,
    height: 42,
    lineHeight: '42px',
    position: 'fixed',
    right: 16,
    borderRadius: token.borderRadius,
    ':hover': {
      backgroundColor: token.colorBgTextHover,
    },
  },
}));

const Lang = () => {
  const { styles } = useLangStyles();
  return (
    <div className={styles.lang} data-lang>
      {SelectLang && <SelectLang />}
    </div>
  );
};

const LoginMessage: React.FC<{
  content: string;
}> = ({ content }) => {
  return (
    <Alert
      style={{
        marginBottom: 24,
      }}
      message={content}
      type="error"
      showIcon
    />
  );
};

const Login: React.FC = () => {
  const [userLoginState, setUserLoginState] = useState<API.LoginResult>({code: 200});
  const [type, setType] = useState<string>('account');
  const { initialState, setInitialState } = useModel('@@initialState');
  const [captchaCode, setCaptchaCode] = useState<string>('');
  const [uuid, setUuid] = useState<string>('');

  const { styles: containerStyles } = createStyles(() => ({
    container: {
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      overflow: 'auto',
      backgroundImage:
        "url('https://mdn.alipayobjects.com/yuyan_qk0oxh/afts/img/V-_oS6r-i7wAAAAAAAAAAAAAFl94AQBr')",
      backgroundSize: '100% 100%',
    },
  }))();

  const intl = useIntl();

  const getCaptchaCode = async () => {
    try {
      const response = await getCaptchaImg({}, { skipErrorHandler: true });
      if (!response?.img) {
        message.error('验证码加载失败，请检查若依服务与 Redis（twlmac）');
        return;
      }
      const imgdata = `data:image/png;base64,${response.img}`;
      setCaptchaCode(imgdata);
      setUuid(response.uuid);
    } catch (e) {
      console.error(e);
      message.error('验证码加载失败，请稍后重试');
    }
  };

  const fetchUserInfo = async () => {
    const userInfo = await initialState?.fetchUserInfo?.();
    if (userInfo) {
      flushSync(() => {
        setInitialState((s) => ({
          ...s,
          currentUser: userInfo,
        }));
      });
    }
    return userInfo;
  };

  const afterLoginOk = async (token: string, successMsg: string) => {
    const current = new Date();
    const expireTime = current.setTime(current.getTime() + 1000 * 7 * 24 * 60 * 60);
    setSessionToken(token, token, expireTime);
    message.success(successMsg);
    const userInfo = await fetchUserInfo();
    let home = '/';
    try {
      const menus = await getRoutersInfo();
      setRemoteMenu(menus);
      const roles = (userInfo?.roles || []) as string[];
      home = wantsPortalHome(roles) ? '/portal/home' : getFirstMenuPath(menus) || '/';
    } catch (e) {
      console.error('load routers after login failed', e);
    }
    const urlParams = new URL(window.location.href).searchParams;
    window.location.href = urlParams.get('redirect') || home;
  };

  const handleSubmit = async (values: API.LoginParams) => {
    try {
      const response = await login({ ...values, uuid });
      if (response.code === 200) {
        await afterLoginOk(
          response?.token,
          intl.formatMessage({
            id: 'pages.login.success',
            defaultMessage: '登录成功！',
          }),
        );
        return;
      } else {
        console.log(response.msg);
        clearSessionToken();
        setUserLoginState({ ...response, type });
        getCaptchaCode();
      }
    } catch (error) {
      const defaultLoginFailureMessage = intl.formatMessage({
        id: 'pages.login.failure',
        defaultMessage: '登录失败，请重试！',
      });
      console.log(error);
      message.error(defaultLoginFailureMessage);
    }
  };

  const handleGuestLogin = async () => {
    try {
      const response = await loginGuest();
      if (response.code === 200) {
        await afterLoginOk(response?.token, '\u6e38\u5ba2\u767b\u5f55\u6210\u529f');
        return;
      }
      message.error(response.msg || '\u6e38\u5ba2\u767b\u5f55\u5931\u8d25');
    } catch (error) {
      console.log(error);
      message.error('\u6e38\u5ba2\u767b\u5f55\u5931\u8d25\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5');
    }
  };
  const { code } = userLoginState;
  const loginType = type;

  useEffect(() => {
    getCaptchaCode();
  }, []);

  return (
    <div className={containerStyles.container}>
      <Helmet>
        <title>
          {intl.formatMessage({
            id: 'menu.login',
            defaultMessage: '登录页',
          })}
          - {Settings.title}
        </title>
      </Helmet>
      <Lang />
      <div
        style={{
          flex: '1',
          padding: '32px 0',
        }}
      >
        <LoginForm
          contentStyle={{
            minWidth: 280,
            maxWidth: '75vw',
          }}
          logo={<img alt="logo" src="/brand-assistant.svg" />}
          title="Project Agent"
          subTitle={intl.formatMessage({ id: 'pages.layouts.userLayout.title' })}
          initialValues={{
            autoLogin: true,
          }}
          actions={[
            <FormattedMessage
              key="loginWith"
              id="pages.login.loginWith"
              defaultMessage="其他登录方式"
            />,
            <ActionIcons key="icons" />,
          ]}
          onFinish={async (values) => {
            await handleSubmit(values as API.LoginParams);
          }}
        >
          <Tabs
            activeKey={type}
            onChange={setType}
            centered
            items={[
              {
                key: 'account',
                label: intl.formatMessage({
                  id: 'pages.login.accountLogin.tab',
                  defaultMessage: '账户密码登录',
                }),
              },
              {
                key: 'mobile',
                label: intl.formatMessage({
                  id: 'pages.login.phoneLogin.tab',
                  defaultMessage: '手机号登录',
                }),
              },
            ]}
          />

          {code !== 200 && loginType === 'account' && (
            <LoginMessage
              content={intl.formatMessage({
                id: 'pages.login.accountLogin.errorMessage',
                defaultMessage: '账户或密码错误',
              })}
            />
          )}
          {type === 'account' && (
            <>
              <ProFormText
                name="username"
                initialValue="admin"
                fieldProps={{
                  size: 'large',
                  prefix: <UserOutlined />,
                }}
                placeholder={intl.formatMessage({
                  id: 'pages.login.username.placeholder',
                  defaultMessage: '用户名: admin',
                })}
                rules={[
                  {
                    required: true,
                    message: (
                      <FormattedMessage
                        id="pages.login.username.required"
                        defaultMessage="请输入用户名!"
                      />
                    ),
                  },
                ]}
              />
              <ProFormText.Password
                name="password"
                fieldProps={{
                  size: 'large',
                  prefix: <LockOutlined />,
                  autoComplete: 'new-password',
                }}
                placeholder={intl.formatMessage({
                  id: 'pages.login.password.placeholder',
                  defaultMessage: '请输入密码',
                })}
                rules={[
                  {
                    required: true,
                    message: (
                      <FormattedMessage
                        id="pages.login.password.required"
                        defaultMessage="请输入密码！"
                      />
                    ),
                  },
                ]}
              />
              <Row>
                <Col flex={3}>
                  <ProFormText
                    style={{
                      float: 'right',
                    }}
                    name="code"
                    placeholder={intl.formatMessage({
                      id: 'pages.login.captcha.placeholder',
                      defaultMessage: '请输入验证',
                    })}
                    rules={[
                      {
                        required: true,
                        message: (
                          <FormattedMessage
                            id="pages.searchTable.updateForm.ruleName.nameRules"
                            defaultMessage="请输入验证啊"
                          />
                        ),
                      },
                    ]}
                  />
                </Col>
                <Col flex={2}>
                  <Image
                    src={captchaCode}
                    alt="验证码"
                    style={{
                      display: 'inline-block',
                      verticalAlign: 'top',
                      cursor: 'pointer',
                      paddingLeft: '10px',
                      width: '100px',
                    }}
                    preview={false}
                    onClick={() => getCaptchaCode()}
                  />
                </Col>
              </Row>
            </>
          )}

          {code !== 200 && loginType === 'mobile' && <LoginMessage content="验证码错误" />}
          {type === 'mobile' && (
            <>
              <ProFormText
                fieldProps={{
                  size: 'large',
                  prefix: <MobileOutlined />,
                }}
                name="mobile"
                placeholder={intl.formatMessage({
                  id: 'pages.login.phoneNumber.placeholder',
                  defaultMessage: '手机号',
                })}
                rules={[
                  {
                    required: true,
                    message: (
                      <FormattedMessage
                        id="pages.login.phoneNumber.required"
                        defaultMessage="请输入手机号！"
                      />
                    ),
                  },
                  {
                    pattern: /^1\d{10}$/,
                    message: (
                      <FormattedMessage
                        id="pages.login.phoneNumber.invalid"
                        defaultMessage="手机号格式错误！"
                      />
                    ),
                  },
                ]}
              />
              <ProFormCaptcha
                fieldProps={{
                  size: 'large',
                  prefix: <LockOutlined />,
                }}
                captchaProps={{
                  size: 'large',
                }}
                placeholder={intl.formatMessage({
                  id: 'pages.login.captcha.placeholder',
                  defaultMessage: '请输入验证码',
                })}
                captchaTextRender={(timing, count) => {
                  if (timing) {
                    return `${count} ${intl.formatMessage({
                      id: 'pages.getCaptchaSecondText',
                      defaultMessage: '获取验证码',
                    })}`;
                  }
                  return intl.formatMessage({
                    id: 'pages.login.phoneLogin.getVerificationCode',
                    defaultMessage: '获取验证码',
                  });
                }}
                name="captcha"
                rules={[
                  {
                    required: true,
                    message: (
                      <FormattedMessage
                        id="pages.login.captcha.required"
                        defaultMessage="请输入验证码！"
                      />
                    ),
                  },
                ]}
                onGetCaptcha={async (phone) => {
                  const result = await getFakeCaptcha({
                    phone,
                  });
                  if (!result) {
                    return;
                  }
                  message.success('获取验证码成功！验证码为：1234');
                }}
              />
            </>
          )}
          <div
            style={{
              marginBottom: 24,
            }}
          >
            <ProFormCheckbox noStyle name="autoLogin">
              <FormattedMessage id="pages.login.rememberMe" defaultMessage="自动登录" />
            </ProFormCheckbox>
            <a
              style={{
                float: 'right',
              }}
            >
              <FormattedMessage id="pages.login.forgotPassword" defaultMessage="忘记密码" />
            </a>
          </div>
        </LoginForm>
        <div style={{ maxWidth: 328, margin: '0 auto', padding: '0 0 24px' }}>
          <Button block size="large" onClick={handleGuestLogin}>
            {'\u6e38\u5ba2\u767b\u5f55'}
          </Button>
          <div style={{ marginTop: 8, color: '#94a3b8', fontSize: 12, textAlign: 'center' }}>
            {'\u65e0\u9700\u8d26\u53f7\uff0c\u4ec5\u53ef\u6d4f\u89c8\u9879\u76ee\u7ba1\u7406\u6a21\u5757'}
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default Login;
