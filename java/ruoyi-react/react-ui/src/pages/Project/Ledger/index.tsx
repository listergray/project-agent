import React, { useEffect, useMemo, useRef, useState } from 'react';
import { PageContainer, ProColumns, ProTable, ActionType } from '@ant-design/pro-components';
import { Drawer, Steps, Tag, Timeline, Typography, Statistic, Row, Col, Card, Space, Tooltip } from 'antd';
import {
  getPmList, getPmStats, getPm, PmProject, STATUS_LABEL, PIPELINE_STEPS, statusToStepIndex,
} from '@/services/project/workflow';
import './index.less';

const statusColor = (status?: string) => {
  switch (status) {
    case 'draft': return 'default';
    case 'pending_basic':
    case 'pending_extend':
    case 'pending_purchase':
    case 'pending_finance': return 'processing';
    case 'basic_passed':
    case 'extend_passed': return 'cyan';
    case 'approved': return 'success';
    default: return 'default';
  }
};

const PipelineCell: React.FC<{ status?: string }> = ({ status }) => {
  const idx = statusToStepIndex(status);
  const finished = idx >= PIPELINE_STEPS.length;
  const current = Math.min(idx, PIPELINE_STEPS.length - 1);
  const label = finished ? '已立项通过' : PIPELINE_STEPS[current]?.title;
  return (
    <div className="pm-pipeline">
      <div className="pm-pipeline-track">
        {PIPELINE_STEPS.map((step, i) => {
          const state = finished || idx > i ? 'finish' : idx === i ? 'process' : 'wait';
          return (
            <React.Fragment key={step.key}>
              {i > 0 && <span className={`pm-pipeline-line ${finished || idx > i ? 'on' : ''}`} />}
              <Tooltip title={step.title}>
                <span className={`pm-pipeline-dot ${state}`}>
                  {state === 'finish' ? '✓' : i + 1}
                </span>
              </Tooltip>
            </React.Fragment>
          );
        })}
      </div>
      <span className="pm-pipeline-label">{label}</span>
    </div>
  );
};

const LedgerPage: React.FC = () => {
  const actionRef = useRef<ActionType>();
  const [stats, setStats] = useState<Record<string, number>>({});
  const [detail, setDetail] = useState<PmProject | null>(null);
  const [open, setOpen] = useState(false);

  const loadStats = async () => {
    const res = await getPmStats();
    if (res.code === 200) setStats(res.data || {});
  };

  useEffect(() => { loadStats(); }, []);

  const columns: ProColumns<PmProject>[] = useMemo(() => [
    { title: '项目编号', dataIndex: 'projectCode', width: 150, copyable: true },
    {
      title: '项目名称',
      dataIndex: 'projectName',
      ellipsis: true,
      render: (_, row) => (
        <a onClick={async () => {
          const res = await getPm(row.id!);
          if (res.code === 200) { setDetail(res.data); setOpen(true); }
        }}>{row.projectName}</a>
      ),
    },
    { title: '类型', dataIndex: 'projectType', width: 90, search: false },
    { title: '负责人', dataIndex: 'owner', width: 90 },
    { title: '部门', dataIndex: 'department', width: 110, search: false },
    { title: '预算(元)', dataIndex: 'budget', width: 110, search: false },
    {
      title: '状态',
      dataIndex: 'status',
      width: 120,
      valueType: 'select',
      valueEnum: Object.fromEntries(Object.entries(STATUS_LABEL).map(([k, v]) => [k, { text: v }])),
      render: (_, row) => <Tag color={statusColor(row.status)}>{STATUS_LABEL[row.status || ''] || row.status}</Tag>,
    },
    {
      title: '流水线',
      dataIndex: 'pipeline',
      search: false,
      width: 280,
      render: (_, row) => <PipelineCell status={row.status} />,
    },
    { title: '更新时间', dataIndex: 'updatedAt', width: 160, search: false },
  ], []);

  return (
    <PageContainer header={{ title: '项目台账', subTitle: '全国公用立项流水线 / 分岗联审' }}>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        {[
          { key: 'total', title: '全部' },
          { key: 'pending_basic', title: '待一次审核' },
          { key: 'pending_extend', title: '待二次审核' },
          { key: 'pending_purchase', title: '购买联审' },
          { key: 'pending_finance', title: '财务联审' },
          { key: 'approved', title: '已通过' },
        ].map((item) => (
          <Col key={item.key} xs={12} sm={8} md={4}>
            <Card size="small"><Statistic title={item.title} value={stats[item.key] || 0} /></Card>
          </Col>
        ))}
      </Row>
      <ProTable<PmProject>
        headerTitle="立项项目"
        actionRef={actionRef}
        rowKey="id"
        columns={columns}
        search={{ labelWidth: 'auto' }}
        request={async (params) => {
          const res = await getPmList({
            status: params.status,
            keyword: params.projectName || params.projectCode || params.owner,
            pageNum: params.current,
            pageSize: params.pageSize,
          });
          loadStats();
          return { data: res.rows || [], total: res.total || 0, success: res.code === 200 };
        }}
        pagination={{ defaultPageSize: 10 }}
      />
      <Drawer width={560} title={detail?.projectName || '项目详情'} open={open} onClose={() => setOpen(false)} destroyOnClose>
        {detail && (
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            <div>
              <Tag color={statusColor(detail.status)}>{STATUS_LABEL[detail.status || '']}</Tag>
              <Typography.Text type="secondary" style={{ marginLeft: 8 }}>{detail.projectCode}</Typography.Text>
            </div>
            <Steps direction="vertical" size="small" current={Math.min(statusToStepIndex(detail.status), 5)} items={PIPELINE_STEPS.map((s) => ({ title: s.title }))} />
            <Typography.Paragraph>
              <strong>负责人:</strong>{detail.owner || '-'} <strong>部门:</strong>{detail.department || '-'}
              <br /><strong>预算(元):</strong>{detail.budget ?? '-'} <strong>类型:</strong>{detail.projectType || '-'}
              <br /><strong>概述:</strong>{detail.description || '-'}
              <br /><strong>目标交付:</strong>{detail.goals || '-'}
              <br /><strong>采购说明:</strong>{detail.purchasePlan || '-'}
              <br /><strong>资金说明:</strong>{detail.financePlan || '-'}
            </Typography.Paragraph>
            <Typography.Title level={5}>流转历史</Typography.Title>
            <Timeline items={(detail.history || []).slice().reverse().map((h) => ({
              children: (
                <div>
                  <div>{h.action} / {h.by}{h.role ? ` (${h.role})` : ''}</div>
                  <Typography.Text type="secondary">{h.at} {h.note ? `/ ${h.note}` : ''}</Typography.Text>
                </div>
              ),
            }))} />
          </Space>
        )}
      </Drawer>
    </PageContainer>
  );
};

export default LedgerPage;
