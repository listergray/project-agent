# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(r"E:/ai-pro/project_agent/java/ruoyi-react/react-ui/src")


def u(*codes):
    return "".join(chr(int(c, 16)) for c in codes)


def w(rel, text):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    print("wrote", rel)


TITLE_BASIC = u("57fa", "7840", "4fe1", "606f", "5f55", "5165")
SUB_BASIC = u("7ecf", "529e", "5c97") + " / " + u("8349", "7a3f", "4fdd", "5b58", "540e", "63d0", "4ea4", "4e00", "6b21", "5ba1", "6838")
TITLE_EXTEND = u("6269", "5c55", "4fe1", "606f", "5f55", "5165")
SUB_EXTEND = u("7ecf", "529e", "5c97") + " / " + u("4e00", "6b21", "5ba1", "901a", "8fc7", "540e", "65b9", "53ef", "586b", "5199")

w(
    "pages/Project/Basic/index.tsx",
    f"""import React, {{ useRef, useState }} from 'react';
import {{
  PageContainer, ProFormText, ProFormTextArea, ProFormSelect, ProFormDigit, ProFormDatePicker,
  ActionType, ProTable, ProColumns, ModalForm,
}} from '@ant-design/pro-components';
import {{ Button, message, Popconfirm, Space, Tag }} from 'antd';
import {{ PlusOutlined }} from '@ant-design/icons';
import {{ createBasic, updateBasic, submitBasic, getPmList, PmProject, STATUS_LABEL }} from '@/services/project/workflow';

const BasicPage: React.FC = () => {{
  const actionRef = useRef<ActionType>();
  const [editing, setEditing] = useState<PmProject | null>(null);
  const [open, setOpen] = useState(false);

  const columns: ProColumns<PmProject>[] = [
    {{ title: '{u("7f16","53f7")}', dataIndex: 'projectCode', width: 150 }},
    {{ title: '{u("540d","79f0")}', dataIndex: 'projectName', ellipsis: true }},
    {{ title: '{u("7c7b","578b")}', dataIndex: 'projectType', width: 90, search: false }},
    {{ title: '{u("8d1f","8d23","4eba")}', dataIndex: 'owner', width: 90 }},
    {{
      title: '{u("72b6","6001")}', dataIndex: 'status', width: 120, search: false,
      render: (_, row) => <Tag>{{STATUS_LABEL[row.status || ''] || row.status}}</Tag>,
    }},
    {{ title: '{u("66f4","65b0","65f6","95f4")}', dataIndex: 'updatedAt', width: 160, search: false }},
    {{
      title: '{u("64cd","4f5c")}', valueType: 'option', width: 220,
      render: (_, row) => (
        <Space>
          {{row.status === 'draft' && (
            <>
              <a onClick={{() => {{ setEditing(row); setOpen(true); }}}}>{u("7f16","8f91")}</a>
              <Popconfirm title="{u("63d0","4ea4","4e00","6b21","5ba1","6838")}?" onConfirm={{async () => {{
                const res = await submitBasic(row.id!);
                if (res.code === 200) {{ message.success('{u("5df2","63d0","4ea4","4e00","6b21","5ba1","6838")}'); actionRef.current?.reload(); }}
                else {{ message.error(res.msg || '{u("63d0","4ea4","5931","8d25")}'); }}
              }}}}>
                <a>{u("63d0","4ea4","5ba1","6838")}</a>
              </Popconfirm>
            </>
          )}}
        </Space>
      ),
    }},
  ];

  return (
    <PageContainer header={{{{ title: '{TITLE_BASIC}', subTitle: '{SUB_BASIC}' }}}}>
      <ProTable<PmProject>
        headerTitle="{u("6211","7684","7acb","9879","8349","7a3f")} / {u("57fa","7840","4fe1","606f")}"
        actionRef={{actionRef}}
        rowKey="id"
        columns={{columns}}
        toolBarRender={{() => [
          <Button key="add" type="primary" icon={{<PlusOutlined />}} onClick={{() => {{ setEditing(null); setOpen(true); }}}}>
            {u("65b0","5efa","9879","76ee")}
          </Button>,
        ]}}
        request={{async (params) => {{
          const res = await getPmList({{
            keyword: params.projectName || params.projectCode || params.owner,
            pageNum: params.current,
            pageSize: params.pageSize,
          }});
          const rows = (res.rows || []).filter((r) => r.status === 'draft' || r.status === 'pending_basic');
          return {{ data: rows, total: rows.length, success: res.code === 200 }};
        }}}}
      />
      <ModalForm<PmProject>
        title={{editing ? '{u("7f16","8f91","57fa","7840","4fe1","606f")}' : '{u("65b0","5efa","57fa","7840","4fe1","606f")}'}}
        open={{open}}
        modalProps={{{{ destroyOnClose: true, onCancel: () => setOpen(false) }}}}
        initialValues={{editing || {{ projectType: '{u("7814","53d1")}', budget: 0 }}}}
        onFinish={{async (values) => {{
          const payload = {{
            ...values,
            id: editing?.id,
            startDate: values.startDate ? String(values.startDate).slice(0, 10) : values.startDate,
            endDate: values.endDate ? String(values.endDate).slice(0, 10) : values.endDate,
          }};
          const res = editing ? await updateBasic(payload) : await createBasic(payload);
          if (res.code === 200) {{
            message.success(editing ? '{u("5df2","4fdd","5b58")}' : '{u("5df2","521b","5efa","8349","7a3f")}');
            setOpen(false);
            actionRef.current?.reload();
            return true;
          }}
          message.error(res.msg || '{u("4fdd","5b58","5931","8d25")}');
          return false;
        }}}}
      >
        <ProFormText name="projectCode" label="{u("9879","76ee","7f16","53f7")}" placeholder="{u("53ef","7a7a")} / auto" />
        <ProFormText name="projectName" label="{u("9879","76ee","540d","79f0")}" rules={{[{{ required: true, message: '{u("8bf7","8f93","5165","9879","76ee","540d","79f0")}' }}]}} />
        <ProFormSelect name="projectType" label="{u("9879","76ee","7c7b","578b")}" options={{['{u("7814","53d1")}', '{u("5b9e","65bd")}', '{u("8fd0","7ef4")}', '{u("9884","7814")}', '{u("5176","4ed6")}'].map((v) => ({{ label: v, value: v }}))}} />
        <ProFormText name="owner" label="{u("8d1f","8d23","4eba")}" />
        <ProFormText name="department" label="{u("6240","5c5e","90e8","95e8")}" />
        <ProFormDigit name="budget" label="{u("9884","7b97")}({u("5143")})" min={{0}} fieldProps={{{{ precision: 2 }}}} />
        <ProFormDatePicker name="startDate" label="{u("8ba1","5212","5f00","59cb")}" fieldProps={{{{ format: 'YYYY-MM-DD' }}}} />
        <ProFormDatePicker name="endDate" label="{u("8ba1","5212","7ed3","675f")}" fieldProps={{{{ format: 'YYYY-MM-DD' }}}} />
        <ProFormTextArea name="description" label="{u("9879","76ee","6982","8ff0")}" />
      </ModalForm>
    </PageContainer>
  );
}};

export default BasicPage;
""",
)

w(
    "pages/Project/Extend/index.tsx",
    f"""import React, {{ useRef, useState }} from 'react';
import {{
  PageContainer, ProTable, ProColumns, ActionType, ModalForm, ProFormText, ProFormTextArea, ProFormSelect,
}} from '@ant-design/pro-components';
import {{ Alert, Button, Space, Tag, message, Popconfirm }} from 'antd';
import {{
  getPmList, updateExtend, submitExtend, submitPurchase, PmProject, STATUS_LABEL,
}} from '@/services/project/workflow';

const ExtendPage: React.FC = () => {{
  const actionRef = useRef<ActionType>();
  const [editing, setEditing] = useState<PmProject | null>(null);
  const [open, setOpen] = useState(false);

  const columns: ProColumns<PmProject>[] = [
    {{ title: '{u("7f16","53f7")}', dataIndex: 'projectCode', width: 150 }},
    {{ title: '{u("540d","79f0")}', dataIndex: 'projectName', ellipsis: true }},
    {{
      title: '{u("72b6","6001")}', dataIndex: 'status', width: 120, search: false,
      render: (_, row) => <Tag color="cyan">{{STATUS_LABEL[row.status || ''] || row.status}}</Tag>,
    }},
    {{ title: '{u("76ee","6807","4ea4","4ed8")}', dataIndex: 'goals', ellipsis: true, search: false }},
    {{ title: '{u("66f4","65b0","65f6","95f4")}', dataIndex: 'updatedAt', width: 160, search: false }},
    {{
      title: '{u("64cd","4f5c")}', valueType: 'option', width: 280,
      render: (_, row) => (
        <Space>
          {{(row.status === 'basic_passed' || row.status === 'extend_passed') && (
            <a onClick={{() => {{ setEditing(row); setOpen(true); }}}}>{u("7f16","8f91","6269","5c55")}</a>
          )}}
          {{row.status === 'basic_passed' && (
            <Popconfirm title="{u("63d0","4ea4","4e8c","6b21","5ba1","6838")}?" onConfirm={{async () => {{
              const res = await submitExtend(row.id!);
              if (res.code === 200) {{ message.success('{u("5df2","63d0","4ea4","4e8c","6b21","5ba1","6838")}'); actionRef.current?.reload(); }}
              else {{ message.error(res.msg || 'fail'); }}
            }}}}>
              <a>{u("63d0","4ea4","4e8c","6b21","5ba1")}</a>
            </Popconfirm>
          )}}
          {{row.status === 'extend_passed' && (
            <Popconfirm title="{u("53d1","8d77","8d2d","4e70","8054","5ba1")}?" onConfirm={{async () => {{
              const res = await submitPurchase(row.id!);
              if (res.code === 200) {{ message.success('{u("5df2","53d1","8d77","8d2d","4e70","8054","5ba1")}'); actionRef.current?.reload(); }}
              else {{ message.error(res.msg || 'fail'); }}
            }}}}>
              <Button type="link" size="small">{u("53d1","8d77","8d2d","4e70","8054","5ba1")}</Button>
            </Popconfirm>
          )}}
        </Space>
      ),
    }},
  ];

  return (
    <PageContainer header={{{{ title: '{TITLE_EXTEND}', subTitle: '{SUB_EXTEND}' }}}}>
      <Alert type="info" showIcon style={{{{ marginBottom: 16 }}}} message="{u("4ec5")} basic_passed {u("53ef","63d0","4ea4","4e8c","6b21","5ba1")}; extend_passed {u("53ef","53d1","8d77","8d2d","4e70","8054","5ba1")}" />
      <ProTable<PmProject>
        headerTitle="{u("53ef","586b","6269","5c55")} / {u("53ef","53d1","8d77","8054","5ba1")}"
        actionRef={{actionRef}}
        rowKey="id"
        columns={{columns}}
        request={{async (params) => {{
          const res = await getPmList({{
            keyword: params.projectName || params.projectCode,
            pageNum: 1,
            pageSize: 100,
          }});
          const rows = (res.rows || []).filter((r) =>
            r.status === 'basic_passed' || r.status === 'extend_passed' || r.status === 'pending_extend');
          return {{ data: rows, total: rows.length, success: res.code === 200 }};
        }}}}
      />
      <ModalForm<PmProject>
        title="{u("6269","5c55","4fe1","606f")}"
        open={{open}}
        modalProps={{{{ destroyOnClose: true, onCancel: () => setOpen(false) }}}}
        initialValues={{editing || {{}}}}
        onFinish={{async (values) => {{
          const res = await updateExtend({{ ...values, id: editing?.id }});
          if (res.code === 200) {{
            message.success('{u("6269","5c55","4fe1","606f","5df2","4fdd","5b58")}');
            setOpen(false);
            actionRef.current?.reload();
            return true;
          }}
          message.error(res.msg || 'fail');
          return false;
        }}}}
      >
        <ProFormTextArea name="goals" label="{u("76ee","6807","4e0e","4ea4","4ed8","7269")}" rules={{[{{ required: true }}]}} />
        <ProFormText name="members" label="{u("6838","5fc3","6210","5458")}" />
        <ProFormSelect name="riskLevel" label="{u("98ce","9669","7b49","7ea7")}" options={{['{u("4f4e")}', '{u("4e2d")}', '{u("9ad8")}'].map((v) => ({{ label: v, value: v }}))}} />
        <ProFormSelect name="priority" label="{u("4f18","5148","7ea7")}" options={{['P0', 'P1', 'P2'].map((v) => ({{ label: v, value: v }}))}} />
        <ProFormTextArea name="purchasePlan" label="{u("91c7","8d2d","8bf4","660e")}" />
        <ProFormTextArea name="financePlan" label="{u("8d44","91d1","8bf4","660e")}" />
      </ModalForm>
    </PageContainer>
  );
}};

export default ExtendPage;
""",
)

AUDIT1 = u("4e00", "6b21", "5ba1", "6838")
AUDIT2 = u("4e8c", "6b21", "5ba1", "6838")
PURCHASE = u("8d2d", "4e70", "8054", "5ba1")
FINANCE = u("8d22", "52a1", "8054", "5ba1")

w(
    "pages/Project/Audit/AuditQueue.tsx",
    f"""import React, {{ useRef, useState }} from 'react';
import {{
  PageContainer, ProTable, ProColumns, ActionType, ModalForm, ProFormTextArea, ProFormRadio,
}} from '@ant-design/pro-components';
import {{ Drawer, Space, Tag, Timeline, Typography, message }} from 'antd';
import {{ getPmList, getPm, reviewPm, PmProject, STATUS_LABEL }} from '@/services/project/workflow';

export type AuditStage = 'basic' | 'extend' | 'purchase' | 'finance';

const STAGE_STATUS: Record<AuditStage, string> = {{
  basic: 'pending_basic',
  extend: 'pending_extend',
  purchase: 'pending_purchase',
  finance: 'pending_finance',
}};

const STAGE_TITLE: Record<AuditStage, string> = {{
  basic: '{AUDIT1}',
  extend: '{AUDIT2}',
  purchase: '{PURCHASE}',
  finance: '{FINANCE}',
}};

type Props = {{ stage: AuditStage }};

const AuditQueue: React.FC<Props> = ({{ stage }}) => {{
  const actionRef = useRef<ActionType>();
  const [current, setCurrent] = useState<PmProject | null>(null);
  const [reviewOpen, setReviewOpen] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);

  const columns: ProColumns<PmProject>[] = [
    {{ title: '{u("7f16","53f7")}', dataIndex: 'projectCode', width: 150 }},
    {{
      title: '{u("540d","79f0")}', dataIndex: 'projectName', ellipsis: true,
      render: (_, row) => (
        <a onClick={{async () => {{
          const res = await getPm(row.id!);
          if (res.code === 200) {{ setCurrent(res.data); setDetailOpen(true); }}
        }}}}>{{row.projectName}}</a>
      ),
    }},
    {{ title: '{u("8d1f","8d23","4eba")}', dataIndex: 'owner', width: 90 }},
    {{ title: '{u("90e8","95e8")}', dataIndex: 'department', width: 110, search: false }},
    {{ title: '{u("9884","7b97")}', dataIndex: 'budget', width: 100, search: false, render: (_, r) => r.budget ?? '-' }},
    {{
      title: '{u("72b6","6001")}', dataIndex: 'status', width: 120, search: false,
      render: (_, row) => <Tag color="processing">{{STATUS_LABEL[row.status || '']}}</Tag>,
    }},
    {{ title: '{u("66f4","65b0")}', dataIndex: 'updatedAt', width: 160, search: false }},
    {{
      title: '{u("64cd","4f5c")}', valueType: 'option', width: 100,
      render: (_, row) => <a onClick={{() => {{ setCurrent(row); setReviewOpen(true); }}}}>{u("529e","7406")}</a>,
    }},
  ];

  return (
    <PageContainer header={{{{ title: STAGE_TITLE[stage], subTitle: '{u("5206","5c97","5f85","529e","961f","5217")}' }}}}>
      <ProTable<PmProject>
        headerTitle={{`{u("5f85")}${{STAGE_TITLE[stage]}}`}}
        actionRef={{actionRef}}
        rowKey="id"
        columns={{columns}}
        search={{{{ labelWidth: 'auto' }}}}
        request={{async (params) => {{
          const res = await getPmList({{
            status: STAGE_STATUS[stage],
            keyword: params.projectName || params.projectCode || params.owner,
            pageNum: params.current,
            pageSize: params.pageSize,
          }});
          return {{ data: res.rows || [], total: res.total || 0, success: res.code === 200 }};
        }}}}
      />
      <ModalForm
        title={{`${{STAGE_TITLE[stage]}}{u("529e","7406")}`}}
        open={{reviewOpen}}
        modalProps={{{{ destroyOnClose: true, onCancel: () => setReviewOpen(false) }}}}
        initialValues={{{{ action: 'approve' }}}}
        onFinish={{async (values) => {{
          if (!current?.id) return false;
          const res = await reviewPm({{ id: current.id, stage, action: values.action, comment: values.comment }});
          if (res.code === 200) {{
            message.success(values.action === 'approve' ? '{u("5df2","901a","8fc7")}' : '{u("5df2","9a73","56de")}');
            setReviewOpen(false);
            actionRef.current?.reload();
            return true;
          }}
          message.error(res.msg || 'fail');
          return false;
        }}}}
      >
        <Typography.Paragraph>{u("9879","76ee")}: {{current?.projectName}} ({{current?.projectCode}})</Typography.Paragraph>
        <ProFormRadio.Group
          name="action"
          label="{u("7ed3","8bba")}"
          options={{[
            {{ label: '{u("901a","8fc7")}', value: 'approve' }},
            {{ label: '{u("9a73","56de")}', value: 'reject' }},
          ]}}
          rules={{[{{ required: true }}]}}
        />
        <ProFormTextArea name="comment" label="{u("610f","89c1")}" />
      </ModalForm>
      <Drawer width={{480}} title="{u("9879","76ee","8be6","60c5")}" open={{detailOpen}} onClose={{() => setDetailOpen(false)}} destroyOnClose>
        {{current && (
          <Space direction="vertical" style={{{{ width: '100%' }}}}>
            <Typography.Paragraph>
              <strong>{u("6982","8ff0")}:</strong>{{current.description || '-'}}
              <br /><strong>{u("76ee","6807")}:</strong>{{current.goals || '-'}}
              <br /><strong>{u("91c7","8d2d")}:</strong>{{current.purchasePlan || '-'}}
              <br /><strong>{u("8d44","91d1")}:</strong>{{current.financePlan || '-'}}
            </Typography.Paragraph>
            <Timeline items={{(current.history || []).slice().reverse().map((h) => ({{
              children: (
                <div>
                  {{h.action}} / {{h.by}} {{h.role ? `(${{h.role}})` : ''}}
                  <div><Typography.Text type="secondary">{{h.at}} {{h.note || ''}}</Typography.Text></div>
                </div>
              ),
            }}))}} />
          </Space>
        )}}
      </Drawer>
    </PageContainer>
  );
}};

export default AuditQueue;
""",
)

for stage in ("basic", "extend", "purchase", "finance"):
    name = stage.capitalize()
    w(
        f"pages/Project/Audit/{name}.tsx",
        f"""import React from 'react';
import AuditQueue from './AuditQueue';

export default () => <AuditQueue stage="{stage}" />;
""",
    )

print("all frontend pages ok")
