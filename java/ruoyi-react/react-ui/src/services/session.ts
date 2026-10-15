import { createIcon } from '@/utils/IconUtil';
import { MenuDataItem } from '@ant-design/pro-components';
import { request } from '@umijs/max';
import React, { lazy } from 'react';


let remoteMenu: any = null;

export function getRemoteMenu() {
  return remoteMenu;
}

export function setRemoteMenu(data: any) {
  remoteMenu = data;
}


/** 门户/闲鱼走静态 layout:false，勿再挂进 ProLayout（否则会冲掉独立页或导致动态路由注册异常） */
function isStandaloneSubsystemMenu(menuItem: any): boolean {
  const path = (menuItem?.path || '').replace(/^\//, '');
  const comp = (menuItem?.component || '').toLowerCase();
  if (path === 'portal' || path.startsWith('portal/') || comp.startsWith('portal/')) return true;
  if (path === 'subsystem' || path.startsWith('subsystem/') || comp.startsWith('subsystem/')) return true;
  return false;
}

function menuTopPath(item: any): string {
  return (item?.path || '').replace(/^\//, '').split('/')[0] || '';
}

function isProjectMenuItem(item: any): boolean {
  const top = menuTopPath(item);
  if (top === 'project') return true;
  const comp = (item?.component || '').toLowerCase();
  return comp.startsWith('project/');
}

/** 按当前 URL 隔离侧栏：项目管理 ↔ 系统管理互不展示 */
export function filterMenusBySubsystem(items: any[] = [], pathname = ''): any[] {
  const path = pathname || '';
  const inProject = path === '/project' || path.startsWith('/project/');
  const inSystem =
    path.startsWith('/system') ||
    path.startsWith('/monitor') ||
    path.startsWith('/tool') ||
    path.startsWith('/account');

  const stripStandalone = (list: any[]): any[] =>
    list
      .filter((m) => {
        const p = menuTopPath(m);
        if (p === 'portal' || p === 'subsystem') return false;
        return true;
      })
      .map((m) => (m.routes?.length ? { ...m, routes: stripStandalone(m.routes) } : m));

  let next = stripStandalone(items);

  if (inProject) {
    next = next.filter((m) => isProjectMenuItem(m));
  } else if (inSystem) {
    next = next.filter((m) => !isProjectMenuItem(m));
  }

  // 子菜单只剥独立入口，不再按 pathname 二次裁剪（子 path 常为 chat/parse 相对路径）
  const mapChildren = (list: any[]): any[] =>
    list.map((m) =>
      m.routes?.length
        ? { ...m, routes: mapChildren(stripStandalone(m.routes)) }
        : m,
    );

  return mapChildren(next);
}

function patchRouteItems(route: any, menu: any, parentPath: string) {
  if (!route || !menu?.length) return;
  if (!route.routes) route.routes = [];
  for (const menuItem of menu) {
    if (isStandaloneSubsystemMenu(menuItem)) {
      continue;
    }
    const comp = menuItem.component;
    if (comp === 'Layout' || comp === 'ParentView' || (!comp && menuItem.routes?.length)) {
      if (menuItem.routes) {
        let hasItem = false;
        let newItem = null;
        for (const routeChild of route.routes) {
          if (routeChild.path === menuItem.path) {
            hasItem = true;
            newItem = routeChild;
          }
        }
        if (!hasItem) {
          newItem = {
            path: menuItem.path,
            routes: [],
            children: []
          }
          route.routes.push(newItem)
        }
        patchRouteItems(newItem, menuItem.routes, parentPath + menuItem.path + '/');
      }
    } else if (comp) {
      const names: string[] = menuItem.component.split('/');
      let path = '';
      names.forEach(name => {
        if (path.length > 0) {
          path += '/';
        }
        if (name !== 'index') {
          path += name.at(0)?.toUpperCase() + name.substr(1);
        } else {
          path += name;
        }
      })
      if (!path.endsWith('.tsx')) {
        path += '.tsx'
      }
      if (route.routes === undefined) {
        route.routes = [];
      }
      if (route.children === undefined) {
        route.children = [];
      }
      const newRoute = {
        element: React.createElement(lazy(() => import('@/pages/' + path))),
        path: parentPath + menuItem.path,
      }
      route.children.push(newRoute);
      route.routes.push(newRoute);
    }
  }
}

export function patchRouteWithRemoteMenus(routes: any) {
  if (remoteMenu === null) { return; }
  let proLayout = null;
  for (const routeItem of routes) {
    if (routeItem.id === 'ant-design-pro-layout') {
      proLayout = routeItem;
      break;
    }
  }
  if (!proLayout) {
    console.error('patchRouteWithRemoteMenus: ant-design-pro-layout not found');
    return;
  }
  patchRouteItems(proLayout, remoteMenu, '');
}

/** 获取当前的用户 GET /api/getUserInfo */
export async function getUserInfo(options?: Record<string, any>) {
  return request<API.UserInfoResult>('/api/getInfo', {
    method: 'GET',
    ...(options || {}),
  });
}

// 刷新方法
export async function refreshToken() {
  return request('/api/auth/refresh', {
    method: 'post'
  })
}

export async function getRouters(): Promise<any> {
  return request('/api/getRouters');
}

export function convertCompatRouters(childrens: API.RoutersMenuItem[]): any[] {
  return childrens.map((item: API.RoutersMenuItem) => {
    return {
      path: item.path,
      icon: createIcon(item.meta.icon),
      //  icon: item.meta.icon,
      name: item.meta.title,
      routes: item.children ? convertCompatRouters(item.children) : undefined,
      hideChildrenInMenu: item.hidden,
      hideInMenu: item.hidden,
      component: item.component,
      authority: item.perms,
    };
  });
}

export async function getRoutersInfo(): Promise<MenuDataItem[]> {
  return getRouters().then((res) => {
    if (res.code === 200) {
      return convertCompatRouters(res.data);
    } else {
      return [];
    }
  });
}

/** 取侧栏第一个可见叶子菜单路径（跳过 hidden） */
export function getFirstMenuPath(menus: MenuDataItem[] | null | undefined, parent = ''): string | undefined {
  if (!menus?.length) return undefined;
  for (const item of menus) {
    if (item.hideInMenu) continue;
    const raw = (item.path || '').trim();
    if (!raw || raw.startsWith('http://') || raw.startsWith('https://')) continue;

    const joined = raw.startsWith('/')
      ? raw
      : `${parent.replace(/\/$/, '')}/${raw}`.replace(/\/+/g, '/');
    const full = joined.startsWith('/') ? joined : `/${joined}`;

    if (item.routes?.length) {
      const child = getFirstMenuPath(item.routes, full);
      if (child) return child;
      continue;
    }
    // 有 component 的叶子，或无子级的菜单项
    if (item.component || !item.routes?.length) {
      return full;
    }
  }
  return undefined;
}

export function getMatchMenuItem(
  path: string,
  menuData: MenuDataItem[] | undefined,
): MenuDataItem[] {
  if (!menuData) return [];
  let items: MenuDataItem[] = [];
  menuData.forEach((item) => {
    if (item.path) {
      if (item.path === path) {
        items.push(item);
        return;
      }
      if (path.length >= item.path?.length) {
        const exp = `${item.path}/*`;
        if (path.match(exp)) {
          if (item.routes) {
            const subpath = path.substr(item.path.length + 1);
            const subItem: MenuDataItem[] = getMatchMenuItem(subpath, item.routes);
            items = items.concat(subItem);
          } else {
            const paths = path.split('/');
            if (paths.length >= 2 && paths[0] === item.path && paths[1] === 'index') {
              items.push(item);
            }
          }
        }
      }
    }
  });
  return items;
}
