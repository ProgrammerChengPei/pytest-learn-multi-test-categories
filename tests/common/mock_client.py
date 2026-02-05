

import json5
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

class MockClient:
    """
    Mock client for testing / 测试用模拟客户端

    Simulates real client behavior including connection management,
    timeout handling, and activity tracking.
    模拟真实客户端行为，包括连接管理、超时处理和活动跟踪。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize mock client / 初始化模拟客户端

        Args:
            config: Test configuration dictionary / 测试配置字典
        """
        # Connection properties / 连接属性
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 8080)
        self.token = config.get('token', 'your-secure-token-here')
        self.timeout = config.get('server_timeout', 5.0)

        # Connection state / 连接状态
        self._connected = True
        self._last_activity = time.time()
        self._idle_timeout = config.get('client_timeout', 10.0)

        # Response simulation / 响应模拟
        self._mock_responses: Dict[str, Any] = {
            'get_status': {'type': 'response', 'status': 'ok', 'server_time': time.time(), 'connections': 1},
            'health_check': {'type': 'response', 'status': 'healthy'},
            'echo_with_timestamp': lambda req: self._create_echo_response(req)
        }

        # Request ID counter / 请求ID计数器
        self._request_id = 0

    def send(self, request: Dict[str, Any]) -> bool:
        """
        Send request and track activity / 发送请求并跟踪活动

        Args:
            request: Request dictionary / 请求字典

        Returns:
            True if send was successful / 发送成功返回True
        """
        if not self._connected:
            return False
        self._last_activity = time.time()
        return True

    def _create_echo_response(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Create echo response for echo_with_timestamp command / 创建echo响应"""
        return {
            'type': 'response',
            'id': request.get('id', self._increment_request_id()),
            'status': 'ok',
            'original_text': request.get('text', ''),
            'server_response': 'Echo: ' + request.get('text', ''),
            'server_timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }

    def _increment_request_id(self) -> int:
        """Increment and return request ID / 增加并返回请求ID"""
        self._request_id += 1
        return self._request_id

    def get_mock_response(self, command: str, request: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Get mock response for a command / 获取命令的模拟响应

        Args:
            command: Command name / 命令名称
            request: Original request (for lambda responses) / 原始请求（用于lambda响应）

        Returns:
            Mock response dictionary with id field / 包含id字段的模拟响应字典
        """
        response = self._mock_responses.get(command, {})
        if callable(response):
            return response(request)

        # Add id field to static responses
        if isinstance(response, dict) and 'id' not in response:
            response = response.copy()
            response['id'] = self._increment_request_id()

        return response

    def receive(self, timeout: float = None) -> Dict[str, Any]:
        """
        Receive response with timeout check / 接收响应并检查超时

        Note: This is kept for API compatibility, but actual responses
        are generated via get_mock_response in test helpers.
        注意: 保留此方法用于API兼容，但实际响应通过测试辅助函数中的get_mock_response生成。

        Args:
            timeout: Timeout in seconds / 超时时间(秒)

        Returns:
            Response dictionary / 响应字典

        Raises:
            ConnectionError: If client is not connected / 如果客户端未连接
            TimeoutError: If idle timeout exceeded / 如果超过空闲超时
        """
        if not self._connected:
            raise ConnectionError("Client not connected")

        elapsed = time.time() - self._last_activity
        if elapsed > self._idle_timeout:
            self._connected = False
            raise TimeoutError(f"Connection timed out after {elapsed:.1f}s idle")

        self._last_activity = time.time()
        return {"status": "ok", "timestamp": time.time()}

    def simulate_timeout(self, idle_duration: float = None) -> None:
        """
        Simulate idle timeout / 模拟空闲超时

        Args:
            idle_duration: Idle duration in seconds (default: exceeds timeout)
            idle_duration: 空闲时长（秒，默认：超过超时时间）
        """
        if idle_duration is None:
            idle_duration = self._idle_timeout + 1

        self._last_activity = time.time() - idle_duration
        elapsed = time.time() - self._last_activity

        if elapsed > self._idle_timeout:
            print(f"  → Idle timeout detected: {elapsed:.1f}s > {self._idle_timeout}s")
            self._connected = False
        else:
            print(f"  → Idle duration: {elapsed:.1f}s, within limit")

    def reconnect(self) -> None:
        """Simulate reconnection / 模拟重连"""
        time.sleep(0.1)
        self._connected = True
        self._last_activity = time.time()

    def close(self) -> None:
        """Close connection / 关闭连接"""
        self._connected = False

    @property
    def connected(self) -> bool:
        """
        Check if client is connected / 检查客户端是否已连接

        Auto-disconnects if idle timeout exceeded.
        如果超过空闲超时时间则自动断连。
        """
        if self._connected and (time.time() - self._last_activity > self._idle_timeout):
            self._connected = False
        return self._connected

    @connected.setter
    def connected(self, value: bool) -> None:
        """Set connection status / 设置连接状态"""
        self._connected = value
        if value:
            self._last_activity = time.time()
