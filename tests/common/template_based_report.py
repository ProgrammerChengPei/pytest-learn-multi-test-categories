"""
Template-based Excel Report Generator / 基于模板的Excel报告生成器

使用Excel模板和JSON配置生成测试报告
"""
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from openpyxl import Workbook

try:
    from openpyxl import load_workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False
    print("⚠ openpyxl未安装，将跳过Excel报告生成")
    print("Install with: pip install openpyxl")


class TemplateBasedReportGenerator:
    """Template-based Excel report generator / 基于模板的Excel报告生成器"""

    def __init__(self, config_path: Path):
        """
        初始化报告生成器 / Initialize report generator

        Args:
            config_path: JSON配置文件路径 / JSON config file path
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.template_path = Path(self.config['template'])
        self.output_dir = Path(self.config['output_dir'])
        self.output_dir.mkdir(exist_ok=True, parents=True)

        self.test_results: List[Dict[str, Any]] = []
        self.start_time: float = 0
        self.end_time: float = 0

    def _load_config(self) -> Dict[str, Any]:
        """加载JSON配置 / Load JSON config"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def start(self):
        """开始计时 / Start timing"""
        self.start_time = time.time()

    def stop(self):
        """停止计时 / Stop timing"""
        self.end_time = time.time()

    def add_test_result(self, result: Dict[str, Any]):
        """
        添加测试结果 / Add test result

        Args:
            result: 测试结果字典 / Test result dictionary
        """
        self.test_results.append(result)

    def generate_report(self, filename: str = None) -> str:
        """
        生成报告 / Generate report

        Args:
            filename: 输出文件名 / Output filename

        Returns:
            生成的报告路径 / Generated report path
        """
        if not OPENPYXL_AVAILABLE:
            print("⚠ openpyxl未安装，跳过Excel报告生成")
            return ""

        # 如果模板不存在，创建默认模板 / Create default template if not exists
        if not self.template_path.exists():
            print(f"⚠ 模板文件不存在，将创建默认模板: {self.template_path}")
            self._create_default_template()

        # 加载模板 / Load template
        wb = load_workbook(str(self.template_path))

        # 准备数据 / Prepare data
        data = self._prepare_data()

        # 根据配置填充工作表 / Fill worksheets based on config
        for sheet_name, sheet_config in self.config['mappings'].items():
            if sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                sheet_type = sheet_config.get('type', 'list')

                if sheet_type == 'summary':
                    self._fill_summary_sheet(ws, sheet_config, data)
                elif sheet_type == 'list':
                    self._fill_list_sheet(ws, sheet_config, data)
                elif sheet_type == 'testcase_mapping':
                    self._fill_testcase_mapping_sheet(ws, sheet_config, data)

        # 生成文件名 / Generate filename
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"test_report_{timestamp}.xlsx"

        # 保存报告 / Save report
        output_path = self.output_dir / filename
        wb.save(str(output_path))

        print(f"✓ Excel报告已生成: {output_path}")
        return str(output_path)

    def _prepare_data(self) -> Dict[str, Any]:
        """
        准备数据用于填充模板 / Prepare data for template filling

        Returns:
            数据字典 / Data dictionary
        """
        # 计算统计信息 / Calculate statistics
        total = len(self.test_results)
        passed = len([r for r in self.test_results if r.get('status') == 'passed'])
        failed = len([r for r in self.test_results if r.get('status') == 'failed'])
        skipped = len([r for r in self.test_results if r.get('status') == 'skipped'])

        # 按类型统计 / Statistics by type
        type_stats = {
            'flash': {'total': 0, 'passed': 0, 'failed': 0},
            'interface': {'total': 0, 'passed': 0, 'failed': 0},
            'function': {'total': 0, 'passed': 0, 'failed': 0},
            'performance': {'total': 0, 'passed': 0, 'failed': 0}
        }

        for result in self.test_results:
            category = result.get('category', '')
            if category in type_stats:
                type_stats[category]['total'] += 1
                if result.get('status') == 'passed':
                    type_stats[category]['passed'] += 1
                elif result.get('status') == 'failed':
                    type_stats[category]['failed'] += 1

        # 计算通过率 / Calculate pass rate
        for stats in type_stats.values():
            if stats['total'] > 0:
                stats['pass_rate'] = stats['passed'] / stats['total']
            else:
                stats['pass_rate'] = 0.0

        return {
            'session': {
                'report_time': datetime.now(),
                'total_duration': self.end_time - self.start_time
            },
            'stats': {
                'total': total,
                'passed': passed,
                'failed': failed,
                'skipped': skipped,
                'flash': type_stats['flash'],
                'interface': type_stats['interface'],
                'function': type_stats['function'],
                'performance': type_stats['performance']
            },
            'results': self.test_results
        }

    def _fill_summary_sheet(self, ws, sheet_config: Dict[str, Any], data: Dict[str, Any]):
        """
        填充汇总工作表 / Fill summary worksheet

        Args:
            ws: 工作表对象 / Worksheet object
            sheet_config: 工作表配置 / Worksheet config
            data: 数据字典 / Data dictionary
        """
        # 填充单个字段 / Fill single fields
        fields = sheet_config.get('fields', {})
        for field_name, field_config in fields.items():
            cell = ws[field_config['cell']]
            value = self._get_value(field_config['source'], data)

            # 格式化值 / Format value
            formatted_value = self._format_value(value, field_config)
            cell.value = formatted_value

        # 填充类型统计 / Fill type statistics
        type_stats_config = sheet_config.get('type_stats', {})
        if type_stats_config:
            self._fill_type_stats(ws, type_stats_config, data)

    def _fill_type_stats(self, ws, type_stats_config: Dict[str, Any], data: Dict[str, Any]):
        """
        填充类型统计 / Fill type statistics

        Args:
            ws: 工作表对象 / Worksheet object
            type_stats_config: 类型统计配置 / Type statistics config
            data: 数据字典 / Data dictionary
        """
        columns = type_stats_config.get('columns', {})
        row_mapping = type_stats_config.get('row_mapping', {})
        fields = type_stats_config.get('fields', {})

        for type_name, row_num in row_mapping.items():
            type_data = data['stats'].get(type_name, {})

            # 填充名称 / Fill name
            name_cell = ws[f"{columns['测试类型 / Type']}{row_num}"]
            name_cell.value = type_name

            # 填充统计数据 / Fill statistics
            for stat_key, stat_config in fields.get(type_name, {}).items():
                col_letter = columns.get(stat_key)
                if col_letter:
                    cell = ws[f"{col_letter}{row_num}"]
                    value = self._get_value(stat_config['source'], type_data)
                    formatted_value = self._format_value(value, stat_config)
                    cell.value = formatted_value

    def _fill_list_sheet(self, ws, sheet_config: Dict[str, Any], data: Dict[str, Any]):
        """
        填充列表工作表 / Fill list worksheet

        Args:
            ws: 工作表对象 / Worksheet object
            sheet_config: 工作表配置 / Worksheet config
            data: 数据字典 / Data dictionary
        """
        start_row = sheet_config.get('start_row', 2)
        columns = sheet_config.get('columns', {})

        # 填充每一行 / Fill each row
        for index, result in enumerate(data['results']):
            row_num = start_row + index

            for col_name, col_config in columns.items():
                col_letter = col_config['col']
                cell = ws[f"{col_letter}{row_num}"]

                # 获取值 / Get value
                source = col_config.get('source')
                fallback = col_config.get('fallback')

                if source == 'index':
                    value = index + 1
                else:
                    value = result.get(source, '')
                    # 如果值不存在且配置了fallback，则使用fallback
                    # If value doesn't exist and fallback is configured, use fallback
                    if not value and fallback:
                        value = result.get(fallback, '')

                # 格式化值 / Format value
                formatted_value = self._format_value(value, col_config)
                cell.value = formatted_value

                # 应用样式 / Apply style
                if 'style' in col_config and source == 'status':
                    status_style = col_config['style'].get(str(value).lower())
                    if status_style:
                        fill_color = status_style.get('fill')
                        if fill_color:
                            cell.fill = PatternFill(
                                start_color=fill_color,
                                end_color=fill_color,
                                fill_type='solid'
                            )

    def _get_value(self, source: str, data: Dict[str, Any]) -> Any:
        """
        根据source路径获取值 / Get value by source path

        Args:
            source: 数据源路径 / Data source path (e.g., "stats.total")
            data: 数据字典 / Data dictionary

        Returns:
            获取的值 / Retrieved value
        """
        keys = source.split('.')
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

        return value

    def _format_value(self, value: Any, config: Dict[str, Any]) -> Any:
        """
        格式化值 / Format value

        Args:
            value: 原始值 / Original value
            config: 格式配置 / Format config

        Returns:
            格式化后的值 / Formatted value
        """
        if value is None:
            return ''

        format_type = config.get('format', 'string')

        if format_type == 'datetime':
            if isinstance(value, datetime):
                return value.strftime('%Y-%m-%d %H:%M:%S')
            return str(value)

        elif format_type == 'number':
            decimals = config.get('decimals', 2)
            unit = config.get('unit', '')
            try:
                formatted = f"{float(value):.{decimals}f}"
                return formatted + unit
            except (ValueError, TypeError):
                return str(value)

        elif format_type == 'percent':
            try:
                return f"{float(value) * 100:.1f}%"
            except (ValueError, TypeError):
                return '0.0%'

        else:  # string
            return str(value)

    def _create_default_template(self):
        """创建默认模板 / Create default template"""
        if not OPENPYXL_AVAILABLE:
            print("⚠ openpyxl未安装，无法创建模板")
            return

        from openpyxl import Workbook

        wb = Workbook()
        if 'Sheet' in wb.sheetnames:
            del wb['Sheet']

        # 创建汇总工作表 / Create summary sheet
        self._create_default_summary_sheet(wb)

        # 创建详情工作表 / Create details sheet
        self._create_default_details_sheet(wb)

        # 创建测试用例映射工作表 / Create testcase mapping sheet
        self._create_default_testcase_mapping_sheet(wb)

        # 保存模板 / Save template
        self.template_path.parent.mkdir(exist_ok=True, parents=True)
        wb.save(str(self.template_path))

    def _create_default_summary_sheet(self, wb: Workbook):
        """创建默认汇总工作表 / Create default summary sheet"""
        ws = wb.create_sheet("测试汇总 Summary", 0)

        # 标题样式 / Title style
        title_font = Font(name='微软雅黑', size=16, bold=True, color='FFFFFF')
        title_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')

        ws.merge_cells('A1:E1')
        title_cell = ws['A1']
        title_cell.value = "Pytest 测试报告 / Pytest Test Report"
        title_cell.font = title_font
        title_cell.fill = title_fill
        title_cell.alignment = Alignment(horizontal='center', vertical='center')

        # 测试信息标签 / Test info labels
        info_labels = [
            ("报告生成时间 / Report Time", "A3"),
            ("测试总耗时 / Total Duration", "A4"),
            ("测试总数 / Total Tests", "A5"),
            ("通过数 / Passed", "A6"),
            ("失败数 / Failed", "A7"),
            ("跳过数 / Skipped", "A8"),
        ]

        for label, cell in info_labels:
            ws[cell] = label

        # 测试类型统计 / Test type statistics
        ws['A10'] = "按测试类型统计 / Statistics by Type"
        ws['A10'].font = title_font
        ws['A10'].fill = title_fill
        ws.merge_cells('A10:E10')

        # 表头 / Headers
        type_headers = ["测试类型 / Type", "总数 / Total", "通过 / Passed", "失败 / Failed", "通过率 / Pass Rate"]
        header_font = Font(name='微软雅黑', size=11, bold=True)
        header_fill = PatternFill(start_color='D9E1F2', end_color='D9E1F2', fill_type='solid')

        for col, header in enumerate(type_headers, 1):
            cell = ws.cell(row=11, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center')

        # 类型名称 / Type names
        type_names = ["刷写 / Flash", "接口 / Interface", "功能 / Function", "性能 / Performance"]
        for idx, name in enumerate(type_names, 12):
            ws[f'A{idx}'] = name

    def _create_default_details_sheet(self, wb: Workbook):
        """创建默认详情工作表 / Create default details sheet"""
        ws = wb.create_sheet("测试详情 TestDetails", 1)

        # 表头 / Headers
        headers = [
            "序号 / No",
            "测试名称 / Test Name",
            "测试类型 / Test Type",
            "状态 / Status",
            "耗时 / Duration (s)",
            "文件 / File",
            "行号 / Line",
            "消息 / Message",
            "性能指标 / Metric",
            "指标值 / Metric Value"
        ]

        header_font = Font(name='微软雅黑', size=11, bold=True)
        header_fill = PatternFill(start_color='D9E1F2', end_color='D9E1F2', fill_type='solid')
        widths = [6, 35, 15, 12, 15, 40, 8, 50, 20, 20]

        for col_idx, (header, width) in enumerate(zip(headers, widths), 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')
            ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = width

        # 冻结首行 / Freeze first row
        ws.freeze_panes = 'A2'

    def _create_default_testcase_mapping_sheet(self, wb: Workbook):
        """创建默认测试用例映射工作表 / Create default testcase mapping sheet"""
        ws = wb.create_sheet("测试用例 TestCases", 2)

        # 表头 / Headers
        headers = [
            "序号 / No",
            "测试用例名称 / Test Case Name",
            "测试类型 / Test Type",
            "测试结果 / Test Result",
            "说明 / Description"
        ]

        header_font = Font(name='微软雅黑', size=11, bold=True)
        header_fill = PatternFill(start_color='D9E1F2', end_color='D9E1F2', fill_type='solid')
        widths = [6, 30, 15, 12, 60]

        for col_idx, (header, width) in enumerate(zip(headers, widths), 1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')
            ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = width

        # 添加示例数据 / Add example data
        example_data = [
            (2, "测试abc", "Flash", "", ""),
            (3, "连接设备", "Flash", "", ""),
            (4, "准备刷写", "Flash", "", ""),
            (5, "API登录测试", "Interface", "", ""),
            (6, "API登出测试", "Interface", "", ""),
            (7, "获取设备状态", "Interface", "", ""),
            (8, "用户注册流程", "Function", "", ""),
            (9, "用户登录测试", "Function", "", ""),
            (10, "响应时间测试", "Performance", "", ""),
        ]

        for row_idx, (no, name, test_type, result, desc) in enumerate(example_data, 2):
            ws.cell(row=row_idx, column=1, value=no)
            ws.cell(row=row_idx, column=2, value=name)
            ws.cell(row=row_idx, column=3, value=test_type)
            ws.cell(row=row_idx, column=4, value=result)
            ws.cell(row=row_idx, column=5, value=desc)

        # 冻结首行 / Freeze first row
        ws.freeze_panes = 'A2'

    def _fill_testcase_mapping_sheet(self, ws, sheet_config: Dict[str, Any], data: Dict[str, Any]):
        """
        填充基于测试用例名称映射的工作表 / Fill testcase mapping sheet

        这个功能允许通过测试用例的中文名，将测试结果填充到Excel模板中指定的单元格。
        实现用例设计和用例脚本的对应关系。

        Excel模板示例：
        ----------------------------------------------------
        |    A       |       B       |   ...   |   J       |   K       |
        ----------------------------------------------------
        |    ...     |   测试用例名称  |   ...   |   测试结果 |   说明     |
        ----------------------------------------------------
        |    12      |   测试abc      |   ...   |           |           |
        ----------------------------------------------------
        |    13      |   测试def      |   ...   |           |           |
        ----------------------------------------------------

        Args:
            ws: 工作表对象 / Worksheet object
            sheet_config: 工作表配置 / Worksheet config
            data: 数据字典 / Data dictionary
        """
        name_column = sheet_config.get('name_column', 'B')
        result_column = sheet_config.get('result_column', 'J')
        docstring_column = sheet_config.get('docstring_column')  # 可选的docstring列
        result_mappings = sheet_config.get('result_mappings', {
            'passed': '通过',
            'failed': '失败',
            'skipped': '跳过'
        })

        # 扫描整个工作表，查找测试用例名称 / Scan entire worksheet for test case names
        max_row = ws.max_row

        # 构建测试结果映射表 / Build test result mapping table
        # key: 测试用例中文名, value: {status, docstring, name}
        test_result_map = {}
        for result in data['results']:
            chinese_name = result.get('chinese_name')
            if chinese_name:
                status = result.get('status', 'skipped')
                # 映射英文状态到中文显示 / Map English status to Chinese display
                mapped_status = result_mappings.get(status, status)
                # 获取docstring，如果没有则使用测试函数名 / Get docstring, use function name if not available
                docstring = result.get('message', '')
                if not docstring:
                    docstring = result.get('name', '')
                test_result_map[chinese_name] = {
                    'status': mapped_status,
                    'original_status': status,
                    'docstring': docstring
                }

        # 遍历工作表中的每一行，查找匹配的测试用例名称 / Iterate through each row
        found_tests = 0
        for row in range(1, max_row + 1):
            # 获取名称列的单元格值 / Get value from name column
            name_cell = ws[f'{name_column}{row}']
            test_name = str(name_cell.value).strip() if name_cell.value else ''

            # 如果单元格不为空且在测试结果映射表中
            if test_name and test_name in test_result_map:
                test_info = test_result_map[test_name]

                # 填充结果列 / Fill result column
                result_cell = ws[f'{result_column}{row}']
                result_cell.value = test_info['status']

                # 应用颜色样式 / Apply color style
                if test_info['original_status'] == 'passed':
                    result_cell.fill = PatternFill(
                        start_color='C6EFCE',
                        end_color='C6EFCE',
                        fill_type='solid'
                    )
                elif test_info['original_status'] == 'failed':
                    result_cell.fill = PatternFill(
                        start_color='FFC7CE',
                        end_color='FFC7CE',
                        fill_type='solid'
                    )
                elif test_info['original_status'] == 'skipped':
                    result_cell.fill = PatternFill(
                        start_color='FFEB9C',
                        end_color='FFEB9C',
                        fill_type='solid'
                    )

                # 填充docstring列（如果配置了的话）/ Fill docstring column (if configured)
                if docstring_column:
                    docstring_cell = ws[f'{docstring_column}{row}']
                    docstring_cell.value = test_info['docstring']

                found_tests += 1

        print(f"  ✓ 填充了 {found_tests} 个测试用例结果 / Filled {found_tests} test case results")


def generate_report_from_template(config_path: Path) -> str:
    """
    从模板生成报告的便捷函数 / Convenience function to generate report from template

    Args:
        config_path: 配置文件路径 / Config file path

    Returns:
        生成的报告路径 / Generated report path
    """
    generator = TemplateBasedReportGenerator(config_path)
    return generator.generate_report()
