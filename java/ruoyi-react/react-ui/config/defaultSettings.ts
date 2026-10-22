import type { ProLayoutProps } from '@ant-design/pro-components';

/**
 * 全局布局与 Ant Design 主题（序造 paper / ink / lime）
 */
const Settings: ProLayoutProps & {
  logo?: string;
  colorWeak?: boolean;
} = {
  navTheme: 'light',
  colorPrimary: '#1c211d',
  layout: 'mix',
  contentWidth: 'Fluid',
  fixedHeader: false,
  fixSiderbar: true,
  colorWeak: false,
  title: '\u52a9\u624b\u7cfb\u7edf',
  logo: '/brand-assistant.svg',
  iconfontUrl: '',
  token: {
    colorBgAppListIconHover: 'rgba(28,33,29,0.06)',
    colorTextAppListIconHover: '#1c211d',
    colorTextAppListIcon: '#646960',
    sider: {
      colorMenuBackground: '#f4f3ed',
      colorBgMenuItemHover: '#e4eacd',
      colorBgMenuItemSelected: '#e4eacd',
      colorTextMenuSelected: '#1c211d',
      colorTextMenuItemHover: '#1c211d',
      colorTextMenu: '#646960',
      colorTextMenuActive: '#1c211d',
      colorBgMenuItemCollapsedElevated: '#ffffff',
      colorTextMenuSecondary: '#646960',
      paddingInlineLayoutMenu: 12,
    },
    header: {
      colorBgHeader: '#f4f3ed',
      colorHeaderTitle: '#1c211d',
      colorTextMenu: '#646960',
      colorTextMenuSecondary: '#646960',
      colorTextMenuSelected: '#1c211d',
      colorBgMenuItemHover: '#e4eacd',
      colorBgMenuItemSelected: '#e4eacd',
      colorTextRightActionsItem: '#646960',
      heightLayoutHeader: 56,
    },
    pageContainer: {
      colorBgPageContainer: '#f4f3ed',
      paddingBlockPageContainerContent: 24,
      paddingInlinePageContainerContent: 24,
    },
    bgLayout: '#f4f3ed',
  },
};

export default Settings;
