import React, { useRef, useState } from 'react';
import {
  PageContainer, ProFormText, ProFormTextArea, ProFormSelect, ProFormDigit, ProFormDatePicker,
  ActionType, ProTable, ProColumns, ModalForm,
} from '@ant-design/pro-components';
import { Button, message, Popconfirm, Space, Tag } from 'antd';
import { PlusOutlined } from '@ant-design/icons';
import { createBasic, updateBasic, submitBasic, getPmList, PmProject, STATUS_LABEL } from '@/services/project/workflow';

const BasicPage: React.FC = () => {
  const actionRef = useRef<ActionType>();
  const [editing, setEditing] = useState<PmProject | null>(null);
  const [open, setOpen] = useState(false);

  const columns: ProColumns<PmProject>[] = [
    { title: '编号', dataIndex: 'projectCode', width: 150 },
    { title: '名称', dataIndex: 'projectName', ellipsis: true },
    { title: '类型', dataIndex: 'projectType', width: 90, search: false },
    { title: '负责人', dataIndex: 'owner', width: 90 },
    {
      title: '状态', dataIndex: 'status', width: 120, search: false,
      render: (_, row) => <Tag>{STATUS_LABEL[row.status || ''] || row.status}</Tag>,
    },
    { title: '更新时间', dataIndex: 'updatedAt', width: 160, search: false },
    {
      title: '操作', valueType: 'option', width: 220,
      render: (_, row) => (
        <Space>
          {row.status === 'draft' && (
            <>
              <a onClick={() => { setEditing(row); setOpen(true); }}>编辑</a>
              <Popconfirm title="提交一次审核?" onConfirm={async () => {
                const res = await submitBasic(row.id!);
                if (res.code === 200) { message.success('已提交一次审核'); actionRef.current?.reload(); }
                else { message.error(res.msg || '提交失败'); }
              }}>
                <a>提交审核</a>
              </Popconfirm>
            </>
          )}
        </Space>
      ),
    },
  ];

  return (
    <PageContainer header={{ title: '基础信息录入', subTitle: '经办岗 / 草稿保存后提交一次审核' }}>
      <ProTable<PmProject>
        headerTitle="我的立项草稿 / 基础信息"
        actionRef={actionRef}
        rowKey="id"
        columns={columns}
        toolBarRender={() => [
          <Button key="add" type="primary" icon={<PlusOutlined />} onClick={() => { setEditing(null); setOpen(true); }}>
            新建项目
          </Button>,
        ]}
        request={async (params) => {
          const res = await getPmList({
            keyword: params.projectName || params.projectCode || params.owner,
            pageNum: params.current,
            pageSize: params.pageSize,
          });
          const rows = (res.rows || []).filter((r) => r.status === 'draft' || r.status === 'pending_basic');
          return { data: rows, total: rows.length, success: res.code === 200 };
        }}
      />
      <ModalForm<PmProject>
        title={editing ? '编辑基础信息' : '新建基础信息'}
        open={open}
        modalProps={{ destroyOnClose: true, onCancel: () => setOpen(false) }}
        initialValues={editing || { projectType: '研发', budget: 0 }}
        onFinish={async (values) => {
          const payload = {
            ...values,
            id: editing?.id,
            startDate: values.startDate ? String(values.startDate).slice(0, 10) : values.startDate,
            endDate: values.endDate ? String(values.endDate).slice(0, 10) : values.endDate,
          };
          const res = editing ? await updateBasic(payload) : await createBasic(payload);
          if (res.code === 200) {
            message.success(editing ? '已保存' : '已创建草稿');
            setOpen(false);
            actionRef.current?.reload();
            return true;
          }
          message.error(res.msg || '保存失败');
          return false;
        }}
      >
        <ProFormText name="projectCode" label="项目编号" placeholder="可空 / auto" />
        <ProFormText name="projectName" label="项目名称" rules={[{ required: true, message: '请输入项目名称' }]} />
        <ProFormSelect name="projectType" label="项目类型" options={['研发', '实施', '运维', '预研', '其他'].map((v) => ({ label: v, value: v }))} />
        <ProFormText name="owner" label="负责人" />
        <ProFormText name="department" label="所属部门" />
        <ProFormDigit name="budget" label="预算(元)" min={0} fieldProps={{ precision: 2 }} />
        <ProFormDatePicker name="startDate" label="计划开始" fieldProps={{ format: 'YYYY-MM-DD' }} />
        <ProFormDatePicker name="endDate" label="计划结束" fieldProps={{ format: 'YYYY-MM-DD' }} />
        <ProFormTextArea name="description" label="项目概述" />
      </ModalForm>
    </PageContainer>
  );
};

export default BasicPage;
