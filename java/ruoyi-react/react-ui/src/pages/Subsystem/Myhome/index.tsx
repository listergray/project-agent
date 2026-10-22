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

const MyhomeEmbed: React.FC = () => {
  const { initialState } = useModel('@@initialState');
  const origin = useMemo(
    () => resolveSubsystemEntry({ slug: 'myhome', port: 18001 }),
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
      title={'\u4eba\u751f\u6307\u5357'}
      iconSrc="/brand-myhome.svg"
      openOrigin={origin}
      iframeSrc={`${origin}/`}
    />
  );
};

export default MyhomeEmbed;
