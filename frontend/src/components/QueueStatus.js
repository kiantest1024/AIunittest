import React, { useState, useEffect } from 'react';
import { Progress, Badge, Tooltip, Button, Space, Typography, Divider, Drawer } from 'antd';
import {
  ClockCircleOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  StopOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import './QueueStatus.css';

const { Text } = Typography;

const QueueStatus = ({ visible = true, refreshInterval = 2000 }) => {
  const [queueStatus, setQueueStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [drawerVisible, setDrawerVisible] = useState(false);

  // 获取队列状态
  const fetchQueueStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/queue/status');
      if (response.ok) {
        const data = await response.json();
        setQueueStatus(data);
        setError(null);
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (err) {
      console.error('Error fetching queue status:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 自动刷新
  useEffect(() => {
    if (!visible) return;

    fetchQueueStatus();
    const interval = setInterval(fetchQueueStatus, refreshInterval);
    
    return () => clearInterval(interval);
  }, [visible, refreshInterval]);

  // 手动刷新
  const handleRefresh = () => {
    fetchQueueStatus();
  };

  if (!visible) {
    return null;
  }

  // 如果没有队列状态，只显示简单的状态指示器
  if (!queueStatus) {
    return (
      <div
        className="queue-status-indicator"
        style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          zIndex: 1000,
          background: '#f0f0f0',
          padding: '8px 12px',
          borderRadius: '20px',
          fontSize: '12px',
          color: '#666',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}
      >
        <ClockCircleOutlined /> 队列状态加载中...
      </div>
    );
  }

  const {
    pending_tasks = 0,
    running_tasks = 0,
    ai_tasks_running = 0,
    max_concurrent = 3,
    max_ai_tasks = 2,
    active_streams = 0,
    stats = {},
    stream_details = []
  } = queueStatus;

  // 计算使用率
  const concurrentUsage = (running_tasks / max_concurrent) * 100;
  const aiUsage = (ai_tasks_running / max_ai_tasks) * 100;

  // 状态颜色
  const getStatusColor = (usage) => {
    if (usage >= 90) return '#ff4d4f'; // 红色
    if (usage >= 70) return '#faad14'; // 橙色
    if (usage >= 40) return '#1890ff'; // 蓝色
    return '#52c41a'; // 绿色
  };

  // 如果没有活动任务，显示简化的状态指示器
  if (running_tasks === 0 && pending_tasks === 0 && active_streams === 0) {
    return (
      <div
        className="queue-status-indicator"
        style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          zIndex: 1000,
          background: '#f6ffed',
          border: '1px solid #b7eb8f',
          padding: '8px 12px',
          borderRadius: '20px',
          fontSize: '12px',
          color: '#52c41a',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          cursor: 'pointer'
        }}
        onClick={() => setDrawerVisible(true)}
      >
        <CheckCircleOutlined /> 系统空闲
      </div>
    );
  }

  // 有活动任务时显示紧凑的状态栏
  return (
    <>
      {/* 紧凑状态栏 */}
      <div
        className="queue-status-compact"
        style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          zIndex: 1000,
          background: 'rgba(255, 255, 255, 0.95)',
          border: '1px solid #d9d9d9',
          padding: '8px 16px',
          borderRadius: '20px',
          fontSize: '12px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          cursor: 'pointer',
          backdropFilter: 'blur(10px)',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}
        onClick={() => setDrawerVisible(true)}
      >
        <Space size="small">
          {pending_tasks > 0 && (
            <Badge count={pending_tasks} color="#faad14" size="small">
              <ClockCircleOutlined style={{ color: '#faad14' }} />
            </Badge>
          )}

          {running_tasks > 0 && (
            <Badge count={running_tasks} color="#1890ff" size="small">
              <PlayCircleOutlined style={{ color: '#1890ff' }} />
            </Badge>
          )}

          {ai_tasks_running > 0 && (
            <Badge count={ai_tasks_running} color="#722ed1" size="small">
              <CheckCircleOutlined style={{ color: '#722ed1' }} />
            </Badge>
          )}

          <span style={{ color: '#666', marginLeft: '4px' }}>
            点击查看详情
          </span>
        </Space>
      </div>

      {/* 详细信息抽屉 */}
      <Drawer
        title={
          <Space>
            <PlayCircleOutlined />
            <span>任务队列状态</span>
            <Button
              type="text"
              size="small"
              icon={<ReloadOutlined />}
              loading={loading}
              onClick={handleRefresh}
            />
          </Space>
        }
        placement="right"
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
        width={360}
        bodyStyle={{ padding: '16px' }}
      >
      {error ? (
        <div style={{ color: '#ff4d4f', textAlign: 'center' }}>
          <ExclamationCircleOutlined /> 获取状态失败: {error}
        </div>
      ) : (
        <Space direction="vertical" style={{ width: '100%' }} size="small">
          {/* 队列概览 */}
          <div className="queue-overview">
            <Space wrap>
              <Tooltip title="等待中的任务">
                <Badge count={pending_tasks} color="#faad14">
                  <ClockCircleOutlined style={{ fontSize: '16px' }} />
                </Badge>
              </Tooltip>
              
              <Tooltip title="执行中的任务">
                <Badge count={running_tasks} color="#1890ff">
                  <PlayCircleOutlined style={{ fontSize: '16px' }} />
                </Badge>
              </Tooltip>
              
              <Tooltip title="AI生成任务">
                <Badge count={ai_tasks_running} color="#722ed1">
                  <CheckCircleOutlined style={{ fontSize: '16px' }} />
                </Badge>
              </Tooltip>
              
              <Tooltip title="活跃流">
                <Badge count={active_streams} color="#52c41a">
                  <StopOutlined style={{ fontSize: '16px' }} />
                </Badge>
              </Tooltip>
            </Space>
          </div>

          <Divider style={{ margin: '8px 0' }} />

          {/* 资源使用率 */}
          <div className="resource-usage">
            <div style={{ marginBottom: '8px' }}>
              <Text strong>并发任务使用率</Text>
              <Progress 
                percent={Math.round(concurrentUsage)}
                size="small"
                strokeColor={getStatusColor(concurrentUsage)}
                format={() => `${running_tasks}/${max_concurrent}`}
              />
            </div>
            
            <div style={{ marginBottom: '8px' }}>
              <Text strong>AI任务使用率</Text>
              <Progress 
                percent={Math.round(aiUsage)}
                size="small"
                strokeColor={getStatusColor(aiUsage)}
                format={() => `${ai_tasks_running}/${max_ai_tasks}`}
              />
            </div>
          </div>

          {/* 统计信息 */}
          {stats.total_tasks > 0 && (
            <>
              <Divider style={{ margin: '8px 0' }} />
              <div className="queue-stats">
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  总任务: {stats.total_tasks} | 
                  已完成: {stats.completed_tasks} | 
                  失败: {stats.failed_tasks}
                </Text>
                {stats.avg_wait_time > 0 && (
                  <div>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      平均等待: {stats.avg_wait_time.toFixed(1)}s | 
                      平均执行: {stats.avg_execution_time.toFixed(1)}s
                    </Text>
                  </div>
                )}
              </div>
            </>
          )}

          {/* 活跃流详情 */}
          {stream_details.length > 0 && (
            <>
              <Divider style={{ margin: '8px 0' }} />
              <div className="active-streams">
                <Text strong style={{ fontSize: '12px' }}>活跃生成任务:</Text>
                {stream_details.map((stream, index) => (
                  <div key={stream.task_id} style={{ marginTop: '4px' }}>
                    <Text style={{ fontSize: '11px' }}>
                      用户 {stream.user_id.substring(0, 8)}... 
                      ({stream.completed}/{stream.total})
                    </Text>
                    {stream.current && (
                      <div style={{ fontSize: '10px', color: '#666' }}>
                        当前: {stream.current}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </>
          )}

          {/* 性能提示 */}
          {(concurrentUsage >= 90 || aiUsage >= 90) && (
            <>
              <Divider style={{ margin: '8px 0' }} />
              <div className="performance-tip">
                <Text type="warning" style={{ fontSize: '11px' }}>
                  <ExclamationCircleOutlined /> 
                  系统负载较高，新任务可能需要等待
                </Text>
              </div>
            </>
          )}
        </Space>
      )}
      </Drawer>
    </>
  );
};

export default QueueStatus;
