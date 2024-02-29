from peewee import *
from jqdatasdk import *
from vnpy.model.base_model import BaseModel
import re
import datetime
import dateutil.relativedelta
from vnpy.trader.utility import load_json, save_json


class SecuritiesInfoModel(BaseModel):
    """所有标的信息模型类"""
    id = AutoField(primary_key=True, verbose_name="主键id")
    symbol = CharField(null=False)
    display_name = CharField(null=False, verbose_name="中文名称")
    name_code = CharField(null=False, verbose_name="缩写简称")
    start_date = DateField(null=False, verbose_name="上市日期")
    end_date = DateField(null=False, verbose_name="退市日期")
    sec_type = CharField(null=False, verbose_name="类型(futures:期货，stock:股票等等)")

    class Meta:
        table_name = 'securities_info'

    def get_symbol_letter(self):
        """获取代码中的字母部分"""
        symbol_letter = [re.sub('[^a-zA-Z]', '', i.symbol.split(".")[0]) for i in SecuritiesInfoModel.select().where(SecuritiesInfoModel.name_code ** "%8888%")]
        return symbol_letter

    def get_main_contract_code(self, filename):
        """查询所有主力合约代码"""
        new_dt = datetime.datetime.now().date()
        try:
            main_contract_data = load_json(filename)
        except:
            main_contract_data = {}
        if main_contract_data.get("main_contract", None):
            old_dt = (datetime.datetime.strptime(main_contract_data["datetime"], '%Y-%m-%d') + dateutil.relativedelta.relativedelta(days=15)).date()
            if new_dt <= old_dt:
                return main_contract_data["main_contract"]

        auth("13539755450", "Js123456")
        symbol_letter = self.get_symbol_letter()
        main_contract_code = []
        for letter in symbol_letter:
            main_contract_code.append(get_dominant_future(letter, new_dt).split(".")[0])
        data = {
            "datetime": new_dt.strftime('%Y-%m-%d'),
            "main_contract": main_contract_code
        }
        save_json(filename, data)

        return main_contract_code
