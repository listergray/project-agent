import React, { useRef, useState } from 'react';
import {
  PageContainer, ProTable, ProColumns, ActionType, ModalForm, ProFormText, ProFormTextArea, ProFormSelect,
} from '@ant-design/pro-components';
import { Alert, Button, Space, Tag, message, Popconfirm } from 'antd';
import {
  getPmList, updateExtend, submitExtend, submitPurchase, PmProject, STATUS_LABEL,
} from '@/services/project/workflow';

const ExtendPage: React.FC = () => {
  const actionRef = useRef<ActionType>();
  const [editing, setEditing] = useState<PmProject | null>(null);
  const [open, setOpen] = useState(false);

  const columns: ProColumns<PmProject>[] = [
    { title: '编号', dataIndex: 'projectCode', width: 150 },
    { title: '名称', dataIndex: 'projectName', ellipsis: true },
    {
      title: '状态', dataIndex: 'status', width: 120, search: false,
      render: (_, row) => <Tag color="cyan">{STATUS_LABEL[row.status || ''] || row.status}</Tag>,
    },
    { title: '目标交付', dataIndex: 'goals', ellipsis: true, search: false },
    { title: '更新时间', dataIndex: 'updatedAt', width: 160, search: false },
    {
      title: '操作', valueType: 'option', width: 280,
      render: (_, row) => (
        <Space>
          {(row.status === 'basic_passed' || row.status === 'extend_passed') && (
            <a onClick={() => { setEditing(row); setOpen(true); }}>编辑扩展</a>
          )}
          {row.status === 'basic_passed' && (
            <Popconfirm title="提交二次审核?" onConfirm={async () => {
              const res = await submitExtend(row.id!);
              if (res.code === 200) { message.success('已提交二次审核'); actionRef.current?.reload(); }
              else { message.error(res.msg || 'fail'); }
            }}>
              <a>提交二次审</a>
            </Popconfirm>
          )}
          {row.status === 'extend_passed' && (
            <Popconfirm title="发起购买联审?" onConfirm={async () => {
              const res = await submitPurchase(row.id!);
              if (res.code === 200) { message.success('已发起购买联审'); actionRef.current?.reload(); }
              else { message.error(res.msg || 'fail'); }
            }}>
              <Button type="link" size="small">发起购买联审</Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <PageContainer header={{ title: '扩展信息录入', subTitle: '经办岗 / 一次审通过后方可填写' }}>
      <Alert type="info" showIcon style={{ marginBottom: 16 }} message="仅 basic_passed 可提交二次审; extend_passed 可发起购买联审" />
      <ProTable<PmProject>
        headerTitle="可填扩展 / 可发起联审"
        actionRef={actionRef}
        rowKey="id"
        columns={columns}
        request={async (params) => {
          const res = await getPmList({
            keyword: params.projectName || params.projectCode,
            pageNum: 1,
            pageSize: 100,
          });
          const rows = (res.rows || []).filter((r) =>
            r.status === 'basic_passed' || r.status === 'extend_passed' || r.status === 'pending_extend');
          return { data: rows, total: rows.length, success: res.code === 200 };
        }}
      />
      <ModalForm<PmProject>
        title="扩展信息"
        open={open}
        modalProps={{ destroyOnClose: true, onCancel: () => setOpen(false) }}
        initialValues={editing || {}}
        onFinish={async (values) => {
          const res = await updateExtend({ ...values, id: editing?.id });
          if (res.code === 200) {
            message.success('扩展信息已保存');
            setOpen(false);
            actionRef.current?.reload();
            return true;
          }
          message.error(res.msg || 'fail');
          return false;
        }}
      >
        <ProFormTextArea name="goals" label="目标与交付物" rules={[{ required: true }]} />
        <ProFormText name="members" label="核心成员" />
        <ProFormSelect name="riskLevel" label="风险等级" options={['低', '中', '高'].map((v) => ({ label: v, value: v }))} />
        <ProFormSelect name="priority" label="优先级" options={['P0', 'P1', 'P2'].map((v) => ({ label: v, value: v }))} />
        <ProFormTextArea name="purchasePlan" label="采购说明" />
        <ProFormTextArea name="financePlan" label="资金说明" />
      </ModalForm>
    </PageContainer>
  );
};

export default ExtendPage;
