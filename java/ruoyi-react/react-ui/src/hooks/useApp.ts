import { App } from 'antd';

/**
 * 便捷 hook，获取 antd App 组件的 message / notification / modal
 * 解决 antd v6 静态方法无法消费动态主题上下文的问题
 */
const useApp = () => {
  return App.useApp();
};

export default useApp;
