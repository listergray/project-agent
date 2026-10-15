import { Footer, Question, SelectLang, AvatarDropdown, AvatarName } from '@/components';
import { LinkOutlined } from '@ant-design/icons';
import type { Settings as LayoutSettings } from '@ant-design/pro-components';
import { SettingDrawer } from '@ant-design/pro-components';
import { App } from 'antd';
import type { RunTimeLayoutConfig } from '@umijs/max';
import { history, Link } from '@umijs/max';
import defaultSettings from '../config/defaultSettings';
import { errorConfig } from './requestErrorConfig';
import { clearSessionToken, getAccessToken, getRefreshToken, getTokenExpireTime, setSessionToken } from './access';
import {
  filterMenusBySubsystem,
  getRemoteMenu,
  getRoutersInfo,
  getUserInfo,
  patchRouteWithRemoteMenus,
  setRemoteMenu,
} from './services/session';
import { PageEnum } from './enums/pagesEnums';


const isDev = process.env.NODE_ENV === 'development';



/**
 * @see  https://umijs.org/zh-CN/plugins/plugin-initial-state
 * */
export async function getInitialState(): Promise<{
  settings?: Partial<LayoutSettings>;
  currentUser?: API.CurrentUser;
  loading?: boolean;
  fetchUserInfo?: () => Promise<API.CurrentUser | undefined>;
}> {
  const fetchUserInfo = async () => {
    try {
      const response = await getUserInfo({
        skipErrorHandler: true,
      });
      if (response.user.avatar === '') {
        response.user.avatar =
          'https://gw.alipayobjects.com/zos/rmsportal/BiazfanxmamNRoxxVxka.png';
      }
      return {
        ...response.user,
        permissions: response.permissions,
        roles: response.roles,
      } as API.CurrentUser;
    } catch (error) {
      console.log(error);
      history.push(PageEnum.LOGIN);
    }
    return undefined;
  };
  // 如果不是登录页面，执行
  const { location } = history;
  if (location.pathname !== PageEnum.LOGIN) {
    const currentUser = await fetchUserInfo();
    return {
      fetchUserInfo,
      currentUser,
      settings: defaultSettings as Partial<LayoutSettings>,
    };
  }
  return {
    fetchUserInfo,
    settings: defaultSettings as Partial<LayoutSettings>,
  };
}

// ProLayout 支持的api https://procomponents.ant.design/components/layout
export const layout: RunTimeLayoutConfig = ({ initialState, setInitialState }) => {
  const pathname = history.location.pathname || '';
  const inProject = pathname === '/project' || pathname.startsWith('/project/');
  return {
    actionsRender: () => [<Question key="doc" />, <SelectLang key="SelectLang" />],
    avatarProps: {
      src: initialState?.currentUser?.avatar,
      title: <AvatarName />,
      render: (_, avatarChildren) => {
        return <AvatarDropdown menu={true}>{avatarChildren}</AvatarDropdown>;
      },
    },
    waterMarkProps: {
      // content: initialState?.currentUser?.nickName,
    },
    menu: {
      locale: false,
      // pathname 变化时重算侧栏（项目管理 / 系统管理互相隔离）
      params: {
        userId: initialState?.currentUser?.userId,
        pathname,
      },
      request: async () => {
        if (!initialState?.currentUser?.userId) {
          return [];
        }
        let menus = getRemoteMenu();
        if (menus == null) {
          try {
            menus = await getRoutersInfo();
            setRemoteMenu(menus);
          } catch (e) {
            console.error('menu request failed', e);
            return [];
          }
        }
        return filterMenusBySubsystem(menus || [], history.location.pathname);
      },
    },
    footerRender: () => <Footer />,
    onPageChange: () => {
      const { location } = history;
      // 如果没有登录，重定向到 login
      if (!initialState?.currentUser && location.pathname !== PageEnum.LOGIN) {
        history.push(PageEnum.LOGIN);
      }
    },
    layoutBgImgList: [
      {
        src: 'https://mdn.alipayobjects.com/yuyan_qk0oxh/afts/img/D2LWSqNny4sAAAAAAAAAAAAAFl94AQBr',
        left: 85,
        bottom: 100,
        height: '303px',
      },
      {
        src: 'https://mdn.alipayobjects.com/yuyan_qk0oxh/afts/img/C2TWRpJpiC0AAAAAAAAAAAAAFl94AQBr',
        bottom: -68,
        right: -45,
        height: '303px',
      },
      {
        src: 'https://mdn.alipayobjects.com/yuyan_qk0oxh/afts/img/F6vSTbj8KpYAAAAAAAAAAAAAFl94AQBr',
        bottom: 0,
        left: 0,
        width: '331px',
      },
    ],
    links: isDev
      ? [
        <Link key="openapi" to="/umi/plugin/openapi" target="_blank">
          <LinkOutlined />
          <span>OpenAPI 文档</span>
        </Link>,
      ]
      : [],
    menuHeaderRender: undefined,
    // 自定义 403 页面
    // unAccessible: <div>unAccessible</div>,
    // 增加一个 loading 的状态
    childrenRender: (children) => {
      // if (initialState?.loading) return <PageLoading />;
      return (
        <App>
          {children}
          <SettingDrawer
            disableUrlParams
            enableDarkTheme
            settings={initialState?.settings}
            onSettingChange={(settings) => {
              setInitialState((preInitialState) => ({
                ...preInitialState,
                settings,
              }));
            }}
          />
        </App>
      );
    },
    ...initialState?.settings,
    // 覆盖 settings：P 标仅项目管理；系统/助手用 brand-assistant
    logo: inProject ? '/brand-mark.svg' : '/brand-assistant.svg',
    title: inProject ? 'Project Agent' : '\u52a9\u624b\u7cfb\u7edf',
  };
};

export async function onRouteChange({ location }: { clientRoutes: any; location: any }) {
  if (location.pathname === PageEnum.LOGIN) return;
  // 有 token 但菜单尚未加载时拉取一次，避免 history.go(0) 死循环转圈
  if (getRemoteMenu() == null && getAccessToken()) {
    try {
      const menus = await getRoutersInfo();
      setRemoteMenu(menus);
    } catch (e) {
      console.error('onRouteChange load menus failed', e);
      setRemoteMenu([]);
    }
  }
}

// export function patchRoutes({ routes, routeComponents }) {
//   console.log('patchRoutes', routes, routeComponents);
// }


export async function patchClientRoutes({ routes }: { routes: any }) {
  // console.log('patchClientRoutes', routes);
  patchRouteWithRemoteMenus(routes);
}

export function render(oldRender: () => void) {
  const token = getAccessToken();
  if (!token || token?.length === 0) {
    oldRender();
    return;
  }
  getRoutersInfo()
    .then((res) => {
      setRemoteMenu(res);
      oldRender();
    })
    .catch((e) => {
      console.error('getRoutersInfo failed', e);
      setRemoteMenu([]);
      oldRender();
    });
}

/**
 * @name request 配置，可以配置错误处理
 * 它基于 axios 和 ahooks 的 useRequest 提供了一套统一的网络请求和错误处理方案。
 * @doc https://umijs.org/docs/max/request#配置
 */
/** 与后端 token.expireTime 一致：7 天（毫秒） */
const SESSION_TTL_MS = 7 * 24 * 60 * 60 * 1000;

export const request: any = {
  ...errorConfig,
  requestInterceptors: [
    (url: any, options: { headers: any }) => {
      const headers = options.headers ? options.headers : [];
      console.log('request ====>:', url);
      const authHeader = headers['Authorization'];
      const isToken = headers['isToken'];
      if (!authHeader && isToken !== false) {
        const expireTime = getTokenExpireTime();
        if (expireTime) {
          const left = Number(expireTime) - new Date().getTime();
          if (left < 0) {
            clearSessionToken();
          } else {
            const accessToken = getAccessToken();
            if (accessToken) {
              headers['Authorization'] = `Bearer ${accessToken}`;
              // 有操作则滑动续期本地会话，与后端 Redis 续期对齐
              setSessionToken(accessToken, getRefreshToken() || accessToken, Date.now() + SESSION_TTL_MS);
            }
          }
        } else {
          clearSessionToken();
        }
      }
      return { url, options };
    },
  ],
  responseInterceptors: [
    // (response) =>
    // {
    //   // // 不再需要异步处理读取返回体内容，可直接在data中读出，部分字段可在 config 中找到
    //   // const { data = {} as any, config } = response;
    //   // // do something
    //   // console.log('data: ', data)
    //   // console.log('config: ', config)
    //   return response
    // },
  ],
};
