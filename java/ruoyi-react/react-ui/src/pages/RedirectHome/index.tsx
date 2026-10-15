import React, { useEffect, useState } from 'react';
import { history, useModel } from '@umijs/max';
import { Spin } from 'antd';
import { getFirstMenuPath, getRemoteMenu, getRoutersInfo, setRemoteMenu } from '@/services/session';

/**
 * admin / guest → 子系统中心；其他角色 → 第一个可见菜单。
 */
const RedirectHome: React.FC = () => {
  const [tip, setTip] = useState('正在进入…');
  const { initialState } = useModel('@@initialState');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const roles = (initialState?.currentUser?.roles || []) as string[];
        if (roles.includes('admin') || roles.includes('guest')) {
          if (!cancelled) history.replace('/portal/home');
          return;
        }
        let menus = getRemoteMenu();
        if (menus == null) {
          menus = await getRoutersInfo();
          if (!cancelled) setRemoteMenu(menus);
        }
        const first = getFirstMenuPath(menus);
        if (cancelled) return;
        if (first) {
          history.replace(first);
          return;
        }
        setTip('暂无可用菜单，请联系管理员授权');
      } catch (e) {
        console.error(e);
        if (!cancelled) setTip('菜单加载失败，请刷新重试');
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [initialState?.currentUser?.roles]);

  return (
    <div style={{ paddingTop: 120, textAlign: 'center' }}>
      <Spin size="large" tip={tip} />
      <div style={{ marginTop: 16, color: '#64748b' }}>{tip}</div>
    </div>
  );
};

export default RedirectHome;
