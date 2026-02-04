"""
Function Test Cases / 功能测试用例
使用全名 nodeid 进行依赖声明，验证跨文件依赖
"""
import pytest


class TestFunction:
    """Function test class / 功能测试类"""

    @pytest.mark.function
    @pytest.mark.dependency(
        name="tests2.function_tests.test_function.TestFunction#test_function_basic",
        depends=["tests2.interface_tests.test_interface.TestInterface#test_interface_complete"]
    )
    def test_function_basic(self):
        """
        Test basic function / 测试基本功能

        依赖完整的 nodeid: tests2.interface_tests.test_interface.TestInterface#test_interface_complete
        """
        print("✓ test_function_basic 执行")
        assert True

    @pytest.mark.function
    @pytest.mark.dependency(
        name="tests2.function_tests.test_function.TestFunction#test_function_advanced",
        depends=["tests2.function_tests.test_function.TestFunction#test_function_basic"]
    )
    def test_function_advanced(self):
        """
        Test advanced function / 测试高级功能

        依赖同文件的完整 nodeid
        """
        print("✓ test_function_advanced 执行")
        assert True

    @pytest.mark.function
    @pytest.mark.dependency(
        name="tests2.function_tests.test_function.TestFunction#test_function_complete",
        depends=["tests2.function_tests.test_function.TestFunction#test_function_advanced"]
    )
    def test_function_complete(self):
        """
        Test function completion / 测试功能完成

        使用完整的 nodeid 作为依赖名称
        这是 performance 测试的依赖目标
        """
        print("✓ test_function_complete 执行（标记为依赖目标）")
        assert True
