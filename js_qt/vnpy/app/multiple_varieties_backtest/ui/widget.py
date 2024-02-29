
import csv
from copy import copy
from datetime import datetime, timedelta

from vnpy.trader.ui.editor import CodeEditor

from vnpy.app.cta_strategy import OptimizationSetting
from vnpy.app.multiple_varieties_backtest.base import EVENT_MULTIPLE_VARIETIES_BACK_TEST_LOG, \
    EVENT_MULTIPLE_VARIETIES_BACK_TEST_FINISHED, EVENT_MULTIPLE_VARIETIES_BACK_OPTIMIZATION_FINISHED
from vnpy.event import Event, EventEngine
from vnpy.trader.constant import Interval
from vnpy.trader.engine import MainEngine
from vnpy.trader.symbol_attr import ContractMultiplier, ContractPricePick
from vnpy.trader.ui import QtCore, QtWidgets, QtGui
from vnpy.trader.utility import load_json, save_json, get_letter_from_symbol, save_parameter_optimization_data_to_csv
from ..engine import (
    APP_NAME,
)
from ...utility import TerminateThread


class MultipleVarietiesBackTestManager(QtWidgets.QWidget):
    """
    多品种回测QWidget
    """

    setting_filename = "multiple_varieties_back_test_setting.json"

    signal_log = QtCore.pyqtSignal(Event)
    signal_backtesting_finished = QtCore.pyqtSignal(Event)
    signal_optimization_finished = QtCore.pyqtSignal(Event)

    def __init__(self, main_engine: MainEngine, event_engine: EventEngine):
        """"""
        super().__init__()

        self.main_engine = main_engine
        self.event_engine = event_engine

        self.backtester_engine = main_engine.get_engine(APP_NAME)
        self.class_names = []
        self.settings = {}
        self.target_display = None
        self.init_ui()
        self.register_event()
        self.backtester_engine.init_engine()
        self.init_strategy_settings()
        self.input_box_set_text()

    def init_strategy_settings(self):
        """加载json文件获取策略参数配置,设置到变量中,给策略交易下拉框中设置文本"""
        self.class_names = self.backtester_engine.get_strategy_class_names()  # 获取策略类名

        for class_name in self.class_names:
            setting = self.backtester_engine.get_default_setting(class_name)  # 根据策略类名获取策略参数
            self.settings[class_name] = setting

        self.class_combo.addItems(self.class_names)  # 交易策略下拉框中设置策略名

    def input_box_set_text(self):
        """从json文件中加载回测相关数据,设置到回测相关输入框中"""
        setting = load_json(self.setting_filename)  # 从json文件中加载回测相关的设置:比如开始时间,结束时间，交易滑点等。
        if not setting:
            return
        self.class_combo.setCurrentIndex(self.class_combo.findText(setting["class_name"]))
        self.symbol_line.setText(setting["vt_symbol"])
        self.interval_combo.setCurrentIndex(
            self.interval_combo.findText(setting["interval"])
        )
        self.rate_line.setText(str(setting["rate"]))
        self.slippage_line.setText(str(setting["slippage"]))
        self.capital_line.setText(str(setting["capital"]))
        if 'end' not in setting.keys():
            setting["end"] = datetime.now().strftime("%Y-%m-%d")
        if 'start' not in setting.keys():
            setting["start"] = datetime.now().strftime("%Y-%m-%d")
        self.end_date_edit.setDate(datetime.strptime(setting["end"], '%Y-%m-%d').date())
        self.start_date_edit.setDate(datetime.strptime(setting["start"], '%Y-%m-%d').date())
        if not setting["inverse"]:
            self.inverse_combo.setCurrentIndex(0)
        else:
            self.inverse_combo.setCurrentIndex(1)

    def init_ui(self):
        """"""
        self.setWindowTitle("多品种回测")
        self.class_combo = QtWidgets.QComboBox()
        self.symbol_line = QtWidgets.QTextEdit(
            "JD8888.XDCE,AP8888.XZCE,OI8888.XZCE,CF8888.XZCE,RM8888.XZCE,Y8888.XDCE,CS8888.XDCE,A8888.XDCE,"
            "M8888.XDCE,P8888.XDCE,SR8888.XZCE,RB8888.XSGE,I8888.XDCE,SS8888.XSGE,CU8888.XSGE,"
            "AL8888.XSGE,ZN8888.XSGE,NI8888.XSGE,HC8888.XSGE,SF8888.XZCE,SM8888.XZCE,FU8888.XSGE,ZC8888.XZCE,"
            "JM8888.XDCE,J8888.XDCE,TA8888.XZCE,FG8888.XZCE,BU8888.XSGE,L8888.XDCE,MA8888.XZCE,PP8888.XDCE,"
            "SP8888.XSGE,RU8888.XSGE,EG8888.XDCE,EB8888.XDCE,SA8888.XZCE")

        self.interval_combo = QtWidgets.QComboBox()
        for inteval in Interval:
            self.interval_combo.addItem(inteval.value)

        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=3 * 365)

        self.start_date_edit = QtWidgets.QDateEdit(
            QtCore.QDate(
                start_dt.year,
                start_dt.month,
                start_dt.day,
            )
        )
        self.end_date_edit = QtWidgets.QDateEdit(
            QtCore.QDate.currentDate()
        )

        self.rate_line = QtWidgets.QLineEdit("0")
        self.slippage_line = QtWidgets.QLineEdit("0.2")
        self.capital_line = QtWidgets.QLineEdit("1000000")

        self.inverse_combo = QtWidgets.QComboBox()
        self.inverse_combo.addItems(["正向", "反向"])

        backtesting_button = QtWidgets.QPushButton("开始回测")
        backtesting_button.clicked.connect(self.start_backtesting)

        backtesting_stop_button = QtWidgets.QPushButton("停止回测")
        backtesting_stop_button.clicked.connect(self.stop_backtesting)

        optimization_button = QtWidgets.QPushButton("参数优化")
        optimization_button.clicked.connect(self.start_optimization)

        self.result_button = QtWidgets.QPushButton("优化结果")
        self.result_button.clicked.connect(self.show_optimization_result)
        self.result_button.setEnabled(False)

        edit_button = QtWidgets.QPushButton("代码编辑")
        edit_button.clicked.connect(self.edit_strategy_code)

        reload_button = QtWidgets.QPushButton("策略重载")
        reload_button.clicked.connect(self.reload_strategy_class)

        for button in [
            backtesting_button,
            backtesting_stop_button,
            optimization_button,
            self.result_button,
            edit_button,
            reload_button
        ]:
            button.setFixedHeight(button.sizeHint().height() * 2)

        form = QtWidgets.QFormLayout()
        form.addRow("交易策略", self.class_combo)
        form.addRow("本地代码", self.symbol_line)
        form.addRow("K线周期", self.interval_combo)
        form.addRow("开始日期", self.start_date_edit)
        form.addRow("结束日期", self.end_date_edit)
        form.addRow("手续费率", self.rate_line)
        form.addRow("交易滑点", self.slippage_line)
        form.addRow("回测资金", self.capital_line)
        form.addRow("合约模式", self.inverse_combo)

        left_vbox = QtWidgets.QVBoxLayout()
        left_vbox.addLayout(form)
        left_vbox.addWidget(backtesting_button)
        left_vbox.addWidget(backtesting_stop_button)
        left_vbox.addStretch()
        left_vbox.addWidget(optimization_button)
        left_vbox.addWidget(self.result_button)
        left_vbox.addStretch()
        left_vbox.addWidget(edit_button)
        left_vbox.addWidget(reload_button)

        # 日志监测部件
        self.log_monitor = QtWidgets.QTextEdit()
        self.log_monitor.setMaximumHeight(400)
        left_vbox.addWidget(self.log_monitor)

        # 指标统计监测部件
        self.statistics_monitor = StatisticsMonitor()

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.statistics_monitor)


        hbox = QtWidgets.QHBoxLayout()
        hbox.addLayout(left_vbox, stretch=1)
        hbox.addLayout(vbox, stretch=10)

        self.setLayout(hbox)

        # Code Editor
        self.editor = CodeEditor(self.main_engine, self.event_engine)

    def register_event(self):
        """"""
        self.signal_log.connect(self.process_log_event)
        self.signal_backtesting_finished.connect(self.process_backtesting_finished_event)
        self.signal_optimization_finished.connect(self.process_optimization_finished_event)
        self.event_engine.register(EVENT_MULTIPLE_VARIETIES_BACK_TEST_LOG, self.signal_log.emit)
        self.event_engine.register(EVENT_MULTIPLE_VARIETIES_BACK_TEST_FINISHED, self.signal_backtesting_finished.emit)
        self.event_engine.register(EVENT_MULTIPLE_VARIETIES_BACK_OPTIMIZATION_FINISHED, self.signal_optimization_finished.emit)

    def process_log_event(self, event: Event):
        """"""
        msg = event.data
        self.write_log(msg)

    def write_log(self, msg):
        """"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        msg = f"{timestamp}\t{msg}"
        self.log_monitor.append(msg)

    def process_backtesting_finished_event(self, event: Event):  # 会传两次回测完成的事件
        """"""
        if self.exec_func:
            if event:
                exec_statistics = copy(self.backtester_engine.get_result_statistics())  # 获取前一个运行策略的统计数据
                self.statistics_monitor.set_data(exec_statistics)
            the_class, par = self.exec_func.pop(0)
            the_class(*par)
            return
        else:
            statistics = self.backtester_engine.get_result_statistics()  # 获取最后一个运行策略的统计数据
            self.statistics_monitor.set_data(statistics)

    def process_optimization_finished_event(self, event: Event):
        """"""
        if self.exec_func_optimization:
            if event:
                self.result_values.extend(self.backtester_engine.get_result_values())
            the_class, par = self.exec_func_optimization.pop(0)
            the_class(*par)
        else:
            self.result_values.extend(self.backtester_engine.get_result_values())
            self.write_log("请点击[优化结果]按钮查看")
            self.result_button.setEnabled(True)

    def stop_backtesting(self):
        TerminateThread().stop(self)
        self.backtester_engine.thread = None

    def start_backtesting(self):
        """"""
        class_name = self.class_combo.currentText()
        self.vt_symbol_list = self.symbol_line.toPlainText().split(",")
        interval = self.interval_combo.currentText()
        start = self.start_date_edit.date().toPyDate()
        end = self.end_date_edit.date().toPyDate()
        rate = float(self.rate_line.text())
        slippage = float(self.slippage_line.text())
        capital = float(self.capital_line.text())

        if self.inverse_combo.currentText() == "正向":
            inverse = False
        else:
            inverse = True

        # Save backtesting parameters
        backtesting_setting = {
            "class_name": class_name,
            "vt_symbol": self.symbol_line.toPlainText(),
            "interval": interval,
            "rate": rate,
            "slippage": slippage,
            "capital": capital,
            "inverse": inverse,
            "start": start.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d")
        }
        save_json(self.setting_filename, backtesting_setting)

        # Get strategy setting
        old_setting = self.settings[class_name]  # 策略参数配置
        dialog = BacktestingSettingEditor(class_name, old_setting)  # 生成点击开始回测时,弹出的策略参数配置对话框对象。
        i = dialog.exec()
        if i != dialog.Accepted:
            return

        new_setting = dialog.get_setting()  # 获取策略参数配置对话框中的内容
        self.settings[class_name] = new_setting  # 把新的策略参数配置内容保存到变量中去

        self.exec_func = []  # 记录准备执行的方法
        for vt_symbol in self.vt_symbol_list:
            # 获取合约代码的字母部分
            symbol_letter = get_letter_from_symbol(vt_symbol.split(".")[0])
            size = ContractMultiplier[symbol_letter]
            pricetick = ContractPricePick[symbol_letter]
            # 记录方法操作
            self.exec_func.append([self.backtester_engine.start_backtesting, [
                class_name,
                vt_symbol,
                interval,
                start,
                end,
                rate,
                slippage,
                size,
                pricetick,
                capital,
                inverse,
                new_setting]])

        self.process_backtesting_finished_event(None)

        if True:
            self.statistics_monitor.clear_data(self.vt_symbol_list)

    def start_optimization(self):
        """"""
        class_name = self.class_combo.currentText()
        self.vt_symbol_list = self.symbol_line.toPlainText().split(",")
        interval = self.interval_combo.currentText()
        start = self.start_date_edit.date().toPyDate()
        end = self.end_date_edit.date().toPyDate()
        rate = float(self.rate_line.text())
        slippage = float(self.slippage_line.text())
        capital = float(self.capital_line.text())

        if self.inverse_combo.currentText() == "正向":
            inverse = False
        else:
            inverse = True

        parameters = self.settings[class_name]
        dialog = OptimizationSettingEditor(class_name, parameters)
        i = dialog.exec()
        if i != dialog.Accepted:
            return

        self.result_values = []
        optimization_setting, use_ga = dialog.get_setting()
        self.target_display = dialog.target_display

        self.exec_func_optimization = []  # 记录准备执行的方法
        for vt_symbol in self.vt_symbol_list:
            # 获取合约代码的字母部分
            symbol_letter = get_letter_from_symbol(vt_symbol.split(".")[0])
            size = ContractMultiplier[symbol_letter]
            pricetick = ContractPricePick[symbol_letter]
            # 记录方法操作
            self.exec_func_optimization.append([self.backtester_engine.start_optimization, [
                class_name,
                vt_symbol,
                interval,
                start,
                end,
                rate,
                slippage,
                size,
                pricetick,
                capital,
                inverse,
                optimization_setting,
                use_ga]])

        self.process_optimization_finished_event(None)
        self.result_button.setEnabled(False)

    def show_optimization_result(self):
        """"""
        dialog = OptimizationResultMonitor(
            self.result_values,
            self.target_display
        )
        dialog.exec_()

    def edit_strategy_code(self):
        """"""
        class_name = self.class_combo.currentText()
        file_path = self.backtester_engine.get_strategy_class_file(class_name)

        self.editor.open_editor(file_path)
        self.editor.show()

    def reload_strategy_class(self):
        """"""
        self.backtester_engine.reload_strategy_class()

        self.class_combo.clear()
        self.init_strategy_settings()

    def show(self):
        """"""
        self.showMaximized()


class StatisticsMonitor(QtWidgets.QTableWidget):
    """"""
    KEY_NAME_MAP = {
        "start_date": "首个交易日",
        "end_date": "最后交易日",
        "total_days": "总交易日",
        "profit_days": "盈利交易日",
        "loss_days": "亏损交易日",
        "capital": "起始资金",
        "end_balance": "结束资金",
        "total_return": "总收益率",
        "annual_return": "年化收益",
        "max_drawdown": "最大回撤",
        "max_ddpercent": "百分比最大回撤",
        "total_net_pnl": "总盈亏",
        "total_commission": "总手续费",
        "total_slippage": "总滑点",
        "total_turnover": "总成交额",
        "total_trade_count": "总成交笔数",
        "daily_return": "日均收益率",
        "return_std": "收益标准差",
        "sharpe_ratio": "夏普比率",
        "win_ratio": "胜率",
        "win_loss_ratio": "盈亏比",
        "return_risk_ratio": "收益风险比",
        "return_drawdown_ratio": "收益回撤比",
        "real_yields": "实际收益率"
    }

    def __init__(self):
        """"""
        super().__init__()

        self.init_ui()

    def init_ui(self):
        """"""
        self.setColumnCount(len(self.KEY_NAME_MAP))
        self.horizontalHeader().setVisible(True)
        self.setHorizontalHeaderLabels(list(self.KEY_NAME_MAP.values()))
        self.horizontalHeader().setSectionResizeMode(
            QtWidgets.QHeaderView.Stretch
        )  # 均匀拉直表头(屏幕剩余可用范围所有列均等平分)

        self.setRowCount(0)

        self.setEditTriggers(self.NoEditTriggers)

        self.menu = QtWidgets.QMenu(self)   # 添加菜单
        resize_action = QtWidgets.QAction("调整列宽", self)
        resize_action.triggered.connect(self.resize_columns)
        self.menu.addAction(resize_action)

        save_action = QtWidgets.QAction("保存数据", self)
        save_action.triggered.connect(self.save_csv)
        self.menu.addAction(save_action)

    def clear_data(self, vt_symbol_list):
        """"""
        self.vt_symbol_list = vt_symbol_list
        self.location = 0
        self.clearContents()  # 清除表格中内容
        self.setRowCount(len(self.vt_symbol_list))  # 重新设置行数
        self.setVerticalHeaderLabels(self.vt_symbol_list)

    def set_data(self, data: dict):
        """"""
        data["capital"] = f"{data['capital']:,.2f}"
        data["end_balance"] = f"{data['end_balance']:,.2f}"
        data["total_return"] = f"{data['total_return']:,.2f}%"
        data["annual_return"] = f"{data['annual_return']:,.2f}%"
        data["max_drawdown"] = f"{data['max_drawdown']:,.2f}"
        data["max_ddpercent"] = f"{data['max_ddpercent']:,.2f}%"
        data["total_net_pnl"] = f"{data['total_net_pnl']:,.2f}"
        data["total_commission"] = f"{data['total_commission']:,.2f}"
        data["total_slippage"] = f"{data['total_slippage']:,.2f}"
        data["total_turnover"] = f"{data['total_turnover']:,.2f}"
        data["daily_net_pnl"] = f"{data['daily_net_pnl']:,.2f}"
        data["daily_commission"] = f"{data['daily_commission']:,.2f}"
        data["daily_slippage"] = f"{data['daily_slippage']:,.2f}"
        data["daily_turnover"] = f"{data['daily_turnover']:,.2f}"
        data["daily_return"] = f"{data['daily_return']:,.2f}%"
        data["return_std"] = f"{data['return_std']:,.2f}%"
        data["sharpe_ratio"] = f"{data['sharpe_ratio']:,.2f}"
        data["return_drawdown_ratio"] = f"{data['return_drawdown_ratio']:,.2f}"
        data["win_ratio"] = f"{data['win_ratio']}"
        data["win_loss_ratio"] = f"{data['win_loss_ratio']}"
        data["return_risk_ratio"] = f"{data['return_risk_ratio']:,.2f}"
        data["real_yields"] = f"{data['real_yields']}"

        # 往表格中设置元素
        for num, key in enumerate(self.KEY_NAME_MAP.keys()):
            cell = QtWidgets.QTableWidgetItem(str(data[key]))
            self.setItem(self.location, num, cell)

        self.location += 1

        self.resizeColumnsToContents()

    def resize_columns(self) -> None:
        """
        Resize all columns according to contents.
        """
        self.horizontalHeader().resizeSections(QtWidgets.QHeaderView.ResizeToContents)

    def save_csv(self) -> None:
        """
        Save table data into a csv file
        """
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "保存数据", "", "CSV(*.csv)")

        if not path:
            return
        try:
            with open(path, "w") as f:
                writer = csv.writer(f, lineterminator="\n")
                list_title = list(self.KEY_NAME_MAP.values())
                list_title.insert(0, "本地合约代码")
                writer.writerow(list_title)
                for row in range(self.rowCount()):
                    row_data = []
                    for column in range(self.columnCount()):
                        item = self.item(row, column)
                        if item:
                            row_data.append(str(item.text()))
                        else:
                            row_data.append("")
                    row_data.insert(0, self.vt_symbol_list[row])
                    writer.writerow(row_data)
        except PermissionError:
            QtWidgets.QMessageBox.critical(self, "保存失败", "写入的文件被打开,请关闭文件后再操作")

    def contextMenuEvent(self, event) -> None:
        """
        右键菜单事件
        """
        self.menu.popup(QtGui.QCursor.pos())  # 设置菜单显示位置


class BacktestingSettingEditor(QtWidgets.QDialog):
    """
    用于创建新策略或编辑策略参数的对话框
    """

    def __init__(
            self, class_name: str, parameters: dict
    ):
        """"""
        super(BacktestingSettingEditor, self).__init__()

        self.class_name = class_name
        self.parameters = parameters
        self.edits = {}

        self.init_ui()

    def init_ui(self):
        """"""
        form = QtWidgets.QFormLayout()

        # Add vt_symbol and name edit if add new strategy
        self.setWindowTitle(f"策略参数配置：{self.class_name}")
        button_text = "确定"
        parameters = self.parameters

        for name, value in parameters.items():
            type_ = type(value)

            edit = QtWidgets.QLineEdit(str(value))
            if type_ is int:
                validator = QtGui.QIntValidator()
                edit.setValidator(validator)
            elif type_ is float:
                validator = QtGui.QDoubleValidator()
                edit.setValidator(validator)

            form.addRow(f"{name} {type_}", edit)

            self.edits[name] = (edit, type_)

        button = QtWidgets.QPushButton(button_text)
        button.clicked.connect(self.accept)
        form.addRow(button)

        self.setLayout(form)

    def get_setting(self):
        """
        获取策略参数配置对话框中的内容：
            获取点击开始回测按钮时会弹出一个策略参数配置对话框
        """
        setting = {}

        for name, tp in self.edits.items():
            edit, type_ = tp
            value_text = edit.text()

            if type_ == bool:
                if value_text == "True":
                    value = True
                else:
                    value = False
            else:
                value = type_(value_text)

            setting[name] = value

        return setting


class OptimizationSettingEditor(QtWidgets.QDialog):
    """
    For setting up parameters for optimization.
    """
    DISPLAY_NAME_MAP = {
        "总收益率": "total_return",
        "夏普比率": "sharpe_ratio",
        "收益回撤比": "return_drawdown_ratio",
        "日均盈亏": "daily_net_pnl"
    }

    def __init__(
            self, class_name: str, parameters: dict
    ):
        """"""
        super().__init__()

        self.class_name = class_name
        self.parameters = parameters
        self.edits = {}

        self.optimization_setting = None
        self.use_ga = False

        self.init_ui()

    def init_ui(self):
        """初始化一个优化参数配置的表格"""
        QLabel = QtWidgets.QLabel

        self.target_combo = QtWidgets.QComboBox()
        self.target_combo.addItems(list(self.DISPLAY_NAME_MAP.keys()))

        grid = QtWidgets.QGridLayout()
        grid.addWidget(QLabel("目标"), 0, 0)
        grid.addWidget(self.target_combo, 0, 1, 1, 3)  # 目标设置下拉框
        grid.addWidget(QLabel("参数"), 1, 0)
        grid.addWidget(QLabel("开始"), 1, 1)
        grid.addWidget(QLabel("步进"), 1, 2)
        grid.addWidget(QLabel("结束"), 1, 3)

        self.setWindowTitle(f"优化参数配置：{self.class_name}")

        validator = QtGui.QDoubleValidator()
        row = 2
        # 设置策略参数的QLineEdit和QLabel
        for name, value in self.parameters.items():
            type_ = type(value)
            if type_ not in [int, float]:
                continue

            start_edit = QtWidgets.QLineEdit(str(value))
            step_edit = QtWidgets.QLineEdit(str(1))
            end_edit = QtWidgets.QLineEdit(str(value))

            for edit in [start_edit, step_edit, end_edit]:
                edit.setValidator(validator)

            grid.addWidget(QLabel(name), row, 0)
            grid.addWidget(start_edit, row, 1)
            grid.addWidget(step_edit, row, 2)
            grid.addWidget(end_edit, row, 3)

            self.edits[name] = {
                "type": type_,
                "start": start_edit,
                "step": step_edit,
                "end": end_edit
            }

            row += 1

        parallel_button = QtWidgets.QPushButton("多进程优化")
        parallel_button.clicked.connect(self.generate_parallel_setting)
        grid.addWidget(parallel_button, row, 0, 1, 4)

        row += 1
        ga_button = QtWidgets.QPushButton("遗传算法优化")
        ga_button.clicked.connect(self.generate_ga_setting)
        grid.addWidget(ga_button, row, 0, 1, 4)

        self.setLayout(grid)

    def generate_ga_setting(self):
        """生成遗传算法优化参数组合"""
        self.use_ga = True
        self.generate_setting()

    def generate_parallel_setting(self):
        """生成多进程优化参数组合"""
        self.use_ga = False
        self.generate_setting()

    def generate_setting(self):
        """生成策略优化组合配置参数"""
        self.optimization_setting = OptimizationSetting()

        self.target_display = self.target_combo.currentText()
        target_name = self.DISPLAY_NAME_MAP[self.target_display]
        self.optimization_setting.set_target(target_name)

        for name, d in self.edits.items():
            type_ = d["type"]
            start_value = type_(d["start"].text())
            step_value = type_(d["step"].text())
            end_value = type_(d["end"].text())

            if start_value == end_value:
                self.optimization_setting.add_parameter(name, start_value)
            else:
                self.optimization_setting.add_parameter(
                    name,
                    start_value,
                    end_value,
                    step_value
                )

        self.accept()

    def get_setting(self):
        """
        获取OptimizationSetting对象和use_ga
            OptimizationSetting:运行优化设置类。
            use_ga:传算法优化为True,多进程优化为false。
        """
        return self.optimization_setting, self.use_ga


class OptimizationResultMonitor(QtWidgets.QDialog):
    """
    For viewing optimization result.
    """

    def __init__(
            self, result_values: list, target_display: str
    ):
        """"""
        super().__init__()

        self.result_values = result_values
        self.target_display = target_display

        self.init_ui()

    def init_ui(self):
        """"""
        self.setWindowTitle("参数优化结果")
        self.resize(1100, 500)

        # Creat table to show result
        self.optimization_table = QtWidgets.QTableWidget()

        if self.result_values[0][2]:
            self.optimization_table.setColumnCount(10)
            self.table_head = ["参数", self.target_display, "年化收益率", "夏普比率", "胜率", "最大回撤比", "盈亏比", "收益风险比", "总成交笔数", "实际收益率"]
        else:
            self.optimization_table.setColumnCount(2)
            self.table_head = ["参数", self.target_display]

        self.optimization_table.setRowCount(len(self.result_values))
        self.optimization_table.setHorizontalHeaderLabels(self.table_head)
        self.optimization_table.setEditTriggers(self.optimization_table.NoEditTriggers)
        self.optimization_table.verticalHeader().setVisible(False)

        self.optimization_table.horizontalHeader().setSectionResizeMode(
            0, QtWidgets.QHeaderView.ResizeToContents
        )  # 对某列宽度设置

        self.optimization_table.horizontalHeader().setSectionResizeMode(
            1, QtWidgets.QHeaderView.Stretch
        )

        for n, tp in enumerate(self.result_values):
            setting, target_value, _ = tp

            # 构建cell对象
            setting_cell = QtWidgets.QTableWidgetItem(str(setting))  # 优化参数的cell对象
            target_cell = QtWidgets.QTableWidgetItem(str(f'{target_value:,.2f}'))  # 目标值的cell对象

            # 设置cell对象文本对齐方式
            setting_cell.setTextAlignment(QtCore.Qt.AlignCenter)
            target_cell.setTextAlignment(QtCore.Qt.AlignCenter)

            # 把cell设置到表格中去
            self.optimization_table.setItem(n, 0, setting_cell)
            self.optimization_table.setItem(n, 1, target_cell)

            if _:
                annual_return = QtWidgets.QTableWidgetItem(str(f'{_["annual_return"]:,.2f}'))
                sharpe_ratio = QtWidgets.QTableWidgetItem(str(f'{_["sharpe_ratio"]:,.2f}'))
                max_ddpercent = QtWidgets.QTableWidgetItem(str(f'{_["max_ddpercent"]:,.2f}'))
                total_trade_count = QtWidgets.QTableWidgetItem(str(_["total_trade_count"]))

                annual_return.setTextAlignment(QtCore.Qt.AlignCenter)
                sharpe_ratio.setTextAlignment(QtCore.Qt.AlignCenter)
                max_ddpercent.setTextAlignment(QtCore.Qt.AlignCenter)
                total_trade_count.setTextAlignment(QtCore.Qt.AlignCenter)

                self.optimization_table.setItem(n, 2, annual_return)
                self.optimization_table.setItem(n, 3, sharpe_ratio)
                self.optimization_table.setItem(n, 4, max_ddpercent)
                self.optimization_table.setItem(n, 5, total_trade_count)

                win_ratio = QtWidgets.QTableWidgetItem(str(f'{_["win_ratio"]}'))
                win_loss_ratio = QtWidgets.QTableWidgetItem(str(f'{_["win_loss_ratio"]}'))
                return_risk_ratio = QtWidgets.QTableWidgetItem(str(f'{_["return_risk_ratio"]:,.2f}'))
                real_yields = QtWidgets.QTableWidgetItem(_["real_yields"])

                win_ratio.setTextAlignment(QtCore.Qt.AlignCenter)
                win_loss_ratio.setTextAlignment(QtCore.Qt.AlignCenter)
                return_risk_ratio.setTextAlignment(QtCore.Qt.AlignCenter)
                real_yields.setTextAlignment(QtCore.Qt.AlignCenter)

                self.optimization_table.setItem(n, 6, win_ratio)
                self.optimization_table.setItem(n, 7, win_loss_ratio)
                self.optimization_table.setItem(n, 8, return_risk_ratio)
                self.optimization_table.setItem(n, 9, real_yields)

        # Create layout
        button = QtWidgets.QPushButton("保存")
        button.clicked.connect(self.save_csv)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addStretch()
        hbox.addWidget(button)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.optimization_table)
        vbox.addLayout(hbox)

        self.setLayout(vbox)

    def save_csv(self) -> None:
        """
        Save table data into a csv file
        """
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "保存数据", "", "CSV(*.csv)")
        if not path:
            return
        try:
            with open(path, "w") as f:
                writer = csv.writer(f, lineterminator="\n")

                column_name = []
                for i in range(self.optimization_table.columnCount()):
                    column_name.append(self.optimization_table.horizontalHeaderItem(i).text())
                writer.writerow(column_name)

                for row in range(self.optimization_table.rowCount()):
                    row_data = []
                    for column in range(self.optimization_table.columnCount()):
                        item = self.optimization_table.item(row, column)
                        if item:
                            row_data.append(str(item.text()))
                        else:
                            row_data.append("")
                    writer.writerow(row_data)
        except PermissionError:
            QtWidgets.QMessageBox.critical(self, "保存失败", "写入的文件被打开,请关闭文件后再操作")

