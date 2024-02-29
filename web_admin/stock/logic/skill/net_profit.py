from django.db.models import Q
from stock.logic.skill.previous_year_date import previous_year_date
from stock.logic.skill.sec_info import get_stock_sec_info
from stock.models.daily_stock_data import DailyStockData
from stock.models.financial_statement import FinancialStatement
from stock.models.moth_data import MothData


class NetProfit:
    def stock_np_parent_company_owners(self, params=None, stock_list=[], stock_column_desc=[]):
        """净利润"""
        next_year_datetime = previous_year_date(params['end_date'], 4)
        out_stock_list = []
        sec_info_list, vt_symbol_map = get_stock_sec_info(stock_list)
        for row in sec_info_list:
            cond = {
                'code': '{}.{}'.format(row['symbol'], row['exchange']),
                'end_date': params['end_date'],
                'start_date': params['start_date'] if params.__contains__('start_date') else '',
                'order': ['pub_date', 'desc'],
                'report_date': next_year_datetime,
                'cycle': params['cycle'],
                'np_parent_company_owners_money': params['np_parent_company_owners_money'] * 10000,
                'np_parent_company_owners_condition': params['np_parent_company_owners_condition']
            }
            if cond['cycle'] == 'day':
                model_d = DailyStockData

            elif cond['cycle'] == 'month':
                model_d = MothData
            df = FinancialStatement().get_net_prfit(cond=cond)
            np_parent_company_owners_condition = cond['np_parent_company_owners_condition']
            if np_parent_company_owners_condition == "gte":
                if len(df):
                    # if str(df["report_date"].values[2]) == "2016-12-31":
                    #     print(df, row["symbol"])
                    if df["np_parent_company_owners"].min() >= cond['np_parent_company_owners_money']:
                        if stock_list:
                            row['np_parent_company_owners'] = round(df["np_parent_company_owners"].values[0] / 10000, 2)
                            out_stock_list.append(row)
                        else:
                            if cond["start_date"]:
                                query_set = model_d.objects.filter(
                                    Q(datetime__lte=cond['end_date'])
                                    & Q(datetime__gte=cond['start_date'])
                                    & Q(symbol=row['symbol'])
                                    & Q(exchange=row['exchange'])
                                ).order_by("-datetime")
                            else:
                                query_set = model_d.objects.filter(
                                    Q(datetime__lte=cond['end_date'])
                                    & Q(symbol=row['symbol'])
                                    & Q(exchange=row['exchange'])
                                ).order_by("-datetime")
                            if query_set:
                                query_set = query_set[0]
                                out_stock_list.append(
                                    {
                                        'id': row['id'],
                                        "symbol": row['symbol'],
                                        "exchange": row['exchange'],
                                        "display_name": vt_symbol_map[f"{row['symbol']}.{row['exchange']}"],
                                        'close': query_set.close_price,
                                        'trade_date': query_set.datetime.strftime("%Y-%m-%d"),
                                        'np_parent_company_owners': round(df["np_parent_company_owners"].values[0] / 10000, 2)
                                    }
                                )
                    elif np_parent_company_owners_condition == "lte":
                        if df["np_parent_company_owners"].max() <= cond['np_parent_company_owners_money']:
                            if stock_list:
                                row['np_parent_company_owners'] = round(
                                    df["np_parent_company_owners"].values[0] / 10000, 2)
                                out_stock_list.append(row)
                            else:
                                if cond["start_date"]:
                                    query_set = model_d.objects.filter(
                                        Q(datetime__lte=cond['end_date'])
                                        & Q(datetime__gte=cond['start_date'])
                                        & Q(symbol=row['symbol'])
                                        & Q(exchange=row['exchange'])
                                    ).order_by("-datetime")
                                else:
                                    query_set = model_d.objects.filter(
                                        Q(datetime__lte=cond['end_date'])
                                        & Q(symbol=row['symbol'])
                                        & Q(exchange=row['exchange'])
                                    ).order_by("-datetime")
                                if query_set:
                                    query_set = query_set[0]
                                    out_stock_list.append(
                                        {
                                            'id': row['id'],
                                            "symbol": row['symbol'],
                                            "exchange": row['exchange'],
                                            "display_name": vt_symbol_map[f"{row['symbol']}.{row['exchange']}"],
                                            'close': query_set.close_price,
                                            'trade_date': query_set.datetime.strftime("%Y-%m-%d"),
                                            'np_parent_company_owners': round(
                                                df["np_parent_company_owners"].values[0] / 10000, 2)
                                        }
                                    )

        stock_column_desc.append({'name': '净利润(单位:万元)', 'key': 'np_parent_company_owners'})
        return out_stock_list, stock_column_desc
