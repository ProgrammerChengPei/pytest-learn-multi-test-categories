# 基于模板的Excel报告配置指南

## 概述 / Overview

本文档介绍如何使用Excel模板和JSON配置文件来自定义pytest测试报告的生成方式。

This document describes how to use Excel templates and JSON configuration files to customize pytest test report generation.

## 核心概念 / Core Concepts

### 1. Excel模板 / Excel Template

Excel模板是一个预先设计好的Excel文件，定义了：
- 工作表结构
- 单元格样式
- 标题和表头
- 布局和格式

### 2. JSON配置 / JSON Configuration

JSON配置文件定义了：
- 模板文件路径
- 数据源到单元格的映射关系
- 数据格式化规则
- 样式应用规则

## 快速开始 / Quick Start

### 步骤1: 生成默认模板 / Step 1: Generate Default Template

```bash
# 运行模板生成脚本
python scripts/create_template.py
```

这将创建默认的Excel模板文件：
```
templates/test_report_template.xlsx
```

### 步骤2: 查看配置文件 / Step 2: View Configuration File

配置文件位于：
```
configs/report_config.json
```

### 步骤3: 运行测试 / Step 3: Run Tests

```bash
pytest tests/ -v
```

报告将自动生成到：
```
reports/test_report_YYYYMMDD_HHMMSS.xlsx
```

## JSON配置详解 / JSON Configuration Details

### 配置文件结构 / Configuration File Structure

```json
{
  "template": "templates/test_report_template.xlsx",
  "output_dir": "reports",
  "mappings": {
    "工作表名1": {
      "type": "summary|list",
      "fields": { ... },
      "columns": { ... }
    },
    "工作表名2": { ... }
  }
}
```

### 1. 顶层配置 / Top-level Configuration

| 字段 / Field | 说明 / Description | 示例 / Example |
|-------------|------------------|---------------|
| `template` | Excel模板文件路径 | `"templates/test_report_template.xlsx"` |
| `output_dir` | 报告输出目录 | `"reports"` |
| `mappings` | 工作表映射配置 | 见下文 / See below |

### 2. 工作表映射配置 / Worksheet Mapping Configuration

#### 2.1 汇总类型工作表 / Summary-type Worksheet

```json
{
  "测试汇总 / Summary": {
    "type": "summary",
    "fields": {
      "报告生成时间 / Report Time": {
        "cell": "C3",
        "source": "session.report_time",
        "format": "datetime"
      }
    }
  }
}
```

**字段说明 / Field Descriptions:**

| 字段 / Field | 说明 / Description |
|-------------|------------------|
| `type` | 工作表类型：`summary`（汇总）或 `list`（列表） |
| `fields` | 单个字段映射配置 |
| `type_stats` | 类型统计配置 |

**单个字段配置 / Single Field Configuration:**

```json
{
  "cell": "C3",
  "source": "stats.total",
  "format": "number",
  "decimals": 2,
  "unit": " 秒"
}
```

| 字段 / Field | 说明 / Description | 可选值 / Options |
|-------------|------------------|----------------|
| `cell` | 单元格地址 | `"A1"`, `"B3"` 等 |
| `source` | 数据源路径 | 见数据源部分 |
| `format` | 数据格式 | `"string"`, `"number"`, `"datetime"`, `"percent"` |
| `decimals` | 小数位数（number类型） | 数字 / number |
| `unit` | 单位后缀 | `"秒"`, `"ms"` 等 |
| `style` | 样式配置 | 见样式部分 |

#### 2.2 列表类型工作表 / List-type Worksheet

```json
{
  "测试详情 / Test Details": {
    "type": "list",
    "start_row": 2,
    "columns": {
      "序号 / No": {
        "col": "A",
        "source": "index",
        "format": "number"
      },
      "测试名称 / Test Name": {
        "col": "B",
        "source": "name",
        "format": "string"
      },
      "状态 / Status": {
        "col": "D",
        "source": "status",
        "format": "string",
        "style": {
          "passed": { "fill": "C6EFCE" },
          "failed": { "fill": "FFC7CE" },
          "skipped": { "fill": "FFEB9C" }
        }
      }
    }
  }
}
```

| 字段 / Field | 说明 / Description |
|-------------|------------------|
| `type` | 必须为 `"list"` |
| `start_row` | 数据开始行号（表头通常在第1行） |
| `columns` | 列配置对象，键为列名 |

**列配置 / Column Configuration:**

| 字段 / Field | 说明 / Description | 特殊值 / Special Value |
|-------------|------------------|---------------------|
| `col` | 列字母 | `"A"`, `"B"`, `"C"` 等 |
| `source` | 数据源 | `"index"` 表示序号，其他见数据源部分 |
| `format` | 格式 | 同上 |
| `style` | 条件样式 | 根据值应用不同样式 |

## 数据源说明 / Data Source Reference

数据通过点号分隔的路径访问，如 `session.report_time`

### 可用数据源 / Available Data Sources

#### Session数据 / Session Data

```python
"session.report_time"      # 报告生成时间
"session.total_duration"   # 总测试耗时
```

#### 统计数据 / Statistics Data

```python
"stats.total"              # 测试总数
"stats.passed"             # 通过数
"stats.failed"             # 失败数
"stats.skipped"            # 跳过数

"stats.flash.total"        # Flash测试总数
"stats.flash.passed"       # Flash通过数
"stats.flash.failed"       # Flash失败数
"stats.flash.pass_rate"    # Flash通过率

"stats.interface.total"    # 接口测试总数
"stats.interface.passed"   # 接口测试通过数
"stats.interface.failed"   # 接口测试失败数
"stats.interface.pass_rate" # 接口测试通过率

"stats.function.total"     # 功能测试总数
"stats.function.passed"    # 功能测试通过数
"stats.function.failed"    # 功能测试失败数
"stats.function.pass_rate" # 功能测试通过率

"stats.performance.total"  # 性能测试总数
"stats.performance.passed" # 性能测试通过数
"stats.performance.failed" # 性能测试失败数
"stats.performance.pass_rate" # 性能测试通过率
```

#### 测试结果数据 / Test Result Data

用于列表类型工作表：

```python
"index"                    # 序号（特殊值）
"name"                     # 测试名称
"category"                 # 测试类型 (flash/interface/function/performance)
"status"                   # 状态 (passed/failed/skipped)
"duration"                 # 耗时（秒）
"file"                     # 文件路径
"line"                     # 行号
"message"                  # 消息/错误信息
"metric"                   # 性能指标名称
"value"                    # 性能指标值
```

## 格式化选项 / Formatting Options

### string / 字符串

```json
{
  "format": "string"
}
```
直接显示字符串值，不做特殊处理。

### number / 数字

```json
{
  "format": "number",
  "decimals": 2,
  "unit": " 秒"
}
```

| 字段 / Field | 说明 / Description |
|-------------|------------------|
| `decimals` | 小数位数，默认2 |
| `unit` | 单位后缀，可选 |

示例：`123.456` → `"123.46 秒"`

### datetime / 日期时间

```json
{
  "format": "datetime"
}
```
格式：`"2024-02-03 14:30:52"`

### percent / 百分比

```json
{
  "format": "percent"
}
```
将小数转换为百分比。示例：`0.85` → `"85.0%"`

## 样式配置 / Style Configuration

### 条件样式 / Conditional Style

在列表工作表中，可以根据值应用不同样式：

```json
{
  "状态 / Status": {
    "col": "D",
    "source": "status",
    "format": "string",
    "style": {
      "passed": {
        "fill": "C6EFCE"   # 绿色背景
      },
      "failed": {
        "fill": "FFC7CE"   # 红色背景
      },
      "skipped": {
        "fill": "FFEB9C"   # 黄色背景
      }
    }
  }
}
```

**常用背景颜色 / Common Background Colors:**

| 用途 / Use | 颜色 / Color | 代码 / Code |
|-----------|-------------|------------|
| 通过 / Passed | 绿色 / Green | `C6EFCE` |
| 失败 / Failed | 红色 / Red | `FFC7CE` |
| 跳过 / Skipped | 黄色 / Yellow | `FFEB9C` |
| 标题 / Header | 蓝色 / Blue | `4472C4` |
| 表头 / Table Header | 浅蓝 / Light Blue | `D9E1F2` |
| 边框 / Border | 灰色 / Gray | `CCCCCC` |

## 自定义模板 / Customizing Templates

### 步骤1: 编辑Excel模板 / Step 1: Edit Excel Template

1. 打开 `templates/test_report_template.xlsx`
2. 自定义样式、布局、表头
3. **注意：** 修改模板时，确保单元格地址与JSON配置一致

### 步骤2: 更新JSON配置 / Step 2: Update JSON Configuration

根据模板修改调整JSON配置中的`cell`或`col`映射。

### 示例：添加新字段 / Example: Add New Field

**模板修改 / Template Modification:**
- 在 `测试汇总` 工作表的 `C9` 单元格添加 `测试人员` 标签
- 数据填入 `D9` 单元格

**JSON配置更新 / JSON Configuration Update:**
```json
{
  "测试汇总 / Summary": {
    "fields": {
      "测试人员 / Tester": {
        "cell": "D9",
        "source": "session.tester",
        "format": "string"
      }
    }
  }
}
```

**添加数据源 / Add Data Source:**
在conftest.py中添加：
```python
session.config.tester_name = "张三"
```

## 配置示例 / Configuration Examples

### 示例1: 简单汇总 / Example 1: Simple Summary

```json
{
  "template": "templates/simple_template.xlsx",
  "output_dir": "reports",
  "mappings": {
    "Summary": {
      "type": "summary",
      "fields": {
        "Total": {
          "cell": "B2",
          "source": "stats.total",
          "format": "number"
        },
        "Passed": {
          "cell": "B3",
          "source": "stats.passed",
          "format": "number"
        }
      }
    }
  }
}
```

### 示例2: 带类型统计的汇总 / Example 2: Summary with Type Stats

```json
{
  "测试汇总 / Summary": {
    "type": "summary",
    "fields": {
      "报告时间": {
        "cell": "C3",
        "source": "session.report_time",
        "format": "datetime"
      }
    },
    "type_stats": {
      "start_row": 12,
      "columns": {
        "测试类型 / Type": "A",
        "总数 / Total": "B",
        "通过 / Passed": "C",
        "失败 / Failed": "D",
        "通过率 / Pass Rate": "E"
      },
      "row_mapping": {
        "flash": 12,
        "interface": 13,
        "function": 14,
        "performance": 15
      },
      "fields": {
        "刷写 / Flash": {
          "total": { "source": "stats.flash.total", "format": "number" },
          "passed": { "source": "stats.flash.passed", "format": "number" },
          "failed": { "source": "stats.flash.failed", "format": "number" },
          "pass_rate": { "source": "stats.flash.pass_rate", "format": "percent" }
        }
      }
    }
  }
}
```

### 示例3: 自定义列的列表 / Example 3: List with Custom Columns

```json
{
  "测试详情 / Test Details": {
    "type": "list",
    "start_row": 2,
    "columns": {
      "No": {
        "col": "A",
        "source": "index",
        "format": "number"
      },
      "Test Name": {
        "col": "B",
        "source": "name",
        "format": "string"
      },
      "Status": {
        "col": "C",
        "source": "status",
        "format": "string",
        "style": {
          "passed": { "fill": "C6EFCE" },
          "failed": { "fill": "FFC7CE" }
        }
      },
      "Duration (ms)": {
        "col": "D",
        "source": "duration",
        "format": "number",
        "decimals": 0,
        "unit": " ms"
      }
    }
  }
}
```

## 运行时自定义 / Runtime Customization

### 方式1: 修改配置文件 / Method 1: Modify Config File

直接编辑 `configs/report_config.json`

### 方式2: 传递自定义配置 / Method 2: Pass Custom Config

在conftest.py中：

```python
def pytest_sessionstart(session):
    # 加载自定义配置
    custom_config_path = project_root / "configs" / "custom_report_config.json"
    generator = TemplateBasedReportGenerator(custom_config_path)
    # ...
```

## 故障排查 / Troubleshooting

### 问题1: 模板文件不存在 / Issue 1: Template File Not Found

**错误信息 / Error:**
```
FileNotFoundError: templates/test_report_template.xlsx
```

**解决方案 / Solution:**
```bash
# 生成默认模板
python scripts/create_template.py
```

### 问题2: 单元格不存在 / Issue 2: Cell Not Found

**错误信息 / Error:**
```
KeyError: 'cell' or invalid cell reference
```

**解决方案 / Solution:**
- 检查JSON配置中的`cell`值是否正确
- 确保模板中存在该单元格

### 问题3: 数据源无效 / Issue 3: Invalid Data Source

**错误信息 / Error:**
```
NoneType error when accessing data source
```

**解决方案 / Solution:**
- 检查`source`路径是否正确
- 参考数据源说明部分

### 问题4: 样式未应用 / Issue 4: Style Not Applied

**可能原因 / Possible Causes:**
- `source`值与配置的键不匹配
- 列配置未设置`style`字段

**解决方案 / Solution:**
- 确保列表工作表的`source`值与样式键匹配
- 检查`style`配置是否正确

## 最佳实践 / Best Practices

### 1. 模板设计 / Template Design

- 使用固定单元格地址，避免使用合并单元格作为数据目标
- 预留足够空间显示数据
- 使用清晰的列名和工作表名
- 考虑数据的最大可能长度

### 2. 配置管理 / Configuration Management

- 为不同项目/环境创建不同的配置文件
- 使用版本控制管理配置文件
- 添加注释说明每个配置的作用
- 定期备份模板文件

### 3. 数据映射 / Data Mapping

- 使用有意义的数据源名称
- 避免深层嵌套（超过3层）
- 为复杂计算创建中间数据源
- 保持配置文件可读性

### 4. 样式管理 / Style Management

- 使用十六进制颜色代码保持一致性
- 为不同状态定义标准颜色方案
- 避免使用过多颜色影响可读性
- �虑打印时的黑白显示效果

## 完整配置示例 / Complete Configuration Example

参见项目中的 `configs/report_config.json` 文件。

## 总结 / Summary

使用Excel模板和JSON配置的优势：

1. **灵活性 / Flexibility** - 完全自定义报告外观
2. **可维护性 / Maintainability** - 样式和逻辑分离
3. **可扩展性 / Scalability** - 易于添加新字段和功能
4. **用户友好 / User-friendly** - 非程序员也能编辑模板
5. **版本控制 / Version Control** - 配置文件易于追踪变更

关键要点：

- Excel模板定义外观和布局
- JSON配置定义数据映射和规则
- 数据源通过点号路径访问
- 支持条件样式和格式化
- 钩子自动填充数据到模板
