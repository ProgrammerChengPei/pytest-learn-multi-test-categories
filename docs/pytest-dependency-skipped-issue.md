# pytest-dependency 跳过问题分析与解决方案

## 问题概述

在使用 `pytest-dependency` 插件管理测试依赖时，测试用例被不正常跳过的问题。

### 具体表现

`test_interface_get_status` 声明依赖 `test_flash_complete`，但即使 `test_flash_complete` 测试通过，`test_interface_get_status` 仍被跳过。

```
SKIPPED (depends: test_flash_complete)
```

## 根本原因分析

### 原因一：pytest-dependency 使用测试的完整 nodeid

`pytest-dependency` 插件通过测试的 **完整 nodeid** 来跟踪和匹配依赖关系。

#### nodeid 的格式

pytest 中的 nodeid 是测试的完整路径标识符，格式为：
```
文件路径::类名::测试方法名
```

例如：
```
tests/flash_tests/test_flash.py::TestFlash::test_flash_complete
tests/interface_tests/test_interface.py::TestInterface::test_interface_get_status
```

#### 问题所在

当使用 `@pytest.mark.dependency(depends=["test_flash_complete"])` 时，声明的依赖名称是简化名称 `test_flash_complete`，但 `pytest-dependency` 在内部存储和查找依赖时使用的是完整 nodeid。

这就导致了名称不匹配：
| 依赖声明 | pytest-dependency 内部查找 | 是否匹配 |
|---------|------------------------|---------|
| `test_flash_complete` | `tests/flash_tests/test_flash.py::TestFlash::test_flash_complete` | ❌ 不匹配 |

#### 代码示例

```python
# tests/flash_tests/test_flash.py
class TestFlash:
    @pytest.mark.flash
    @pytest.mark.dependency(name="test_flash_complete")
    def test_flash_complete(self, test_client, test_state, test_config, test_artifacts_dir):
        """测试刷写完成"""
        test_state.mark_flash_passed()
        # 测试通过后，pytest-dependency 记录的依赖项：
        # 实际 nodeid: tests/flash_tests/test_flash.py::TestFlash::test_flash_complete
        # name 参数: test_flash_complete

# tests/interface_tests/test_interface.py
class TestInterface:
    @pytest.mark.interface
    @pytest.mark.dependency(depends=["test_flash_complete"])
    def test_interface_get_status(self, test_state, test_client):
        """测试get_status接口，依赖刷写测试完成"""
        # 依赖声明查找: test_flash_complete
        # 但实际需要匹配的是完整 nodeid，导致找不到
        pass
```

即使使用了 `name="test_flash_complete"` 参数，在跨文件依赖的情况下，`pytest-dependency` 可能无法正确匹配依赖关系。

---

### 原因二：pytest 收集测试的顺序可能导致依赖信息未正确注册

这是更深层的原因。pytest 的测试收集和执行分为两个阶段，收集顺序的不确定性会影响 `pytest-dependency` 的依赖注册机制。

#### pytest 的两个阶段

**阶段 1：收集阶段（Collection Phase）**
- pytest 扫描所有测试文件
- 构建测试项（test items）列表
- 按特定顺序排列这些测试项

**阶段 2：执行阶段（Execution Phase）**
- 按收集顺序依次执行测试
- 执行过程中更新测试状态

#### pytest-dependency 的工作机制

`pytest-dependency` 插件在**收集阶段**注册依赖关系：

1. 当收集到一个带有 `@pytest.mark.dependency(name="xxx")` 的测试时，插件会注册这个测试名称
2. 当收集到一个带有 `@pytest.mark.dependency(depends=["xxx"])` 的测试时，插件会尝试查找已注册的依赖名称
3. 如果依赖名称未注册（例如依赖的测试还未被收集），则依赖关系可能无法正确建立

#### 收集顺序的影响

pytest 的收集顺序不是固定的，受多种因素影响：
- 文件系统的文件遍历顺序
- 文件名、类名、测试方法的字母顺序
- 插件的收集钩子修改

**关键问题**：如果被依赖的测试 `test_flash_complete` 在依赖它的测试 `test_interface_get_status` **之后**被收集，那么在收集 `test_interface_get_status` 时，`test_flash_complete` 的依赖信息还未注册到 `pytest-dependency` 的内部状态中。

#### 详细示例分析

##### 场景 1：正常的收集顺序（依赖测试先收集）

```python
# pytest 收集顺序
1. tests/flash_tests/test_flash.py::TestFlash::test_flash_complete
   → pytest-dependency 注册: name="test_flash_complete"
   → 内部状态: {"test_flash_complete": <test_item>}

2. tests/interface_tests/test_interface.py::TestInterface::test_interface_get_status
   → pytest-dependency 查找: depends=["test_flash_complete"]
   → 在内部状态中找到了 "test_flash_complete"
   → 依赖关系建立成功
```

结果：依赖关系正确建立 ✅

##### 场景 2：异常的收集顺序（依赖测试后收集）

```python
# pytest 收集顺序
1. tests/interface_tests/test_interface.py::TestInterface::test_interface_get_status
   → pytest-dependency 查找: depends=["test_flash_complete"]
   → 在内部状态中查找 "test_flash_complete"
   → ❌ 未找到！（因为 test_flash_complete 还未被收集）
   → 依赖关系建立失败或状态不确定

2. tests/flash_tests/test_flash.py::TestFlash::test_flash_complete
   → pytest-dependency 注册: name="test_flash_complete"
   → 内部状态: {"test_flash_complete": <test_item>}
   → 但此时 test_interface_get_status 已经处理完毕，依赖关系已无法修正
```

结果：依赖关系建立失败 ❌

##### 为什么会出现场景 2？

pytest 的收集顺序受多种因素影响，以下是一个实际可能出现的收集顺序：

```
tests/
├── function_tests/test_function.py
├── interface_tests/test_interface.py      ← 这里收集了 test_interface_get_status
├── flash_tests/test_flash.py              ← 这里收集了 test_flash_complete
└── performance_tests/test_performance.py
```

可能的收集顺序（按字母顺序）：
1. `tests/flash_tests/test_flash.py::TestFlash::test_flash_complete`
2. `tests/function_tests/test_function.py::TestFunction::test_function_xxx`
3. `tests/interface_tests/test_interface.py::TestInterface::test_interface_get_status`
4. `tests/performance_tests/test_performance.py::TestPerformance::test_performance_xxx`

或者另一种顺序：
1. `tests/function_tests/test_function.py::TestFunction::test_function_xxx`
2. `tests/interface_tests/test_interface.py::TestInterface::test_interface_get_status` ← 在这里查找依赖
3. `tests/flash_tests/test_flash.py::TestFlash::test_flash_complete` ← 但依赖测试在这里才收集

#### 代码层面的证据

让我们看 `pytest-dependency` 插件的简化工作流程：

```python
# pytest-dependency 插件内部逻辑（简化版）

# 全局存储依赖状态
dependency_state = {}

def pytest_collection_modifyitems(config, items):
    """收集阶段：注册依赖和建立依赖关系"""
    for item in items:
        marker = item.get_closest_marker('dependency')
        if not marker:
            continue

        # 情况 1：注册测试名称
        if 'name' in marker.kwargs:
            name = marker.kwargs['name']
            dependency_state[name] = item
            print(f"[注册] {name} -> {item.nodeid}")

        # 情况 2：建立依赖关系
        if 'depends' in marker.kwargs:
            depends_on = marker.kwargs['depends']
            for dep_name in depends_on:
                if dep_name not in dependency_state:
                    # ⚠️ 关键问题：依赖名称还未注册
                    print(f"[警告] 依赖 {dep_name} 尚未注册")
                    # 可能的处理方式：
                    # 1. 标记为待检查
                    # 2. 忽略（导致依赖关系丢失）
                    # 3. 记录警告但不建立关系
                else:
                    print(f"[依赖] {item.nodeid} 依赖于 {dep_name}")
```

#### 实际日志示例

假设 pytest 收集顺序是 `interface` → `flash`：

```
[pytest-dependency] 收集: tests/interface_tests/test_interface.py::TestInterface::test_interface_get_status
[pytest-dependency] 检查依赖: test_flash_complete
[pytest-dependency] ⚠️ 警告: 依赖 'test_flash_complete' 尚未注册到依赖状态中
[pytest-dependency] 依赖关系未建立

[pytest-dependency] 收集: tests/flash_tests/test_flash.py::TestFlash::test_flash_complete
[pytest-dependency] 注册: test_flash_complete
[pytest-dependency] 依赖状态更新: {"test_flash_complete": <TestFlash::test_flash_complete>}
```

#### 执行阶段的问题

在执行阶段，当 `test_interface_get_status` 被执行时：

```python
def pytest_runtest_setup(item):
    """执行阶段：检查依赖是否满足"""
    marker = item.get_closest_marker('dependency')
    if marker and 'depends' in marker.kwargs:
        for dep_name in marker.kwargs['depends']:
            # 检查依赖测试是否已通过
            dep_status = check_dependency_status(dep_name)
            if dep_status != 'passed':
                # ⚠️ 由于收集阶段依赖关系未正确建立，这里可能找不到依赖
                pytest.skip(f"depends: {dep_name}")
```

由于收集阶段依赖关系未正确建立，执行阶段检查时可能：
1. 找不到依赖测试的状态信息
2. 或者依赖状态信息不完整
3. 导致误判为依赖未满足，从而跳过测试

#### 跨文件依赖的复杂性

跨文件依赖（如 `test_interface.py` 依赖 `test_flash.py`）进一步加剧了这个问题，因为：

1. **文件收集顺序不确定**：pytest 可能按文件名字母顺序收集，也可能按目录结构收集
2. **类和方法的排序**：即使文件顺序确定，类名、方法名的排序也可能变化
3. **插件干扰**：其他 pytest 插件可能会修改收集顺序
4. **并行收集**：如果使用 pytest-xdist 等并行插件，收集顺序更加不可预测

#### 实际测试日志分析

从 `test_artifacts/pytest.log` 可以看到：
```
2026-02-04 12:19:58 [INFO] client.py:67 - Connected to localhost:8080
2026-02-04 12:19:58 [INFO] client.py:185 - Sent request: {'type': 'request', 'command': 'get_status', 'id': 1, 'token': 'your-secure-token-here'}
```

这些日志显示 `test_interface_get_status` 实际上被执行了，但在执行前可能因为依赖检查失败而跳过了实际测试逻辑。

---

## 解决方案

采用**混合依赖管理策略**：
- **跨文件依赖**：使用 `test_state` fixture 进行状态管理
- **同文件依赖**：使用 `pytest-dependency` 配合 `name` 参数

### 解决步骤

#### 步骤 1：在 conftest.py 中定义测试状态管理器

```python
# tests/conftest.py
class TestState:
    """测试状态管理器"""
    def __init__(self):
        self.flash_test_passed = False
        self.interface_test_passed = False
        self.function_test_passed = False

    def mark_flash_passed(self):
        self.flash_test_passed = True

    def mark_interface_passed(self):
        self.interface_test_passed = True

    def mark_function_passed(self):
        self.function_test_passed = True

@pytest.fixture(scope="session")
def test_state():
    """测试状态fixture，用于管理测试依赖"""
    return TestState()
```

#### 步骤 2：移除 interface 测试中的 pytest-dependency 装饰器

```python
# tests/interface_tests/test_interface.py
from pytest import skip

class TestInterface:
    @pytest.mark.interface
    def test_interface_get_status(self, test_state, test_client):
        """测试get_status接口"""
        # 通过 fixture 检查依赖
        if not test_state.flash_test_passed:
            pytest.skip("Flash test has not passed yet")

        # 测试逻辑
        request = {
            "type": "request",
            "command": "get_status",
            "id": 1,
            "token": test_client.token
        }
        # ...
```

#### 步骤 3：在 pytest_runtest_setup hook 中实现依赖检查

```python
# tests/conftest.py
def pytest_runtest_setup(item):
    """测试执行前自动检查依赖"""
    # 检查测试类型
    test_type = None
    for marker in ['interface', 'function', 'performance']:
        if item.get_closest_marker(marker):
            test_type = marker
            break

    if not test_type:
        return

    # 获取 test_state fixture
    test_state = None
    try:
        if hasattr(item, '_fixtureinfo'):
            fixturedef = item._fixtureinfo.name2fixturedefs.get('test_state')
            if fixturedef:
                test_state = fixturedef[0].cached_result
                if test_state:
                    test_state = test_state[0]
    except Exception:
        pass

    if not test_state:
        return

    # 检查依赖并跳过
    skip_reason = None
    if test_type == 'interface' and not test_state.flash_test_passed:
        skip_reason = "Flash test has not passed yet"
    elif test_type == 'function' and not test_state.interface_test_passed:
        skip_reason = "Interface test has not passed yet"
    elif test_type == 'performance' and not test_state.function_test_passed:
        skip_reason = "Function test has not passed yet"

    if skip_reason:
        pytest.skip(skip_reason)
```

#### 步骤 4：禁用自动依赖添加

```python
# tests/conftest.py
def pytest_collection_modifyitems(config, items):
    """
    修改测试收集，禁用自动添加pytest-dependency标记
    因为pytest_runtest_setup已经基于test_state实现了依赖检查
    """
    # 按测试类型排序
    phase_order = {
        'flash': 0,
        'interface': 1,
        'function': 2,
        'performance': 3
    }

    def get_test_order(item):
        for marker_name, order in phase_order.items():
            if item.get_closest_marker(marker_name):
                return order
        return 99

    items.sort(key=get_test_order)
```

---

## 为什么即使在同一会话中 pytest-dependency 也可能失败

pytest 的测试收集和执行分为两个阶段：

1. **收集阶段**：扫描所有测试文件，构建测试项列表
2. **执行阶段**：按顺序执行测试项

`pytest-dependency` 插件在收集阶段记录依赖关系，如果：

- 依赖测试 `test_flash_complete` 在被依赖的测试 `test_interface_get_status` **之后**被收集
- 导致在收集 `test_interface_get_status` 时，`test_flash_complete` 的依赖信息未注册

则插件在执行阶段无法找到依赖记录，从而跳过测试。

此外，pytest 的收集顺序受文件名、类名、测试名等多个因素影响，不是稳定的，这进一步增加了依赖匹配的不确定性。

---

## 混合依赖管理策略

### 设计原则

根据依赖的范围选择不同的管理方式：

| 依赖类型 | 推荐方式 | 原因 |
|---------|---------|------|
| 同文件严格有序依赖 | `pytest-dependency` + `name` | 精确控制执行顺序 |
| 跨文件依赖 | `test_state` fixture + hooks | 避免pytest收集顺序问题 |

### 实现架构

```
依赖管理架构
├── 跨文件依赖（test_state）
│   ├── Flash Test Complete → 接口测试执行
│   ├── Interface Test Complete → 功能测试执行
│   └── Function Test Complete → 性能测试执行
│
└── 同文件依赖（pytest-dependency）
    └── Flash Test 内部顺序
        ├── test_flash_connection
        ├── test_flash_prepare (depends on connection)
        ├── test_flash_upload (depends on prepare)
        ├── test_flash_verify (depends on upload)
        └── test_flash_complete (depends on verify)
```

### 代码实现总结

#### 1. test_state fixture（跨文件依赖）
```python
# tests/conftest.py
@pytest.fixture(scope="session")
def test_state():
    return TestState()

# 在测试通过时更新状态
test_state.mark_flash_passed()
test_state.mark_interface_passed()
test_state.mark_function_passed()
```

#### 2. pytest_runtest_setup hook（依赖检查）
```python
# tests/conftest.py
def pytest_runtest_setup(item):
    """在测试执行前检查依赖"""
    # 检查测试类型和前置测试状态
    # 如果未满足依赖，使用 pytest.skip() 跳过
```

#### 3. pytest-dependency（同文件依赖）
```python
# tests/flash_tests/test_flash.py
@pytest.mark.dependency(name="test_name", depends=["prev_test_name"])
def test_name(self, ...):
    pass
```

---

## 最佳实践

### 1. 使用 pytest-dependency 时

✅ **推荐做法**：
```python
@pytest.mark.dependency(name="unique_test_name", depends=["previous_test_name"])
def test_something(self, ...):
    pass
```

❌ **避免做法**：
```python
@pytest.mark.dependency(depends=["test_name"])  # 缺少 name 参数
def test_something(self, ...):
    pass
```

### 2. 跨文件依赖时

✅ **推荐做法**：
```python
# 使用 test_state fixture 进行状态管理
def test_interface(self, test_state, test_client):
    if not test_state.flash_test_passed:
        pytest.skip("Flash test has not passed yet")
    # ...
```

❌ **避免做法**：
```python
# 不使用 pytest-dependency 管理跨文件依赖
@pytest.mark.dependency(depends=["tests/other_file.py::TestClass::test_name"])
def test_interface(self, ...):
    pass
```

### 3. 依赖命名规范

- 使用简短、明确的名称
- 使用小写字母和下划线：`test_flash_connection`
- 避免使用特殊字符和中文
- 确保名称在同一文件内唯一

---

## 相关文件

- `tests/conftest.py` - 测试配置和依赖管理逻辑
- `tests/flash_tests/test_flash.py` - 刷写测试（使用 pytest-dependency 管理内部顺序）
- `tests/interface_tests/test_interface.py` - 接口测试（使用 test_state 管理跨文件依赖）
- `pytest.ini` - pytest 配置文件

---

## 总结

1. **pytest-dependency 的限制**：
   - 依赖名称匹配依赖完整 nodeid
   - 依赖关系在收集阶段注册，收集顺序影响依赖建立的正确性
   - 跨文件依赖时，nodeid 匹配和收集顺序问题叠加，导致依赖不可靠

2. **收集顺序的影响**：
   - 如果依赖测试在被依赖测试之后收集，依赖关系无法正确建立
   - pytest 收集顺序受多种因素影响，具有不确定性
   - 即使在同一会话中，依赖关系也可能因收集顺序问题而失败

3. **混合策略优势**：
   - `test_state` 处理跨文件依赖，避免 pytest 收集顺序问题
   - `pytest-dependency` 处理同文件严格顺序依赖
   - 通过 `pytest_runtest_setup` hook 实现自动依赖检查

4. **实现效果**：
   - Flash 测试内部的严格执行顺序
   - Interface、Function、Performance 测试之间的跨文件依赖正确性
   - 测试执行的稳定性和可预测性
