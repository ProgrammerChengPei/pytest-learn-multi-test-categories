# test_state 计数问题详解

## 问题描述

在测试依赖系统中，当带有 `@pytest.mark.flash` 装饰器的测试 `test_failed_with_mark` 失败后，skip_reason 显示：
```
Skipped: Flash tests not all passed (0/6). Skipping interface tests.
```

但实际应该显示：
```
Skipped: Flash tests not all passed (5/6). Skipping interface tests.
```

**问题现象**：flash 测试有 6 个，其中 5 个通过、1 个失败，但 skip_reason 中显示 passed 为 0。

## 问题根因

### 1. 问题场景

```python
# tests/flash_tests/test_flash1.py

@pytest.mark.flash
def test_failed_with_mark(test_client, test_state, test_config):
    """
    Test failed with flash mark / 带刷写测试标记的用例失败
    """
    assert False  # 这个测试会失败
```

测试执行顺序：
1. `test_flash_connection` - PASSED
2. `test_flash_prepare` - PASSED
3. `test_flash_upload` - PASSED
4. `test_flash_verify` - PASSED
5. `test_flash_complete` - PASSED
6. `test_failed_with_mark` - FAILED ❌

执行结果：5 passed, 1 failed

但是，当执行 interface 测试时，pytest 检查依赖：
```python
if not test_state.is_flash_complete():
    passed = test_state.flash_test_passed_count  # 这里显示 0，而不是 5
    total = test_state.flash_test_total  # 这里显示 6
    skip_reason = f"Flash tests not all passed ({passed}/{total})..."
```

### 2. 代码分析

#### 问题代码（`conftest.py` 原始版本）：

```python
def pytest_runtest_logreport(report):
    """自动收集每个测试的结果"""
    
    # 1. 尝试从 report.item 获取 session
    try:
        if hasattr(report, 'item'):
            item = report.item  # ❌ 这里可能失败
            if hasattr(item, 'session'):
                session = item.session
                test_state = getattr(session, '_test_state_cache', None)
                
                if test_state and test_type:
                    if report.when == 'call':
                        # 更新 test_state
                        if test_type == 'flash':
                            if report.passed:
                                test_state.increment_flash_passed()
                            else:
                                test_state.mark_flash_failed()
    except Exception as e:
        pass  # ❌ 异常被静默忽略
```

#### 问题分析

**问题 1：`report.item` 的可靠性问题**

```python
# pytest_runtest_logreport 在三个阶段被调用：
# - setup 阶段
# - call 阶段（测试执行）
# - teardown 阶段

# 在某些情况下，report.item 可能为 None 或不完整：
# 1. 某些第三方插件修改了 report 对象
# 2. 测试被意外中断时
# 3. 某些异常情况下 pytest 内部处理
```

**问题 2：session 对象获取失败**

```python
# 即使 report.item 不为 None，通过它获取的 session 也可能有问题：
item = report.item
session = item.session  # ❌ 这里获取的 session 可能没有 _test_state_cache 属性

# 因为：
# 1. item.session 可能指向不同的 session 对象
# 2. session._test_state_cache 可能不存在
# 3. session 对象被其他插件修改过
```

**问题 3：异常被静默忽略**

```python
try:
    # 尝试更新 test_state
    ...
except Exception as e:
    pass  # ❌ 所有异常都被忽略，无法调试
```

### 3. 为什么会出现 0/6 的情况

执行流程：

```
1. pytest_sessionstart(session):
   ✓ 创建 test_state 并存储到 session._test_state_cache

2. pytest_collection_modifyitems(config, items):
   ✓ 统计 flash 测试总数 = 6
   ✓ 存储到 config._flash_test_total

3. pytest_runtest_setup(item):
   ✓ 初始化 test_state.flash_test_total = 6

4. pytest_runtest_logreport(report):
   ❌ test_failed_with_mark 失败
   ❌ 尝试更新 test_state，但获取 session 失败
   ❌ test_state.flash_test_passed_count 保持为 0

5. pytest_runtest_setup(item) - 执行 interface 测试:
   ✓ 检查 test_state.is_flash_complete()
   ✓ test_state.flash_test_passed_count = 0 (应该是 5)
   ✓ test_state.flash_test_total = 6
   ✓ 生成 skip_reason = "Flash tests not all passed (0/6)"
```

## 解决方案

### 核心修复：使用 `test_node` 代替 `report.item`

#### 修复后的代码：

```python
def pytest_runtest_logreport(report):
    """自动收集每个测试的结果"""
    global _excel_report_generator, _current_test_item, _wireshark_manager
    
    # 第一步：获取 test_node（优先使用 _current_test_item）
    test_node = None
    if hasattr(report, 'item') and report.item:
        test_node = report.item
    elif _current_test_item:  # ✓ 备选方案
        test_node = _current_test_item
    
    if not test_node:
        return  # ✓ 早期验证
    
    # 获取测试类型
    test_type = None
    for marker_name in ['flash', 'interface', 'function', 'performance']:
        if test_node.get_closest_marker(marker_name):
            test_type = marker_name
            break
    
    # 只在 call 阶段更新 test_state
    if report.when != 'call':
        return
    
    # 第二步：从 test_node 获取 session（✓ test_node 已经验证有效）
    test_state = None
    if test_node and hasattr(test_node, 'session'):
        session = test_node.session
        test_state = getattr(session, '_test_state_cache', None)
    
    if test_state and test_type:
        # ✓ 成功获取到 test_state
        if test_type == 'flash':
            if report.passed:
                test_state.increment_flash_passed()  # ✓ 计数 +1
            else:
                test_state.mark_flash_failed()  # ✓ 标记失败
        # ... 其他测试类型
```

### 关键改进点

| 改进点 | 修复前 | 修复后 |
|--------|--------|--------|
| **获取 session 的方式** | `report.item.session` | `test_node.session` |
| **备选方案** | 无 | 使用 `_current_test_item` |
| **早期验证** | 没有 | 检查 `test_node` 是否为 None |
| **异常处理** | 静默忽略 | 无需 try-except（代码更可靠） |

### 为什么使用 `test_node` 更可靠？

```python
# pytest_runtest_setup 在测试执行前被调用
def pytest_runtest_setup(item):
    global _current_test_item
    _current_test_item = item  # ✓ 存储当前测试项
    
    # ✓ item 是完整的测试项对象，肯定有 session 属性
    session = item.session
    # ✓ session._test_state_cache 在 pytest_sessionstart 中已经设置
```

**优势**：
1. **双重保险**：如果 `report.item` 不可用，使用 `_current_test_item`
2. **早期验证**：在函数开始就检查 `test_node` 是否存在
3. **明确的数据流**：`pytest_runtest_setup` → `_current_test_item` → `pytest_runtest_logreport`

## 验证修复

### 测试用例

```python
# tests/flash_tests/test_flash1.py

@pytest.mark.flash
def test_failed_with_mark(test_client, test_state, test_config):
    """
    Test failed with flash mark / 带刷写测试标记的用例失败
    """
    assert False
```

### 修复后的执行结果

```bash
$ pytest tests/ -v

# Flash 测试执行
tests/flash_tests/test_flash1.py::TestFlash::test_flash_connection PASSED
tests/flash_tests/test_flash1.py::TestFlash::test_flash_prepare PASSED
tests/flash_tests/test_flash1.py::TestFlash::test_flash_upload PASSED
tests/flash_tests/test_flash1.py::TestFlash::test_flash_verify PASSED
tests/flash_tests/test_flash1.py::TestFlash::test_flash_complete PASSED
tests/flash_tests/test_flash1.py::test_failed_with_mark FAILED  # ✓ 失败

# Interface 测试被跳过
tests/interface_tests/test_api1.py::TestInterface::test_interface_get_status SKIPPED (Flash tests not all passed (5/6). Skipping interface tests.)
#                                                                     ↑↑↑
#                                                             现在正确显示 5/6！
```

### 内部状态追踪

```python
# test_failed_with_mark 失败后：
test_state.flash_test_total = 6          # ✓ 正确
test_state.flash_test_passed_count = 5    # ✓ 正确（修复前是 0）
test_state.flash_test_failed = True      # ✓ 正确

# 检查依赖
test_state.is_flash_complete()           # False ✓ 正确
# 因为：passed_count(5) != total(6)
```

## 经验总结

### 1. 不要假设 pytest 钩子的参数总是完整的

```python
# ❌ 错误做法
item = report.item  # 假设 report 一定有 item 属性

# ✓ 正确做法
test_node = None
if hasattr(report, 'item') and report.item:
    test_node = report.item
elif _current_test_item:  # 备选方案
    test_node = _current_test_item
```

### 2. 提供备选方案，而不是静默失败

```python
# ❌ 错误做法
try:
    item = report.item
    session = item.session
    # ...
except Exception:
    pass  # 静默忽略，无法调试

# ✓ 正确做法
test_node = None
if hasattr(report, 'item') and report.item:
    test_node = report.item
elif _current_test_item:  # 明确的备选方案
    test_node = _current_test_item

if not test_node:
    return  # 明确的失败路径
```

### 3. 使用全局变量存储关键状态

```python
# ✓ 在 pytest_runtest_setup 中存储
_current_test_item = item

# ✓ 在 pytest_runtest_logreport 中使用
test_node = _current_test_item  # 可靠的备选方案
```

### 4. 早期验证，避免后期错误

```python
# ✓ 在函数开始就验证
if not test_node:
    return  # 早期返回，避免后续逻辑出错

# ✓ 然后再进行后续处理
test_state = getattr(session, '_test_state_cache', None)
```

## 相关文件

- `tests/conftest.py` - pytest 配置文件，包含所有钩子函数
- `tests/flash_tests/test_flash1.py` - 测试用例文件
- `docs/test_state_counting_issue.md` - 本文档

## 相关提交

```
commit ac2e04c
fix: 修复test_state更新逻辑，确保测试失败时正确计数
```

## 参考资料

- [pytest 钩子文档](https://docs.pytest.org/en/stable/reference/reference.html#hooks)
- [pytest session 对象](https://docs.pytest.org/en/stable/reference/reference.html#session)
- [pytest item 对象](https://docs.pytest.org/en/stable/reference/reference.html#item)
