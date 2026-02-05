# pytest-learn-multi-test-categories

Learn pytest by complex test project of multi test categories. / 通过一个混合了多个测试类别的复杂测试工程，学习pytest测试框架。

嵌入式Pytest测试框架，支持接口、功能、性能测试，**完全基于钩子的自动化**依赖管理和Excel报告生成。

Embedded Pytest test framework supporting interface, function, and performance testing with **hook-based automation** for dependency management and Excel report generation.

## Features / 特性

- ✅ **Hook-based Automation / 钩子驱动自动化**: 所有报告和依赖管理通过钩子自动完成
- ✅ **Zero Configuration / 零配置**: 测试代码只需添加marker，无需手动管理
- ✅ **Auto Excel Report / 自动Excel报告**: 自动生成详细的Excel测试报告
- ✅ **Auto Dependency / 自动依赖管理**: Flash → Interface → Function → Performance自动依赖
- ✅ **Auto State Management / 自动状态管理**: 自动更新测试完成状态
- ✅ **Auto Result Collection / 自动结果收集**: 自动收集测试结果到报告
- ✅ **Multiple Test Types / 多种测试类型**: Flash刷写、Interface接口、Function功能、Performance性能
- ✅ **Code Reduction / 代码减少**: 测试代码量减少约80%

## Project Structure / 项目结构

```
pytest-learn-multi-test-categories/
├── src/                              # Source code / 源代码
│   ├── client.py                    # TCP客户端 / TCP Client
│   ├── server.py                    # TCP服务器 / TCP Server
│   ├── log.py                       # 日志配置 / Logging config
│   ├── excel_report.py              # Excel报告生成器 / Excel report generator
│   └── template_based_report.py    # 基于模板的报告生成器 / Template-based report generator
├── tests/                           # Test files / 测试文件
│   ├── conftest.py                 # 全局配置和钩子 / Global config and hooks
│   ├── flash_tests/                # 刷写测试 / Flash tests
│   │   ├── conftest.py           # 刷写测试配置 / Flash test config
│   │   ├── test_flash1.py        # 刷写测试用例 / Flash test cases
│   │   └── common/              # 刷写测试辅助模块 / Flash test utilities
│   ├── interface_tests/            # 接口测试 / Interface tests
│   │   ├── conftest.py           # 接口测试配置 / Interface test config
│   │   ├── test_api1.py         # 接口测试用例 / Interface test cases
│   │   └── common/              # 接口测试辅助模块 / Interface test utilities
│   │       └── interface_common1.py
│   ├── function_tests/             # 功能测试 / Function tests
│   │   ├── conftest.py           # 功能测试配置 / Function test config
│   │   ├── test_func1.py        # 功能测试用例 / Function test cases
│   │   └── common/              # 功能测试辅助模块 / Function test utilities
│   │       └── function_common1.py
│   └── performance_tests/         # 性能测试 / Performance tests
│       ├── conftest.py           # 性能测试配置 / Performance test config
│       ├── test_perf1.py        # 性能测试用例 / Performance test cases
│       └── common/              # 性能测试辅助模块 / Performance test utilities
│           └── performance_common1.py
├── reports/                        # 测试报告目录 / Test reports directory (自动生成)
├── templates/                      # Excel模板目录 / Excel templates directory
│   └── test_report_template.xlsx   # Excel报告模板 / Excel report template
├── configs/                        # 配置文件 / Configuration files
│   ├── config.json                # 测试配置 / Test configuration
│   └── report_config.json         # 报告配置 / Report configuration
├── scripts/                        # 脚本文件 / Script files
│   └── create_template.py         # 模板生成脚本 / Template generator script
├── pyproject.toml                  # Pytest配置文件 / Pytest configuration file
└── requirements.txt                # Python依赖 / Python dependencies
```

## Test Dependency Chain / 测试依赖链

测试严格按照以下顺序执行（每个阶段的测试依赖于前一阶段通过），**完全由钩子自动管理**：

Tests are executed in strict order (each phase depends on the previous phase passing), **fully automated by hooks**:

```
Flash Test (刷写测试)
    ↓ (自动依赖 / Auto dependency)
Interface Test (接口测试)
    ↓ (自动依赖 / Auto dependency)
Function Test (功能测试)
    ↓ (自动依赖 / Auto dependency)
Performance Test (性能测试)
```

### Hook-based Automation / 基于钩子的自动化

**传统方式需要在每个测试上添加装饰器：**

```python
# ❌ 传统方式 - 需要手动添加依赖
@pytest.mark.interface
@pytest.mark.dependency(depends=["test_flash_complete"])
def test_interface_test():
    # 需要手动管理状态
    test_state.record_result(...)
    test_state.mark_interface_passed()
```

**钩子方式只需添加marker：**

```python
# ✅ 钩子方式 - 自动管理所有依赖和报告
@pytest.mark.interface
def test_interface_test():
    # 无需任何手动管理！
    assert api_call().success
```

### Hooks Used / 使用的钩子

| 钩子 / Hook | 功能 / Function |
|------------|---------------|
| `pytest_sessionstart` | 初始化Excel报告生成器 |
| `pytest_runtest_logreport` | 自动收集测试结果 |
| `pytest_runtest_makereport` | 自动更新测试状态 |
| `pytest_runtest_setup` | 自动检查依赖 |
| `pytest_collection_modifyitems` | 自动添加依赖标记 |
| `pytest_sessionfinish` | 自动生成Excel报告 |

详细信息请参考项目说明文档。

## Installation / 安装

```bash
# Clone repository / 克隆仓库
git clone <repository-url>
cd pytest-learn-multi-test-categories

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
pytest tests/ -v --alluredir=reports/allure-results/
allure serve ./reports/allure-results/

# Run specific test category / 运行特定测试类别
pytest tests/ -v -m flash
pytest tests/ -v -m interface
pytest tests/ -v -m function
pytest tests/ -v -m performance

# Run with coverage / 运行并生成覆盖率
pytest tests/ --cov=src --cov-report=html:reports/coverage --cov-report=term-missing

# Run in parallel / 并行运行
pytest tests/ -n 4
```

## 测试用例中文名映射 / Test Case Chinese Name Mapping

支持通过测试用例的中文名，将测试结果自动填充到Excel模板的指定单元格，实现**用例设计和用例脚本的对应关系**。

Support mapping test results to specified Excel template cells through test case Chinese names, achieving **correspondence between test case design and test scripts**.

### 使用方式 / Usage

**方式1: 使用装饰器 / Method 1: Use Decorator**
```python
@pytest.mark.flash
@pytest.mark.chinese_name("测试abc")
def test_abc():
    """测试abc"""
    assert True
```

**方式2: 使用中文文档字符串 / Method 2: Use Chinese Docstring**
```python
@pytest.mark.interface
def test_api_login():
    """API登录测试"""
    assert True
```

### Excel模板配置 / Excel Template Configuration

在Excel模板的"测试用例"工作表中：
- **B列**: 测试用例名称（填写中文名，如"测试abc"）
- **J列**: 测试结果（自动填充"通过"/"失败"/"跳过"）

| 行号 | B | ... | J |
|------|---|-----|---|
| 2 | 测试abc | ... | (自动填充) |
| 3 | 连接设备 | ... | (自动填充) |

### JSON配置 / JSON Configuration

```json
{
  "测试用例 / Test Cases": {
    "type": "testcase_mapping",
    "name_column": "B",
    "result_column": "J",
    "result_mappings": {
      "passed": "通过",
      "failed": "失败",
      "skipped": "跳过"
    }
  }
}
```

详细配置指南：[docs/测试用例中文名映射指南.md](docs/测试用例中文名映射指南.md)

## reports / 测试报告

测试运行后会自动生成以下文件：

The following files will be automatically generated after test run:

```
reports/
└── test_report_YYYYMMDD_HHMMSS.xlsx    # Excel报告 / Excel report (自动生成)

templates/
└── test_report_template.xlsx           # Excel模板 / Excel template

configs/
└── report_config.json                   # 报告配置 / Report configuration
```

## Excel Report Template Configuration / Excel报告模板配置

### Quick Start / 快速开始

```bash
# 1. 生成默认Excel模板
python scripts/create_template.py

# 2. 运行测试（自动生成报告）
pytest tests/ -v

# 3. 报告生成在：reports/test_report_YYYYMMDD_HHMMSS.xlsx
```

### Customization / 自定义

**方式1: 直接编辑Excel模板**
- 打开 `templates/test_report_template.xlsx`
- 自定义样式、布局、表头
- JSON配置自动映射数据到对应单元格

**方式2: 修改JSON配置**
- 编辑 `configs/report_config.json`
- 定义数据源到单元格的映射关系
- 支持条件样式和格式化规则

详细配置指南参见：[docs/基于模板的Excel报告配置指南.md](docs/基于模板的Excel报告配置指南.md)

### Excel Report Structure / Excel报告结构

生成的Excel报告包含以下工作表：

The generated Excel report contains the following sheets:

1. **测试汇总 / Summary** - 整体测试统计信息 / Overall test statistics
2. **测试详情 / Test Details** - 所有测试的详细结果 / All test details

### Report Features / 报告特性

- 📊 可自定义模板 / Customizable template
- 🎨 彩色状态标记 / Color-coded status markers (绿色=通过，红色=失败)
- ⏱️ 耗时统计 / Duration statistics
- ✅ 通过/失败统计 / Pass/Fail statistics
- 🔍 详细的错误信息 / Detailed error messages
- 📁 带时间戳的文件名 / Timestamped filename
- ⚙️ JSON配置驱动 / JSON configuration driven

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

@pytest.mark.flash
def test_new_flash_test():
    """Flash test / 刷写测试 - 自动依赖管理，自动报告"""
    assert flash_success
```

### 2. Interface Test Example / 接口测试示例

```python
import pytest

@pytest.mark.interface
def test_new_interface():
    """Interface test / 接口测试 - 自动依赖flash测试，自动报告"""
    assert api_login().success
```

### 3. Function Test Example / 功能测试示例

```python
import pytest

@pytest.mark.function
def test_new_function():
    """Function test / 功能测试 - 自动依赖interface测试，自动报告"""
    assert user_registration().success
```

### 4. Performance Test Example / 性能测试示例

```python
import pytest
import time

@pytest.mark.performance
def test_new_performance(request):
    """Performance test / 性能测试 - 自动依赖function测试，自动报告"""
    start = time.time()
    result = api_call()
    duration = time.time() - start

    assert duration < 0.1

    # 记录性能指标（会自动添加到Excel报告）
    request.node.user_properties.append(('metric', 'Response Time'))
    request.node.user_properties.append(('value', f'{duration:.3f}s'))
```

### Code Comparison / 代码对比

**传统方式（80%代码被移除）：**
```python
# ❌ 需要5行以上的样板代码
@pytest.mark.interface
@pytest.mark.dependency(name="test_api_login", depends=["test_flash_complete"])
def test_api_login(test_state):
    result = api_login()
    assert result.success
    test_state.record_result("test_api_login", result)
    test_state.mark_interface_passed()
    # 还有更多报告相关代码...
```

**钩子方式：**
```python
# ✅ 只需2行核心代码
@pytest.mark.interface
def test_api_login():
    assert api_login().success
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
