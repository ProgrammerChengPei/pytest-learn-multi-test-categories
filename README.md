# Pytest-VIU-Design Test Framework / Pytest测试框架

嵌入式Pytest测试框架，支持接口、功能、性能测试，自动依赖管理和Excel报告生成。

Embedded Pytest test framework supporting interface, function, and performance testing with automatic dependency management and Excel report generation.

## Features / 特性

- ✅ **Test Dependency Management / 测试依赖管理**: Flash → Interface → Function → Performance
- ✅ **Excel Report Generation / Excel报告生成**: 自动生成详细的Excel测试报告
- ✅ **Multiple Test Types / 多种测试类型**: Flash刷写、Interface接口、Function功能、Performance性能
- ✅ **Test Coverage / 测试覆盖率**: 支持代码覆盖率测试
- ✅ **Parallel Execution / 并行执行**: 支持多线程并行测试
- ✅ **HTML Report / HTML报告**: 生成HTML格式的测试报告

## Project Structure / 项目结构

```
pytest-viu-design/
├── src/                          # Source code / 源代码
│   ├── client.py                # TCP客户端 / TCP Client
│   ├── server.py                # TCP服务器 / TCP Server
│   ├── log.py                   # 日志配置 / Logging config
│   ├── excel_report.py          # Excel报告生成器 / Excel report generator
│   └── pytest_excel_report.py   # Pytest插件 / Pytest plugin
├── tests/                       # Test files / 测试文件
│   ├── conftest.py             # 全局配置 / Global configuration
│   ├── common/                  # 公共工具 / Common utilities
│   ├── flash_tests/            # 刷写测试 / Flash tests
│   ├── interface_tests/        # 接口测试 / Interface tests
│   ├── function_tests/         # 功能测试 / Function tests
│   └── performance_tests/      # 性能测试 / Performance tests
├── configs/                    # 配置文件 / Configuration files
├── docs/                       # 文档 / Documentation
└── requirements.txt            # Python依赖 / Python dependencies
```

## Test Dependency Chain / 测试依赖链

测试严格按照以下顺序执行（每个阶段的测试依赖于前一阶段通过）：

Tests are executed in strict order (each phase depends on the previous phase passing):

```
Flash Test (刷写测试)
    ↓
Interface Test (接口测试)
    ↓
Function Test (功能测试)
    ↓
Performance Test (性能测试)
```

### Dependency Implementation / 依赖实现方式

使用 **pytest-dependency** 插件实现测试依赖：

```python
@pytest.mark.flash
@pytest.mark.dependency(name="test_flash_complete")
def test_flash_complete(test_state):
    """Flash test / 刷写测试"""
    test_state.mark_flash_passed()

@pytest.mark.interface
@pytest.mark.dependency(name="test_interface_test", depends=["test_flash_complete"])
def test_interface_test(test_state, flash_test_passed):
    """Interface test depends on flash / 接口测试依赖刷写"""
    if not flash_test_passed:
        pytest.skip("Flash test has not passed yet")
```

## Installation / 安装

```bash
# Clone repository / 克隆仓库
git clone <repository-url>
cd pytest-viu-design

# Install dependencies / 安装依赖
pip install -r requirements.txt
```

### Required Dependencies / 必需依赖

- `pytest>=8.0.0` - Core testing framework / 核心测试框架
- `pytest-dependency>=0.6.0` - Test dependency management / 测试依赖管理
- `pytest-html>=4.0.0` - HTML report generation / HTML报告生成
- `openpyxl>=3.1.0` - Excel report generation / Excel报告生成
- `pytest-cov>=5.0.0` - Coverage testing / 覆盖率测试

## Usage / 使用方法

### 1. Run All Tests / 运行所有测试

```bash
# Using pytest directly / 直接使用pytest
pytest tests/ -v

# Using the test runner script / 使用测试运行脚本
python run_tests.py --type all
```

### 2. Run Specific Test Types / 运行特定测试类型

```bash
# Run flash tests only / 仅运行刷写测试
python run_tests.py --type flash

# Run interface tests only / 仅运行接口测试
python run_tests.py --type interface

# Run function tests only / 仅运行功能测试
python run_tests.py --type function

# Run performance tests only / 仅运行性能测试
python run_tests.py --type performance
```

### 3. Run with Coverage / 运行覆盖率测试

```bash
# Run all tests with coverage report / 运行所有测试并生成覆盖率报告
python run_tests.py --type all --coverage

# Set coverage threshold / 设置覆盖率阈值
python run_tests.py --type all --coverage --coverage-threshold 95
```

### 4. Run Tests in Parallel / 并行运行测试

```bash
# Run with 4 workers / 使用4个worker并行运行
python run_tests.py --type all --parallel --workers 4
```

### 5. Direct Pytest Commands / 直接使用Pytest命令

```bash
# Run all tests / 运行所有测试
pytest tests/ -v

# Run specific test category / 运行特定测试类别
pytest tests/ -v -m flash
pytest tests/ -v -m interface
pytest tests/ -v -m function
pytest tests/ -v -m performance

# Run with coverage / 运行并生成覆盖率
pytest tests/ --cov=src --cov-report=html --cov-report=term-missing

# Run in parallel / 并行运行
pytest tests/ -n 4
```

## Test Artifacts / 测试产物

测试运行后会生成以下文件：

The following files will be generated after test run:

```
test_artifacts/
├── pytest.log                    # Pytest日志 / Pytest log
├── pytest_report.html           # HTML报告 / HTML report
├── pytest_report.xlsx           # Excel报告 / Excel report
├── flash_test_result.json        # 刷写测试结果 / Flash test result
├── interface_test_result.json   # 接口测试结果 / Interface test result
├── function_test_result.json    # 功能测试结果 / Function test result
└── performance_test_result.json  # 性能测试结果 / Performance test result
```

## Excel Report Structure / Excel报告结构

生成的Excel报告包含以下工作表：

The generated Excel report contains the following sheets:

1. **测试汇总 / Summary** - 整体测试统计信息 / Overall test statistics
2. **刷写测试 / Flash** - 刷写测试详细结果 / Flash test details
3. **接口测试 / Interface** - 接口测试详细结果 / Interface test details
4. **功能测试 / Function** - 功能测试详细结果 / Function test details
5. **性能测试 / Performance** - 性能测试详细结果 / Performance test details

### Report Features / 报告特性

- 📊 统计图表 / Statistical charts
- 🎨 彩色状态标记 / Color-coded status markers
- ⏱️ 耗时统计 / Duration statistics
- ✅ 通过/失败统计 / Pass/Fail statistics
- 🔍 详细的错误信息 / Detailed error messages

## Test Categories / 测试类别

### 1. Flash Tests / 刷写测试

测试固件刷写功能 / Test firmware flashing functionality:

- 连接测试 / Connection test
- 准备测试 / Preparation test
- 上传测试 / Upload test
- 验证测试 / Verification test
- 完成测试 / Completion test

### 2. Interface Tests / 接口测试

测试系统接口 / Test system interfaces:

- get_status接口 / get_status interface
- health_check接口 / health_check interface
- echo_with_timestamp接口 / echo_with_timestamp interface
- 批量请求测试 / Batch request test
- 延迟测试 / Latency test

### 3. Function Tests / 功能测试

测试系统功能 / Test system functionality:

- 连接生命周期 / Connection lifecycle
- 消息排序 / Message sequencing
- 错误恢复 / Error recovery
- 数据完整性 / Data integrity
- 多客户端 / Multiple clients

### 4. Performance Tests / 性能测试

测试系统性能 / Test system performance:

- 延迟性能 / Latency performance
- 吞吐量性能 / Throughput performance
- 并发性能 / Concurrent performance
- 压力测试 / Stress test

## Configuration / 配置

### pytest.ini / pytest配置文件

```ini
[pytest]
testpaths = tests
markers =
    flash: Flash/Firmware tests
    interface: Interface tests
    function: Function tests
    performance: Performance tests
```

### Server Configuration / 服务器配置

Edit `configs/config.json`:

```json
{
  "host": "localhost",
  "port": 8080,
  "max_connections": 100,
  "heartbeat_interval": 7,
  "token": "your-secure-token-here",
  "server_timeout": 7.0,
  "client_timeout": 10.0
}
```

## Creating New Tests / 创建新测试

### 1. Flash Test Example / 刷写测试示例

```python
import pytest

class TestFlash:
    @pytest.mark.flash
    @pytest.mark.dependency(name="test_new_flash_test", depends=["test_flash_complete"])
    def test_new_flash_test(self, test_state, test_client):
        """Your flash test here / 你的刷写测试"""
        assert True
```

### 2. Interface Test Example / 接口测试示例

```python
import pytest

class TestInterface:
    @pytest.mark.interface
    @pytest.mark.dependency(name="test_new_interface", depends=["test_interface_complete"])
    def test_new_interface(self, test_state, test_client):
        """Your interface test here / 你的接口测试"""
        assert True
```

### 3. Function Test Example / 功能测试示例

```python
import pytest

class TestFunction:
    @pytest.mark.function
    @pytest.mark.dependency(name="test_new_function", depends=["test_function_complete"])
    def test_new_function(self, test_state, test_client):
        """Your function test here / 你的功能测试"""
        assert True
```

### 4. Performance Test Example / 性能测试示例

```python
import pytest

class TestPerformance:
    @pytest.mark.performance
    @pytest.mark.dependency(name="test_new_performance", depends=["test_performance_complete"])
    def test_new_performance(self, test_state, test_client):
        """Your performance test here / 你的性能测试"""
        assert True
```

## Troubleshooting / 故障排除

### Import Errors / 导入错误

```bash
# Ensure you've installed all dependencies / 确保已安装所有依赖
pip install -r requirements.txt
```

### Server Connection Failed / 服务器连接失败

```bash
# Start the server first / 先启动服务器
python src/server.py
```

### Excel Report Not Generated / Excel报告未生成

```bash
# Install openpyxl / 安装openpyxl
pip install openpyxl
```

## License / 许可证

[Your License Here]

## Contact / 联系

[Your Contact Information]
