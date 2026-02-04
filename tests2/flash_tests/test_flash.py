"""
Flash/Firmware Test Cases / 刷写/固件测试用例
使用全名 nodeid 进行依赖声明
"""
import pytest


class TestFlash:
    """Flash test class / 刷写测试类"""

    @pytest.mark.flash
    @pytest.mark.dependency(
        name="tests2.flash_tests.test_flash.TestFlash#test_flash_connection"
    )
    def test_flash_connection(self):
        """
        Test flash connection / 测试刷写连接

        使用完整的 nodeid 作为依赖名称
        """
        print("✓ test_flash_connection 执行")
        assert True

    @pytest.mark.flash
    @pytest.mark.dependency(
        name="tests2.flash_tests.test_flash.TestFlash#test_flash_prepare",
        depends=["tests2.flash_tests.test_flash.TestFlash#test_flash_connection"]
    )
    def test_flash_prepare(self):
        """
        Test flash preparation / 测试刷写准备

        依赖完整的 nodeid
        """
        print("✓ test_flash_prepare 执行")
        assert True

    @pytest.mark.flash
    @pytest.mark.dependency(
        name="tests2.flash_tests.test_flash.TestFlash#test_flash_upload",
        depends=["tests2.flash_tests.test_flash.TestFlash#test_flash_prepare"]
    )
    def test_flash_upload(self):
        """
        Test flash upload / 测试刷写上传

        依赖完整的 nodeid
        """
        print("✓ test_flash_upload 执行")
        assert True

    @pytest.mark.flash
    @pytest.mark.dependency(
        name="tests2.flash_tests.test_flash.TestFlash#test_flash_complete",
        depends=["tests2.flash_tests.test_flash.TestFlash#test_flash_upload"]
    )
    def test_flash_complete(self):
        """
        Test flash completion / 测试刷写完成

        使用完整的 nodeid 作为依赖名称
        这是 interface 测试的依赖目标
        """
        print("✓ test_flash_complete 执行（标记为依赖目标）")
        assert True
