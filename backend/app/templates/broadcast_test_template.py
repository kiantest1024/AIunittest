"""
broadcast.py 测试模板

此文件包含针对 broadcast.py 文件的测试模板，可以直接运行。
"""

import pytest
from unittest import mock
from datetime import datetime

# 导入被测函数
from broadcast import init_socketio, broadcast_metrics, broadcast_test_status, socketio

# ===== 测试夹具 =====

@pytest.fixture
def reset_socketio():
    """测试前后重置 socketio 全局变量"""
    original_socketio = globals()['socketio']
    yield
    globals()['socketio'] = original_socketio

@pytest.fixture
def mock_socketio():
    """模拟 socketio 对象"""
    with mock.patch('broadcast.socketio') as mock_socket:
        yield mock_socket

# ===== init_socketio 函数测试 =====

def test_init_socketio_basic(reset_socketio):
    """基本测试 init_socketio 函数"""
    # 准备测试数据
    mock_socketio_obj = mock.MagicMock()
    
    # 调用函数
    init_socketio(mock_socketio_obj)
    
    # 验证结果
    assert globals()['socketio'] is mock_socketio_obj

def test_init_socketio_with_none(reset_socketio):
    """测试传入 None 值"""
    # 调用函数
    init_socketio(None)
    
    # 验证结果
    assert globals()['socketio'] is None

# ===== broadcast_metrics 函数测试 =====

def test_broadcast_metrics_basic(mock_socketio):
    """基本测试 broadcast_metrics 函数"""
    # 准备测试数据
    test_data = {
        'test_id': 'test123',
        'metrics': {
            'vus': 10,
            'rps': 100,
            'response_time': 50,
            'error_rate': 0.1,
            'total_requests': 1000,
            'failed_requests': 10
        },
        'progress': 50,
        'status': 'running'
    }
    
    # 调用函数
    broadcast_metrics(test_data)
    
    # 验证结果
    mock_socketio.emit.assert_called_once_with('test_metrics', test_data)
    assert 'timestamp' in test_data

def test_broadcast_metrics_missing_test_id(mock_socketio, capsys):
    """测试缺少 test_id 的情况"""
    # 准备测试数据
    test_data = {
        'metrics': {}
    }
    
    # 调用函数
    broadcast_metrics(test_data)
    
    # 验证结果
    captured = capsys.readouterr()
    assert "test_id" in captured.out
    mock_socketio.emit.assert_not_called()

def test_broadcast_metrics_missing_metrics(mock_socketio):
    """测试缺少 metrics 字段的情况"""
    # 准备测试数据
    test_data = {
        'test_id': 'test123'
    }
    
    # 调用函数
    broadcast_metrics(test_data)
    
    # 验证结果
    assert 'metrics' in test_data
    assert isinstance(test_data['metrics'], dict)

def test_broadcast_metrics_no_socketio(capsys):
    """测试 socketio 未初始化的情况"""
    # 准备测试数据
    test_data = {'test_id': 'test123'}
    
    # 临时将 socketio 设为 None
    original_socketio = globals()['socketio']
    globals()['socketio'] = None
    
    try:
        # 调用函数
        broadcast_metrics(test_data)
        
        # 验证结果
        captured = capsys.readouterr()
        assert "socketio未初始化" in captured.out
    finally:
        # 恢复原始值
        globals()['socketio'] = original_socketio

def test_broadcast_metrics_exception_handling(mock_socketio, capsys):
    """测试异常处理情况"""
    # 准备测试数据
    test_data = {'test_id': 'test123'}
    mock_socketio.emit.side_effect = Exception("Test error")
    
    # 调用函数
    broadcast_metrics(test_data)
    
    # 验证结果
    captured = capsys.readouterr()
    assert "Test error" in captured.out

# ===== broadcast_test_status 函数测试 =====

def test_broadcast_test_status_basic(mock_socketio):
    """基本测试 broadcast_test_status 函数"""
    # 准备测试数据
    test_id = "test123"
    status = "running"
    message = "Test is running"
    
    # 调用函数
    broadcast_test_status(test_id, status, message)
    
    # 验证结果
    mock_socketio.emit.assert_called()
    call_args = mock_socketio.emit.call_args[0]
    assert call_args[0] == 'test_status'
    assert call_args[1]['test_id'] == test_id
    assert call_args[1]['status'] == status
    assert call_args[1]['message'] == message

def test_broadcast_test_status_without_message(mock_socketio):
    """测试不带消息的情况"""
    # 准备测试数据
    test_id = "test123"
    status = "running"
    
    # 调用函数
    broadcast_test_status(test_id, status)
    
    # 验证结果
    mock_socketio.emit.assert_called()
    call_args = mock_socketio.emit.call_args[0]
    assert call_args[0] == 'test_status'
    assert call_args[1]['test_id'] == test_id
    assert call_args[1]['status'] == status
    assert 'message' not in call_args[1]

def test_broadcast_test_status_final_status(mock_socketio):
    """测试最终状态的情况"""
    # 准备测试数据
    test_id = "test123"
    
    for status in ['completed', 'stopped', 'failed']:
        mock_socketio.reset_mock()
        
        # 调用函数
        broadcast_test_status(test_id, status)
        
        # 验证结果
        assert mock_socketio.emit.call_count == 2
        
        # 验证第二次调用是进度更新
        second_call_args = mock_socketio.emit.call_args_list[1][0]
        assert second_call_args[0] == 'test_metrics'
        assert second_call_args[1]['test_id'] == test_id
        assert second_call_args[1]['progress'] == 100
        assert second_call_args[1]['status'] == status

def test_broadcast_test_status_no_socketio(capsys):
    """测试 socketio 未初始化的情况"""
    # 准备测试数据
    test_id = "test123"
    status = "running"
    
    # 临时将 socketio 设为 None
    original_socketio = globals()['socketio']
    globals()['socketio'] = None
    
    try:
        # 调用函数
        broadcast_test_status(test_id, status)
        
        # 验证结果
        captured = capsys.readouterr()
        assert "socketio未初始化" in captured.out
    finally:
        # 恢复原始值
        globals()['socketio'] = original_socketio
