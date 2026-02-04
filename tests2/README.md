# tests2 - pytest-dependency 验证测试

## 验证目标

验证使用以下两种方式是否能解决 pytest-dependency 跨文件依赖被跳过的问题：

1. **使用全名 nodeid**：依赖声明和 name 参数都使用完整的 nodeid
2. **使用 tryfirst=True**：确保测试排序在 pytest-dependency 注册依赖之前完成

## 测试结构

```
tests2/
├── conftest.py           # 主 conftest，使用 tryfirst=True 进行测试排序
├── flash_tests/
│   ├── conftest.py
│   └── test_flash.py     # 刷写测试（test_flash_complete 是依赖目标）
├── interface_tests/
│   ├── conftest.py
│   └── test_interface.py # 接口测试，依赖 flash_complete
├── function_tests/
│   ├── conftest.py
│   └── test_function.py  # 功能测试，依赖 interface_complete
└── performance_tests/
    ├── conftest.py
    └── test_performance.py # 性能测试，依赖 function_complete
```

## 依赖链

```
Flash Tests:
  test_flash_connection
  ↓
  test_flash_prepare
  ↓
  test_flash_upload
  ↓
  test_flash_complete (interface 测试的依赖目标)

Interface Tests:
  test_interface_get_status (依赖 test_flash_complete)
  ↓
  test_interface_health_check
  ↓
  test_interface_complete (function 测试的依赖目标)

Function Tests:
  test_function_basic (依赖 test_interface_complete)
  ↓
  test_function_advanced
  ↓
  test_function_complete (performance 测试的依赖目标)

Performance Tests:
  test_performance_latency (依赖 test_function_complete)
  ↓
  test_performance_throughput
  ↓
  test_performance_complete
```

## 运行测试

```bash
# 运行所有测试
pytest tests2 -v

# 运行特定类型的测试
pytest tests2 -v -m flash
pytest tests2 -v -m interface
pytest tests2 -v -m function
pytest tests2 -v -m performance

# 显示依赖关系
pytest tests2 -v --dist=showdeps
```

## 预期结果

如果方案有效，所有测试应该按依赖顺序执行，不应该有不正常的跳过。

### 成功指标
- ✅ 所有 16 个测试都执行（passed）
- ✅ 没有因为依赖问题而被 skipped 的测试
- ✅ 测试顺序符合依赖链

### 失败指标
- ❌ 出现 "Skipped (depends: ...)" 消息
- ❌ 跨文件依赖测试被跳过

## 关键实现

### 1. 使用全名 nodeid

```python
# 依赖目标（flash_tests/test_flash.py）
@pytest.mark.dependency(
    name="tests2.flash_tests.test_flash.TestFlash.test_flash_complete"
)
def test_flash_complete(self):
    pass

# 依赖声明（interface_tests/test_interface.py）
@pytest.mark.dependency(
    depends=["tests2.flash_tests.test_flash.TestFlash.test_flash_complete"]
)
def test_interface_get_status(self):
    pass
```

### 2. 使用 tryfirst=True

```python
# conftest.py
@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(config, items):
    """测试排序，确保在 pytest-dependency 之前执行"""
    phase_order = {
        'flash': 0,
        'interface': 1,
        'function': 2,
        'performance': 3
    }
    items.sort(key=get_test_order)
```

## 验证步骤

1. 运行 `pytest tests2 -v`
2. 观察收集顺序输出（conftest.py 中有调试信息）
3. 检查是否有测试被跳过
4. 验证依赖链是否正确执行

## 验证结果

### 运行结果
```
======================== 7 passed, 10 skipped in 0.16s =========================
```

**跳过的测试**：
- 所有 interface 测试（3个）
- 所有 function 测试（3个）
- 所有 performance 测试（3个）
- 跨文件测试 test_cross_b（1个）

**跳过原因**：
```
test_interface_get_status depends on tests2.flash_tests.test_flash.TestFlash#test_flash_complete
test_interface_health_check depends on tests2.interface_tests.test_interface.TestInterface#test_interface_get_status
test_cross_b depends on test_cross_a
...
```

### 额外验证

#### 验证 1：同文件无类依赖（成功）
```python
# tests2/check_nodeid/test_simple_no_class.py
@pytest.mark.dependency(name="simple_test_no_class_a")
def test_no_class_a():
    assert True

@pytest.mark.dependency(depends=["simple_test_no_class_a"])
def test_no_class_b():
    assert True
```

**结果**：✅ 2 passed（无类依赖正常工作）

#### 验证 2：同文件有类依赖（失败）
```python
# tests2/simple_test/test_simple.py
@pytest.mark.dependency(name="test_a")
def test_a(self):
    assert True

@pytest.mark.dependency(depends=["test_a"])
def test_b(self):
    assert True
```

**结果**：❌ 1 passed, 1 skipped（有类依赖也失败！）

#### 验证 3：跨文件依赖（失败）
```python
# tests2/simple_test/test_a.py
@pytest.mark.dependency(name="test_cross_a")
def test_cross_a():
    assert True

# tests2/simple_test/test_b.py
@pytest.mark.dependency(depends=["test_cross_a"])
def test_cross_b():
    assert True
```

**结果**：❌ 1 passed, 1 skipped
```
2026-02-04 12:59:45 [INFO] skip test_cross_b because it depends on test_cross_a
```

### 结论

**关键发现**：
1. ✅ **无类**的同文件依赖可以正常工作
2. ❌ **有类**的同文件依赖也失败
3. ❌ 跨文件依赖即使使用全名 nodeid 也失败
4. ❌ 即使使用 `tryfirst=True` 保证收集顺序，依赖仍然失败
5. ❌ 尝试了多种 nodeid 格式（`::`、`.`、`#`），都无法解决问题

**pytest-dependency 的根本限制**：
- pytest-dependency 插件在处理**类方法**依赖时存在严重问题
- 不仅仅是跨文件依赖的问题，有类的同文件依赖也会失败
- 不是收集顺序的问题，也不是 nodeid 格式的问题
- 是插件对类方法测试的依赖管理机制的固有限制

**最终结论**：
使用全名 nodeid + tryfirst=True **完全无法解决** pytest-dependency 类方法测试的依赖问题。混合依赖管理策略（test_state fixture 处理跨文件依赖 + pytest-dependency 仅用于无类测试的同文件依赖）是唯一可靠的解决方案。

## 预期的收集顺序

```
1. tests2.flash_tests.test_flash.TestFlash.test_flash_connection
2. tests2.flash_tests.test_flash.TestFlash.test_flash_prepare
3. tests2.flash_tests.test_flash.TestFlash.test_flash_upload
4. tests2.flash_tests.test_flash.TestFlash.test_flash_complete
5. tests2.interface_tests.test_interface.TestInterface.test_interface_get_status
6. tests2.interface_tests.test_interface.TestInterface.test_interface_health_check
7. tests2.interface_tests.test_interface.TestInterface.test_interface_complete
8. tests2.function_tests.test_function.TestFunction.test_function_basic
9. tests2.function_tests.test_function.TestFunction.test_function_advanced
10. tests2.function_tests.test_function.TestFunction.test_function_complete
11. tests2.performance_tests.test_performance.TestPerformance.test_performance_latency
12. tests2.performance_tests.test_performance.TestPerformance.test_performance_throughput
13. tests2.performance_tests.test_performance.TestPerformance.test_performance_complete
```

## 对比 tests/ 目录

| 特性 | tests/ | tests2/ |
|------|--------|---------|
| 依赖方式 | 简化名称 + test_state | 全名 nodeid |
| 跨文件依赖 | test_state fixture | pytest-dependency |
| tryfirst | 无 | 使用 tryfirst=True |
| 依赖链 | 混合策略 | 纯 pytest-dependency |

## 结论说明

如果 tests2/ 中的测试能够正常运行（无异常跳过），说明：
- 全名 nodeid + tryfirst=True 可以解决 pytest-dependency 的跨文件依赖问题
- 但这种方式需要手动维护完整的 nodeid，维护成本较高
- 是否采用取决于项目需求和维护复杂度的权衡

如果 tests2/ 中的测试仍然有跳过问题，说明：
- pytest-dependency 本身的设计限制无法通过这种方式完全解决
- 混合策略（test_state + pytest-dependency）是更可靠的方案
