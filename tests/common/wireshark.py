



import json5
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import pytest

class WiresharkManager:
    """
    Wireshark packet capture manager / Wireshark 抓包管理器

    Manages tshark process for capturing network packets during test execution.
    管理测试执行期间的 tshark 抓包进程。
    """

    def __init__(self, config: Dict[str, Any], reports_dir: Path):
        """
        Initialize Wireshark manager / 初始化 Wireshark 管理器

        Args:
            config: Test configuration dictionary / 测试配置字典
            reports_dir: Directory to save capture files / 保存抓包文件的目录
        """
        self.config = config
        self.reports_dir = reports_dir
        self.wireshark_config = config.get('wireshark', {})
        self.enabled = self.wireshark_config.get('enabled', False)
        self.tshark_path = self.wireshark_config.get('wireshark_path', '')
        self.interface = self.wireshark_config.get('interface', '')
        self.capture_filter = self.wireshark_config.get('capture_filter', '')
        self.process: Optional[subprocess.Popen] = None
        self.capture_file: Optional[Path] = None

    def start_capture(self, test_name: str = None) -> Optional[Path]:
        """
        Start packet capture / 开始抓包

        Args:
            test_name: Optional test name for filename / 测试名称（用于文件名）

        Returns:
            Path to capture file if successful, None otherwise
            成功返回抓包文件路径，失败返回None
        """
        if not self.enabled:
            return None

        # Check if tshark exists / 检查 tshark 是否存在
        if not os.path.exists(self.tshark_path):
            print(f"  [Wireshark] tshark not found at: {self.tshark_path}")
            return None

        try:
            # Generate capture filename with timestamp
            # 生成带时间戳的抓包文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            test_suffix = f"_{test_name}" if test_name else ""
            self.capture_file = self.reports_dir / f"capture_{timestamp}{test_suffix}.pcap"

            # Build tshark command
            # 构建 tshark 命令
            cmd = [
                self.tshark_path,
                '-i', self.interface,
                '-f', self.capture_filter,
                '-w', str(self.capture_file)
            ]

            # Start tshark process
            # 启动 tshark 进程
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )

            print(f"  [Wireshark] Started capture: {self.capture_file.name}")
            return self.capture_file

        except Exception as e:
            print(f"  [Wireshark] Failed to start capture: {e}")
            return None

    def stop_capture(self) -> Optional[Path]:
        """
        Stop packet capture / 停止抓包

        Returns:
            Path to capture file if exists, None otherwise
            存在则返回抓包文件路径，否则返回None
        """
        if not self.process:
            return None

        try:
            # Terminate tshark process
            # 终止 tshark 进程
            self.process.terminate()

            # Wait for process to finish (max 5 seconds)
            # 等待进程结束（最多5秒）
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()

            print(f"  [Wireshark] Stopped capture: {self.capture_file.name if self.capture_file else 'unknown'}")

            result = self.capture_file
            self.process = None
            self.capture_file = None
            return result

        except Exception as e:
            print(f"  [Wireshark] Failed to stop capture: {e}")
            return None

    def is_running(self) -> bool:
        """Check if capture is running / 检查抓包是否正在运行"""
        return self.process is not None and self.process.poll() is None

    def cleanup(self):
        """Clean up resources / 清理资源"""
        if self.is_running():
            self.stop_capture()
