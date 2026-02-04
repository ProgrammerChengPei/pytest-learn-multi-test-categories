# 概述

本项目是嵌入式Pytest测试框架，支持接口、功能、性能测试，**完全基于钩子的自动化**依赖管理和Excel报告生成。

src是TCP通信的服务端和客户端，只是测试对象示例，随测试需要而更新。

## 目录结构

| tests
|-- conftest.py
|-- common              # 接口、功能和性能测试共同的辅助模块

|-- flash_tests         # 刷写测试
|   |-- common          # 刷写测试辅助模块
|   |-- test_flash1.py
|   |-- conftest.py     # 刷写测试的配置文件，用于定义fixture和hook

|-- interface_tests     # 接口测试
|   |-- common          # 接口测试辅助模块
|   |   |-- interface_common1.py
|   |-- test_api1.py
|   |-- conftest.py     # 接口测试的配置文件，用于定义fixture和hook

|-- function_tests      # 功能测试
|   |-- common          # 功能测试辅助模块
|   |   |-- function_common1.py
|   |-- test_func1.py
|   |-- conftest.py     # 功能测试的配置文件，用于定义fixture和hook

|-- performance_tests   # 性能测试
|   |-- common          # 性能测试辅助模块
|   |   |-- performance_common1.py
|   |-- test_perf1.py
|   |-- conftest.py     # 性能测试的配置文件，用于定义fixture和hook

| pyproject.toml        # 测试配置文件
| README.md             # 测试说明文档
| requirements.txt      # 测试依赖库列表


- 每个common目录下有独立的辅助模块，用于存放该测试类型特有的辅助函数
- 每个conftest.py和common目录都尽可能用上

## 需求

### 测试依赖
- 所有测试用例都依赖刷写测试，如果刷写测试失败，则后续所有测试用例都跳过
- 所有功能测试用例都依赖接口测试，如果接口测试失败，则后续所有功能测试用例都跳过
- 所有性能测试用例都依赖功能测试，如果功能测试失败，则后续所有性能测试用例都跳过

### 测试报告
templates/目录下有excel测试报告模板，测试结束后生成最终的Excel报告

### 技术约束
- 尽量使用pytest的钩子、fixture、marker、参数化、已有插件等特性