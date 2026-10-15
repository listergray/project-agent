import React, { useRef, useState } from 'react';
import {
  PageContainer, ProTable, ProColumns, ActionType, ModalForm, ProFormTextArea, ProFormRadio,
} from '@ant-design/pro-components';
import { Drawer, Space, Tag, Timeline, Typography, message } from 'antd';
import { getPmList, getPm, reviewPm, PmProject, STATUS_LABEL } from '@/services/project/workflow';

export type AuditStage = 'basic' | 'extend' | 'purchase' | 'finance';

const STAGE_STATUS: Record<AuditStage, string> = {
  basic: 'pending_basic',
  extend: 'pending_extend',
  purchase: 'pending_purchase',
  finance: 'pending_finance',
};

const STAGE_TITLE: Record<AuditStage, string> = {
  basic: '一次审核',
  extend: '二次审核',
  purchase: '购买联审',
  finance: '财务联审',
};

type Props = { stage: AuditStage };

const AuditQueue: React.FC<Props> = ({ stage }) => {
  const actionRef = useRef<ActionType>();
  const [current, setCurrent] = useState<PmProject | null>(null);
  const [reviewOpen, setReviewOpen] = useState(false);
  const [detailOpen, setDetailOpen] = useState(false);

  const columns: ProColumns<PmProject>[] = [
    { title: '编号', dataIndex: 'projectCode', width: 150 },
    {
      title: '名称', dataIndex: 'projectName', ellipsis: true,
      render: (_, row) => (
        <a onClick={async () => {
          const res = await getPm(row.id!);
          if (res.code === 200) { setCurrent(res.data); setDetailOpen(true); }
        }}>{row.projectName}</a>
      ),
    },
    { title: '负责人', dataIndex: 'owner', width: 90 },
    { title: '部门', dataIndex: 'department', width: 110, search: false },
    { title: '预算', dataIndex: 'budget', width: 100, search: false, render: (_, r) => r.budget ?? '-' },
    {
      title: '状态', dataIndex: 'status', width: 120, search: false,
      render: (_, row) => <Tag color="processing">{STATUS_LABEL[row.status || '']}</Tag>,
    },
    { title: '更新', dataIndex: 'updatedAt', width: 160, search: false },
    {
      title: '操作', valueType: 'option', width: 100,
      render: (_, row) => <a onClick={() => { setCurrent(row); setReviewOpen(true); }}>办理</a>,
    },
  ];

  return (
    <PageContainer header={{ title: STAGE_TITLE[stage], subTitle: '分岗待办队列' }}>
      <ProTable<PmProject>
        headerTitle={`待${STAGE_TITLE[stage]}`}
        actionRef={actionRef}
        rowKey="id"
        columns={columns}
        search={{ labelWidth: 'auto' }}
        request={async (params) => {
          const res = await getPmList({
            status: STAGE_STATUS[stage],
            keyword: params.projectName || params.projectCode || params.owner,
            pageNum: params.current,
            pageSize: params.pageSize,
          });
          return { data: res.rows || [], total: res.total || 0, success: res.code === 200 };
        }}
      />
      <ModalForm
        title={`${STAGE_TITLE[stage]}办理`}
        open={reviewOpen}
        modalProps={{ destroyOnClose: true, onCancel: () => setReviewOpen(false) }}
        initialValues={{ action: 'approve' }}
        onFinish={async (values) => {
          if (!current?.id) return false;
          const res = await reviewPm({ id: current.id, stage, action: values.action, comment: values.comment });
          if (res.code === 200) {
            message.success(values.action === 'approve' ? '已通过' : '已驳回');
            setReviewOpen(false);
            actionRef.current?.reload();
            return true;
          }
          message.error(res.msg || 'fail');
          return false;
        }}
      >
        <Typography.Paragraph>项目: {current?.projectName} ({current?.projectCode})</Typography.Paragraph>
        <ProFormRadio.Group
          name="action"
          label="结论"
          options={[
            { label: '通过', value: 'approve' },
            { label: '驳回', value: 'reject' },
          ]}
          rules={[{ required: true }]}
        />
        <ProFormTextArea name="comment" label="意见" />
      </ModalForm>
      <Drawer width={480} title="项目详情" open={detailOpen} onClose={() => setDetailOpen(false)} destroyOnClose>
        {current && (
          <Space direction="vertical" style={{ width: '100%' }}>
            <Typography.Paragraph>
              <strong>概述:</strong>{current.description || '-'}
              <br /><strong>目标:</strong>{current.goals || '-'}
              <br /><strong>采购:</strong>{current.purchasePlan || '-'}
              <br /><strong>资金:</strong>{current.financePlan || '-'}
            </Typography.Paragraph>
            <Timeline items={(current.history || []).slice().reverse().map((h) => ({
              children: (
                <div>
                  {h.action} / {h.by} {h.role ? `(${h.role})` : ''}
                  <div><Typography.Text type="secondary">{h.at} {h.note || ''}</Typography.Text></div>
                </div>
              ),
            }))} />
          </Space>
        )}
      </Drawer>
    </PageContainer>
  );
};

export default AuditQueue;
