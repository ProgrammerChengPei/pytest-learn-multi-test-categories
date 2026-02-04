"""
Interface Test Cases / 接口测试用例
使用全名 nodeid 进行依赖声明，验证跨文件依赖
"""
import pytest


class TestInterface:
    """Interface test class / 接口测试类"""

    @pytest.mark.interface
    @pytest.mark.dependency(
        name="tests2.interface_tests.test_interface.TestInterface#test_interface_get_status",
        depends=["tests2.flash_tests.test_flash.TestFlash#test_flash_complete"]
    )
    def test_interface_get_status(self):
        """
        Test get_status interface / 测试get_status接口

        依赖完整的 nodeid: tests2.flash_tests.test_flash.TestFlash#test_flash_complete
        """
        print("✓ test_interface_get_status 执行")
        assert True

    @pytest.mark.interface
    @pytest.mark.dependency(
        name="tests2.interface_tests.test_interface.TestInterface#test_interface_health_check",
        depends=["tests2.interface_tests.test_interface.TestInterface#test_interface_get_status"]
    )
    def test_interface_health_check(self):
        """
        Test health_check interface / 测试health_check接口

        依赖同文件的完整 nodeid
        """
        print("✓ test_interface_health_check 执行")
        assert True

    @pytest.mark.interface
    @pytest.mark.dependency(
        name="tests2.interface_tests.test_interface.TestInterface#test_interface_complete",
        depends=["tests2.interface_tests.test_interface.TestInterface#test_interface_health_check"]
    )
    def test_interface_complete(self):
        """
        Test interface completion / 测试接口完成

        使用完整的 nodeid 作为依赖名称
        这是 function 测试的依赖目标
        """
        print("✓ test_interface_complete 执行（标记为依赖目标）")
        assert True
