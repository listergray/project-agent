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

const DouyinEmbed: React.FC = () => {
  const { initialState } = useModel('@@initialState');
  const origin = useMemo(
    () => resolveSubsystemEntry({ slug: 'douyin', port: 12500 }),
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
      title={'\u6296\u97f3\u76ee\u5f55\u53d1\u89c6\u9891'}
      iconSrc="/brand-douyin.svg"
      openOrigin={origin}
      iframeSrc={`${origin}/`}
    />
  );
};

export default DouyinEmbed;
