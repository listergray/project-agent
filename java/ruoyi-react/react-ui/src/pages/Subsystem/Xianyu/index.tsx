import React, { useEffect, useMemo } from 'react';
import { history, useModel } from '@umijs/max';
import { PageEnum } from '@/enums/pagesEnums';
import { getAccessToken } from '@/access';
import SubsystemChrome from '@/components/SubsystemChrome';
import { resolveSubsystemEntry } from '@/utils/subsystemOrigin';

function getAccessTokenSafe() {
  try {
    return !!getAccessToken();
  } catch {
    return false;
  }
}

const XianyuEmbed: React.FC = () => {
  const { initialState } = useModel('@@initialState');
  const origin = useMemo(
    () => resolveSubsystemEntry({ slug: 'xianyu', port: 12400 }),
    [],
  );

  useEffect(() => {
    if (!initialState) return;
    if (!initialState.currentUser && !getAccessTokenSafe()) {
      history.replace(PageEnum.LOGIN);
    }
  }, [initialState]);

  return (
    <SubsystemChrome
      title={'\u95f2\u9c7c\u81ea\u52a8\u53d1\u8d27'}
      iconSrc="/brand-xianyu.svg"
      openOrigin={origin}
      iframeSrc={`${origin}/?embed=1&v=shop-ops-1`}
    />
  );
};

export default XianyuEmbed;
