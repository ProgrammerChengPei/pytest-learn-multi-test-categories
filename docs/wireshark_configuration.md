# Wireshark 抓包配置说明 / Wireshark Packet Capture Configuration

## 概述 / Overview

测试框架支持在测试执行时自动启动和停止 Wireshark 抓包，用于记录网络通信报文。
The test framework supports automatic Wireshark packet capture during test execution to record network communication packets.

## 配置 / Configuration

在 `configs/config.json` 中添加以下配置：
Add the following configuration in `configs/config.json`:

```json
{
  "wireshark": {
    "enabled": true,
    "interface": "以太网",
    "capture_filter": "port 8080",
    "wireshark_path": "C:\\Program Files\\Wireshark\\tshark.exe"
  }
}
```

### 配置说明 / Configuration Details

| 参数 / Parameter | 说明 / Description | 示例 / Example |
| --- | --- | --- |
| `enabled` | 是否启用抓包功能 / Whether to enable packet capture | `true` 或 `false` |
| `interface` | 网络接口名称 / Network interface name | `以太网`, `Wi-Fi`, `Ethernet0` |
| `capture_filter` | Wireshark 抓包过滤器 / Wireshark capture filter | `port 8080`, `host 192.168.1.100` |
| `wireshark_path` | tshark.exe 完整路径 / Full path to tshark.exe | `C:\\Program Files\\Wireshark\\tshark.exe` |

## 查找网络接口 / Finding Network Interface

### Windows 系统 / Windows System

运行以下命令查找网络接口名称：
Run the following command to find network interface names:

```cmd
tshark -D
```

输出示例 / Example output:
```
1. \Device\NPF_{12345678-1234-1234-1234-123456789012} (以太网)
2. \Device\NPF_{87654321-4321-4321-4321-210987654321} (Wi-Fi)
```

使用括号中的名称（如 `以太网`）作为 `interface` 值。
Use the name in parentheses (e.g., `以太网`) as the `interface` value.

## 常用抓包过滤器 / Common Capture Filters

| 过滤器 / Filter | 说明 / Description |
| --- | --- |
| `port 8080` | 抓取 8080 端口的所有流量 / Capture all traffic on port 8080 |
| `host 192.168.1.100` | 抓取与指定主机的所有通信 / Capture all communication with specified host |
| `tcp port 8080` | 抓取 8080 端口的 TCP 流量 / Capture TCP traffic on port 8080 |
| `udp port 8080` | 抓取 8080 端口的 UDP 流量 / Capture UDP traffic on port 8080 |
| `port 8080 or port 8081` | 抓取多个端口 / Capture multiple ports |

## 抓包文件位置 / Capture File Location

抓包文件自动保存到 `reports/` 目录，文件名格式：
Capture files are automatically saved to the `reports/` directory with filename format:

```
capture_YYYYMMDD_HHMMSS_test_name.pcap
```

示例 / Example:
```
capture_20260205_143025_test_flash_basic.pcap
capture_20260205_143028_test_api_get_status.pcap
```

## 使用说明 / Usage Instructions

1. 安装 Wireshark / Install Wireshark
   - 下载地址 / Download URL: https://www.wireshark.org/download.html
   - 安装时确保安装 tshark 命令行工具 / Ensure tshark command-line tool is installed during installation

2. 配置 config.json / Configure config.json
   - 设置 `enabled: true`
   - 配置正确的网络接口名称 / Configure the correct network interface name
   - 配置 tshark.exe 路径 / Configure tshark.exe path

3. 运行测试 / Run Tests
   ```bash
   pytest
   ```

4. 查看抓包文件 / View Capture Files
   - 使用 Wireshark GUI 打开 `.pcap` 文件
   - 或使用命令行：`tshark -r capture_file.pcap`

## 注意事项 / Notes

- 抓包功能仅在测试执行期间运行 / Packet capture only runs during test execution
- 每个测试都会生成独立的抓包文件 / Each test generates a separate capture file
- 如果 tshark 路径配置错误，测试仍然会运行，但不会抓包 / Tests still run if tshark path is incorrect, but no capture will occur
- 抓包文件可能较大，建议定期清理 `reports/` 目录 / Capture files can be large, consider cleaning `reports/` directory regularly

## 禁用抓包 / Disabling Capture

要禁用抓包功能，只需在 `config.json` 中设置：
To disable packet capture, simply set in `config.json`:

```json
{
  "wireshark": {
    "enabled": false
  }
}
```
