/** ??????????? http://127.0.0.1:18800? */
export const xuzao = {
  ink: '#1c211d',
  lime: '#baf047',
  line: '#d5d7cd',
  muted: '#646960',
  pale: '#e4eacd',
  paper: '#f4f3ed',
  white: '#ffffff',
  radius: 4,
  sans: '"PingFang SC","Microsoft YaHei","Noto Sans CJK SC",Arial,sans-serif',
} as const;

export type XuzaoToken = typeof xuzao;
