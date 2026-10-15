# -*- coding: utf-8 -*-
from pathlib import Path

xianyu = r'''import React, { useEffect, useRef } from 'react';
import { Button, Space, Typography } from 'antd';
import { ArrowLeftOutlined, ExportOutlined } from '@ant-design/icons';
import { history, useModel } from '@umijs/max';
import { PageEnum } from '@/enums/pagesEnums';

/** xianyu-auto subsystem (Spring Boot + Vue, default :12400). No RuoYi shell menus. */
const XIANYU_ORIGIN = process.env.XIANYU_PORTAL_ORIGIN || 'http://127.0.0.1:12400';
const TOOLBAR_H = 48;

const XianyuEmbed: React.FC = () => {
  const frameRef = useRef<HTMLIFrameElement>(null);
  const { initialState } = useModel('@@initialState');

  useEffect(() => {
    if (!initialState?.currentUser) {
      history.replace(PageEnum.LOGIN);
    }
  }, [initialState?.currentUser]);

  useEffect(() => {
    const resize = () => {
      const frame = frameRef.current;
      if (!frame) return;
      frame.style.height = `${Math.max(window.innerHeight - TOOLBAR_H, 480)}px`;
    };
    resize();
    window.addEventListener('resize', resize);
    return () => window.removeEventListener('resize', resize);
  }, []);

  return (
    <div style={{ height: '100vh', overflow: 'hidden', background: '#0f172a' }}>
      <div
        style={{
          height: TOOLBAR_H,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 16px',
          borderBottom: '1px solid rgba(148,163,184,0.2)',
          background: '#111827',
        }}
      >
        <Space>
          <Button
            type="text"
            icon={<ArrowLeftOutlined />}
            style={{ color: '#e2e8f0' }}
            onClick={() => history.push('/portal/home')}
          >
            {'\u5b50\u7cfb\u7edf\u4e2d\u5fc3'}
          </Button>
          <Typography.Text style={{ color: '#94a3b8' }}>
            {'\u95f2\u9c7c\u81ea\u52a8\u53d1\u8d27'}
          </Typography.Text>
        </Space>
        <Button
          type="link"
          icon={<ExportOutlined />}
          href={XIANYU_ORIGIN}
          target="_blank"
          rel="noreferrer"
        >
          {'\u65b0\u7a97\u53e3\u6253\u5f00'}
        </Button>
      </div>
      <iframe
        ref={frameRef}
        title={'\u95f2\u9c7c\u81ea\u52a8\u53d1\u8d27'}
        src={`${XIANYU_ORIGIN}/`}
        style={{ width: '100%', border: 0, display: 'block', background: '#fff' }}
        allow="clipboard-read; clipboard-write"
      />
    </div>
  );
};

export default XianyuEmbed;
'''
Path(r'E:\ai-pro\project_agent\java\ruoyi-react\react-ui\src\pages\Subsystem\Xianyu\index.tsx').write_text(xianyu, encoding='utf-8')
print('xianyu page rewritten')

import pymysql
conn = pymysql.connect(host='192.168.1.57', port=3306, user='root', password='root123456', database='ry', charset='utf8mb4', connect_timeout=5, autocommit=True)
with conn.cursor() as cur:
    cur.execute("UPDATE sys_menu SET visible='1' WHERE menu_id IN (2200, 2201)")
    print('hid sidebar menus 2200/2201, rows=', cur.rowcount)
conn.close()

# also update patch SQL so re-apply stays hidden
sql = Path(r'E:\ai-pro\project_agent\java\ruoyi-react\sql\patch_portal_subsystems.sql')
text = sql.read_text(encoding='utf-8')
# set visible to 1 for 2200 and 2201 inserts (menu_type M/C rows under subsystem)
# pattern: SELECT 2200, ... 'M', '0', '0' -> 'M', '1', '0'
# SELECT 2201, ... 'C', '0', '0' -> 'C', '1', '0'
import re
text2 = re.sub(
    r"(SELECT 2200, '[^']+', 0, 6, 'subsystem', NULL, '', '', 1, 0, 'M', )'0'(, '0')",
    r"\1'1'\2",
    text,
)
text2 = re.sub(
    r"(SELECT 2201, '[^']+', 2200, 1, 'xianyu', 'subsystem/xianyu/index', '', '', 1, 0, 'C', )'0'(, '0')",
    r"\1'1'\2",
    text2,
)
sql.write_text(text2, encoding='utf-8')
print('patch sql updated')