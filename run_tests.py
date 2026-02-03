#!/usr/bin/env python3
"""
Test Runner Script / 测试运行脚本
"""
import sys
import subprocess
import argparse
from pathlib import Path


def run_pytest(args):
    """
    Run pytest with specified arguments / 使用指定参数运行pytest

    Args:
        args: Command line arguments / 命令行参数
    """
    project_root = Path(__file__).parent

    # Base pytest command / 基础pytest命令
    pytest_cmd = [
        sys.executable, "-m", "pytest",
        str(project_root / "tests"),
        "-v",
        "--tb=short",
        "--color=yes"
    ]

    # Add markers based on test type / 根据测试类型添加标记
    if args.test_type == 'all':
        # Run all tests / 运行所有测试
        pass
    elif args.test_type == 'flash':
        pytest_cmd.extend(["-m", "flash"])
    elif args.test_type == 'interface':
        pytest_cmd.extend(["-m", "interface"])
    elif args.test_type == 'function':
        pytest_cmd.extend(["-m", "function"])
    elif args.test_type == 'performance':
        pytest_cmd.extend(["-m", "performance"])

    # Add coverage if requested / 如果请求则添加覆盖率
    if args.coverage:
        pytest_cmd.extend([
            "--cov=src",
            "--cov-report=html",
            "--cov-report=term-missing",
            f"--cov-fail-under={args.coverage_threshold}"
        ])

    # Add parallel execution if requested / 如果请求则添加并行执行
    if args.parallel:
        pytest_cmd.extend(["-n", str(args.workers)])

    # Add maxfail option / 添加最大失败选项
    pytest_cmd.extend(["--maxfail", str(args.maxfail)])

    # Add timeout if specified / 如果指定则添加超时
    if args.timeout:
        pytest_cmd.extend(["--timeout", str(args.timeout)])

    print("\n" + "="*70)
    print("Running Pytest Test Framework / 运行Pytest测试框架")
    print("="*70)
    print(f"Test Type: {args.test_type}")
    print(f"Command: {' '.join(pytest_cmd)}")
    print("="*70 + "\n")

    # Run pytest / 运行pytest
    result = subprocess.run(pytest_cmd, cwd=project_root)

    # Generate Excel report if all tests passed / 如果所有测试通过则生成Excel报告
    if result.returncode == 0:
        try:
            from src.excel_report import generate_excel_report_from_artifacts
            artifacts_dir = project_root / "test_artifacts"
            if artifacts_dir.exists():
                generate_excel_report_from_artifacts(artifacts_dir)
        except ImportError:
            pass
        except Exception as e:
            print(f"Warning: Could not generate Excel report: {e}")

    return result.returncode


def main():
    """Main function / 主函数"""
    parser = argparse.ArgumentParser(
        description='Pytest Test Framework Runner / Pytest测试框架运行器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples / 示例:
  # Run all tests / 运行所有测试
  python run_tests.py --type all

  # Run only flash tests / 仅运行刷写测试
  python run_tests.py --type flash

  # Run interface and function tests / 运行接口和功能测试
  python run_tests.py --type interface
  python run_tests.py --type function

  # Run with coverage / 运行并生成覆盖率报告
  python run_tests.py --type all --coverage

  # Run tests in parallel / 并行运行测试
  python run_tests.py --type all --parallel --workers 4

  # Run performance tests / 运行性能测试
  python run_tests.py --type performance
        """
    )

    parser.add_argument(
        '--type', '-t',
        dest='test_type',
        choices=['all', 'flash', 'interface', 'function', 'performance'],
        default='all',
        help='Type of tests to run / 要运行的测试类型 (default: all)'
    )

    parser.add_argument(
        '--coverage', '-c',
        action='store_true',
        help='Run with coverage report / 运行并生成覆盖率报告'
    )

    parser.add_argument(
        '--coverage-threshold',
        type=int,
        default=95,
        help='Coverage threshold percentage / 覆盖率阈值百分比 (default: 95)'
    )

    parser.add_argument(
        '--parallel', '-p',
        action='store_true',
        help='Run tests in parallel / 并行运行测试'
    )

    parser.add_argument(
        '--workers', '-w',
        type=int,
        default=4,
        help='Number of workers for parallel execution / 并行执行的worker数量 (default: 4)'
    )

    parser.add_argument(
        '--maxfail', '-m',
        type=int,
        default=5,
        help='Stop after N failures / N次失败后停止 (default: 5)'
    )

    parser.add_argument(
        '--timeout',
        type=int,
        help='Test timeout in seconds / 测试超时时间(秒)'
    )

    args = parser.parse_args()

    return run_pytest(args)


if __name__ == "__main__":
    sys.exit(main())
