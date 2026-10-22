import { getCaptchaImg, login, loginGuest } from '@/services/system/auth';
import { getFakeCaptcha } from '@/services/ant-design-pro/login';
import { LockOutlined, MobileOutlined, UserOutlined } from '@ant-design/icons';
import {
  LoginForm,
  ProFormCaptcha,
  ProFormCheckbox,
  ProFormText,
} from '@ant-design/pro-components';
import { createStyles } from 'antd-style';
import { FormattedMessage, SelectLang, useIntl, useModel, Helmet } from '@umijs/max';
import { Alert, Button, Tabs, message } from 'antd';
import Settings from '../../../../config/defaultSettings';
import React, { useEffect, useState } from 'react';
import { flushSync } from 'react-dom';
import { clearSessionToken, setSessionToken } from '@/access';
import { getRoutersInfo, setRemoteMenu, getFirstMenuPath } from '@/services/session';

function wantsPortalHome(roles: string[]) {
  return roles.includes('admin') || roles.includes('guest');
}

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
      overflow: 'hidden',
      background: '#f4f3ed',
      color: '#1c211d',
      fontFamily: '"PingFang SC","Microsoft YaHei","Noto Sans CJK SC",Arial,sans-serif',
      '.ant-pro-form-login-container': {
        background: 'transparent !important',
        height: 'auto !important',
        padding: '0 !important',
        minHeight: '0 !important',
      },
      '.ant-pro-form-login-main': {
        background: '#ffffff',
        border: '1px solid #d5d7cd',
        borderRadius: 4,
        padding: '16px 20px 4px',
        boxShadow: '0 8px 28px rgba(28,33,29,0.06)',
        width: '100% !important',
        maxWidth: 360,
        margin: '0 auto',
      },
      '.ant-pro-form-login-header': {
        marginBottom: 4,
      },
      '.ant-pro-form-login-logo img': {
        width: 40,
        height: 40,
      },
      '.ant-pro-form-login-title': {
        fontSize: 24,
        lineHeight: 1.25,
        color: '#1c211d',
      },
      '.ant-pro-form-login-desc': {
        color: '#646960 !important',
        marginBottom: 8,
        fontSize: 13,
      },
      '.ant-tabs': {
        marginBottom: 4,
      },
      '.ant-tabs-nav': {
        marginBottom: 8,
      },
      '.ant-form-item': {
        marginBottom: 14,
      },
      '.ant-btn-primary': {
        background: '#1c211d !important',
        borderColor: '#1c211d !important',
        borderRadius: 4,
      },
      '.ant-btn-primary:hover': {
        background: '#2a322c !important',
        borderColor: '#2a322c !important',
      },
      '.ant-tabs-ink-bar': {
        background: '#1c211d',
      },
      '.ant-tabs-tab.ant-tabs-tab-active .ant-tabs-tab-btn': {
        color: '#1c211d',
      },
      '.ant-input-affix-wrapper, .ant-input': {
        borderRadius: 4,
        borderColor: '#d5d7cd',
      },
      '.captcha-row': {
        display: 'flex',
        alignItems: 'flex-start',
        gap: 8,
        width: '100%',
      },
      '.captcha-row .captcha-input': {
        flex: 1,
        minWidth: 0,
      },
      '.captcha-row .captcha-input .ant-form-item': {
        marginBottom: 14,
      },
      '.captcha-row .captcha-img': {
        flex: '0 0 auto',
        height: 40,
        marginTop: 0,
        marginBottom: 14,
        border: '1px solid #d5d7cd',
        borderRadius: 4,
        cursor: 'pointer',
        overflow: 'hidden',
        background: '#fff',
      },
      '.captcha-row .captcha-img img': {
        display: 'block',
        height: 38,
        width: 110,
        objectFit: 'cover',
      },
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
          flex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '16px 16px 12px',
          minHeight: 0,
          overflow: 'hidden',
        }}
      >
        <div style={{ width: '100%', maxWidth: 360 }}>
        <LoginForm
          contentStyle={{
            minWidth: 280,
            maxWidth: 360,
            width: '100%',
          }}
          logo={<img alt="logo" src="/brand-assistant.svg" />}
          title="Project Agent"
          subTitle={intl.formatMessage({ id: 'pages.layouts.userLayout.title' })}
          initialValues={{
            autoLogin: true,
          }}
          actions={[]}
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
              <div className="captcha-row">
                <div className="captcha-input">
                  <ProFormText
                    name="code"
                    fieldProps={{ size: 'large' }}
                    placeholder={intl.formatMessage({
                      id: 'pages.login.captcha.placeholder',
                      defaultMessage: '请输入验证码',
                    })}
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
                  />
                </div>
                <div
                  className="captcha-img"
                  onClick={() => getCaptchaCode()}
                  title={'\u70b9\u51fb\u5237\u65b0\u9a8c\u8bc1\u7801'}
                >
                  {captchaCode ? (
                    <img src={captchaCode} alt={'\u9a8c\u8bc1\u7801'} />
                  ) : (
                    <span style={{ display: 'inline-block', width: 110, height: 38 }} />
                  )}
                </div>
              </div>
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
          <div style={{ marginBottom: 8 }}>
            <ProFormCheckbox noStyle name="autoLogin">
              <FormattedMessage id="pages.login.rememberMe" defaultMessage="自动登录" />
            </ProFormCheckbox>
            <a style={{ float: 'right' }}>
              <FormattedMessage id="pages.login.forgotPassword" defaultMessage="忘记密码" />
            </a>
          </div>
        </LoginForm>
        <div style={{ marginTop: 12 }}>
          <Button
            block
            size="large"
            onClick={handleGuestLogin}
            style={{
              background: '#e4eacd',
              borderColor: '#d5d7cd',
              color: '#1c211d',
              borderRadius: 4,
              fontWeight: 600,
            }}
          >
            {'\u6e38\u5ba2\u767b\u5f55'}
          </Button>
          <div style={{ marginTop: 6, color: '#646960', fontSize: 12, textAlign: 'center' }}>
            {'\u65e0\u9700\u8d26\u53f7\uff0c\u4ec5\u53ef\u6d4f\u89c8\u9879\u76ee\u7ba1\u7406\u6a21\u5757'}
          </div>
        </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
