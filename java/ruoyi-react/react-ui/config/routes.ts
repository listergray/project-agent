/**
 * @name umi route config
 * @doc https://umijs.org/docs/guides/routes
 * NOTE: path '*' must be last or it swallows dynamic menu routes.
 */
export default [
  {
    path: '/',
    component: './RedirectHome',
  },
  {
    path: '/portal',
    layout: false,
    routes: [
      {
        name: 'portal-home',
        path: '/portal/home',
        component: './Portal/Home',
      },
    ],
  },
  {
    path: '/subsystem',
    layout: false,
    routes: [
      {
        name: 'xianyu-auto',
        path: '/subsystem/xianyu',
        component: './Subsystem/Xianyu',
      },
      {
        name: 'douyin-auto',
        path: '/subsystem/douyin',
        component: './Subsystem/Douyin',
      },
      {
        name: 'myhome',
        path: '/subsystem/myhome',
        component: './Subsystem/Myhome',
      },
    ],
  },

  {
    path: '/user',
    layout: false,
    routes: [
      {
        name: 'login',
        path: '/user/login',
        component: './User/Login',
      },
    ],
  },
  {
    path: '/account',
    routes: [
      {
        name: 'acenter',
        path: '/account/center',
        component: './User/Center',
      },
      {
        name: 'asettings',
        path: '/account/settings',
        component: './User/Settings',
      },
    ],
  },
  {
    // 项目管理：静态兜底，避免菜单被停用/隐藏时 /project/chat 落到 404
    path: '/project',
    routes: [
      {
        name: 'project-chat',
        path: '/project/chat',
        component: './Project/Chat',
      },
      {
        name: 'project-parse',
        path: '/project/parse',
        component: './Project/Parse',
      },
    ],
  },
  {
    name: 'system',
    path: '/system',
    routes: [
      {
        name: 'dict-data',
        path: '/system/dict-data/index/:id',
        component: './System/DictData',
      },
      {
        name: 'role-auth-user',
        path: '/system/role-auth/user/:id',
        component: './System/Role/authUser',
      },
    ],
  },
  {
    name: 'monitor',
    path: '/monitor',
    routes: [
      {
        name: 'job-log',
        path: '/monitor/job-log/index/:id',
        component: './Monitor/JobLog',
      },
    ],
  },
  {
    name: 'tool',
    path: '/tool',
    routes: [
      {
        name: 'gen-import',
        path: '/tool/gen/import',
        component: './Tool/Gen/import',
      },
      {
        name: 'gen-edit',
        path: '/tool/gen/edit',
        component: './Tool/Gen/edit',
      },
    ],
  },
  {
    path: '*',
    layout: false,
    component: './404',
  },
];
