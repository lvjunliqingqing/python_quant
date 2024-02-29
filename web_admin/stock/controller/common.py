from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def conditionList(request):
    cond_list = [
        {
            "label": '基本面指标',
            "options": [
                {
                    'label': '净利润',
                    'value': 'np_parent_company_owners'
                },
                {
                    'label': '扣非净利润',
                    'value': 'adjusted_profit'
                },
                {
                    'label': '市盈率',
                    'value': 'pe_ratio'
                },
                {
                    'label': '市净率',
                    'value': 'pb_ratio'
                },
                {
                    'label': '市现率',
                    'value': 'pcf_ratio'
                },
                {
                    'label': '流通市值',
                    'value': 'circulating_market_cap'
                },
                {
                    'label': '换手率',
                    'value': 'turnover_rate'
                },
                {
                    'label': '每股资本公积',
                    'value': 'capital_reserves_per_share'
                },
                {
                    'label': '净资产收益率',
                    'value': 'return_on_assets'
                },
                {
                    'label': '每股收益',
                    'value': 'earnings_per_share'
                },
                {
                    'label': '营业收入增长率',
                    'value': 'increase_rate_of_business_revenue'
                },
                {
                    'label': '净利润增长率',
                    'value': 'np_parent_company_owners_growth_rate'
                },
                {
                    'label': '资产负债率',
                    'value': 'asset_liability_ratio'
                }
            ]
        },
        {
            "label": '技术面指标',
            "options": [
                {
                    'label': '突破历史高点',
                    'value': 'break_high'
                },
                {
                    'label': '突破日均线',
                    'value': 'break_ma'
                },
                {
                    'label': '突破历史成交量',
                    'value': 'break_volume'
                },
                {
                    'label': '涨幅做多',
                    'value': 'zf_long'
                },
                {
                    'label': '跌幅做空',
                    'value': 'df_long'
                },
                {
                    'label': '涨幅历史分位数',
                    'value': 'df_history_long'
                },
                {
                    'label': '跌幅历史分位数',
                    'value': 'df_history_short'
                },
                {
                    'label': '十字星',
                    'value': 'history_cross'
                },
                # {
                #     'label': '大阳中上部',
                #     'value': 'sun_middle_upper_part'
                # },
                # {
                #     'label': '大阴中下部',
                #     'value': 'big_yin_lower_middle_part'
                # },
                {
                    'label': 'RSI指标',
                    'value': 'RSI_indicator'
                }
            ]
        }

    ]
    out = {
        'code': 0,
        'data': cond_list
    }
    return JsonResponse(out)


@csrf_exempt
def dynamicFormList(request):
    form_list = {
        'break_high': [
            {
                'type': 'input',
                'key': 'break_high_value',
                'label': '历史周期',
                'logic': '>=',
                'precision': 0,
                'icon': 'el-icon-time',
                'group': 'break_high'
            },
            {
                'type': 'input',
                'key': 'from_the_current_number_of_days',
                'label': '历史高点出现在指定时间的多少天前',
                'logic': '>=',
                'precision': 0,
                'icon': 'el-icon-time',
                'group': 'break_high'
            }
        ],
        'break_ma': [
            {
                'type': 'input',
                'key': 'break_ma_value',
                'label': '均线周期',
                'logic': '>=',
                'group': 'break_ma',
                'precision': 0
            }
        ],
        'break_volume': [
            {
                'type': 'input',
                'key': 'break_volume_value',
                'label': '成交量周期',
                'logic': '>=',
                'group': 'break_volume',
                'precision': 0
            }
        ],
        'np_parent_company_owners': [
            {
                'type': 'select',
                'key': 'np_parent_company_owners_logic',
                'label': '净利润条件',
                'group': 'np_parent_company_owners'
            },
            {
                'type': 'input',
                'key': 'np_parent_company_owners_value',
                'label': '净利润(万)',
                'group': 'np_parent_company_owners'
            }
        ],
        'adjusted_profit': [
            {
                'type': 'select',
                'key': 'adjusted_profit_logic',
                'label': '扣非净利润条件',
                'group': 'adjusted_profit'
            },
            {
                'type': 'input',
                'key': 'adjusted_profit_value',
                'label': '扣非净利润(万)',
                'group': 'adjusted_profit'
            }
        ],
        'pe_ratio': [
            {
                'type': 'slider',
                'key': 'pe_ratio_value',
                'label': '市盈率范围',
                'min': 0,
                'max': 50000,
                'step': 1,
                'group': 'pe_ratio'
            }
        ],
        'pb_ratio': [
            {
                'type': 'slider',
                'key': 'pb_ratio_value',
                'label': '市净率范围',
                'min': 0,
                'max': 50000,
                'step': 1,
                'group': 'pb_ratio'
            }
        ],
        'circulating_market_cap': [
            {
                'type': 'slider',
                'key': 'circulating_market_cap_value',
                'label': '流通市值(亿元)',
                'min': 0,
                'max': 50,
                'step': 1,
                'group': 'circulating_market_cap'
            }
        ],
        'turnover_rate': [
            {
                'type': 'slider',
                'key': 'turnover_rate_value',
                'label': '换手率',
                'min': 0,
                'max': 100,
                'step': 1,
                'group': 'turnover_rate'
            }
        ],
        'capital_reserves_per_share': [
            {
                'type': 'slider',
                'key': 'capital_reserves_per_share_value',
                'label': '每股资本公积',
                'min': 0,
                'max': 100,
                'step': 1,
                'group': 'capital_reserves_per_share'
            }
        ],
        'pcf_ratio': [
            {
                'type': 'slider',
                'key': 'pcf_ratio_value',
                'label': '市现率范围',
                'min': 0,
                'max': 50000,
                'step': 1,
                'group': 'pcf_ratio'
            }
        ],
        'zf_long': [
            {
                'type': 'slider',
                'key': 'zf_long_one_value',
                'label': '前天K线',
                'min': -10,
                'max': 10,
                'step': 0.5,
                'group': 'zf_long'
            },
            {
                'type': 'slider',
                'key': 'zf_long_two_value',
                'label': '昨天K线',
                'min': -10,
                'max': 10,
                'step': 0.5,
                'group': 'zf_long'
            }
        ],
        'df_long': [
            {
                'type': 'slider',
                'key': 'df_long_one_value',
                'label': '前天K线',
                'min': -10,
                'max': 10,
                'step': 0.5,
                'group': 'df_long'
            },
            {
                'type': 'slider',
                'key': 'df_long_two_value',
                'label': '昨天K线',
                'min': -10,
                'max': 10,
                'step': 0.5,
                'group': 'df_long'
            }
        ],
        'df_history_long': [
            {
                'type': 'slider',
                'key': 'df_history_long_yesterday_value',
                'label': '昨天分位数',
                'min': 0,
                'max': 100,
                'step': 1,
                'group': 'df_history_long'
            },
            {
                'type': 'slider',
                'key': 'df_history_long_today_value',
                'label': '今天分位数',
                'min': 0,
                'max': 100,
                'step': 1,
                'group': 'df_history_long'
            }
        ],
        'df_history_short': [
            {
                'type': 'slider',
                'key': 'df_history_short_yesterday_value',
                'label': '昨天分位数',
                'min': 0,
                'max': 100,
                'step': 1,
                'group': 'df_history_short'
            },
            {
                'type': 'slider',
                'key': 'df_history_short_today_value',
                'label': '今天分位数',
                'min': 0,
                'max': 100,
                'step': 1,
                'group': 'df_history_short'
            }
        ],
        'history_cross': [
            {
                'type': 'slider',
                'key': 'history_cross_yesterday_value',
                'label': '昨天浮动点',
                'min': -10,
                'max': 10,
                'step': 0.01,
                'group': 'history_cross'
            },
            {
                'type': 'slider',
                'key': 'history_cross_today_value',
                'label': '今天浮动点',
                'min': -10,
                'max': 10,
                'step': 0.01,
                'group': 'history_cross'
            },
            {
                'type': 'slider',
                'key': 'history_cross_yesterday_width_value',
                'label': '昨天上下影线的长度',
                'min': 0,
                'max': 5,
                'step': 0.01,
                'group': 'history_cross'
            },
            {
                'type': 'slider',
                'key': 'history_cross_today_width_value',
                'label': '今天上下影线的长度',
                'min': 0,
                'max': 5,
                'step': 0.01,
                'group': 'history_cross'
            }
        ],
        'sun_middle_upper_part': [
            {
                'type': 'slider',
                'key': 'sun_middle_upper_part_yesterday_value',
                'label': '昨天阳线的长度',
                'min': 0,
                'max': 20,
                'step': 0.1,
                'group': 'sun_middle_upper_part'
            }
        ],
        'big_yin_lower_middle_part': [
            {
                'type': 'slider',
                'key': 'big_yin_lower_middle_part_yesterday_value',
                'label': '昨天阴线的长度',
                'min': -20,
                'max': 0,
                'step': 0.1,
                'group': 'big_yin_lower_middle_part'
            }
        ],
        'return_on_assets': [
            {
                'type': 'slider',
                'key': 'return_on_assets_value',
                'label': '净资产收益率',
                'min': 0,
                'max': 500,
                'step': 1,
                'group': 'return_on_assets'
            }
        ],
        'earnings_per_share': [
            {
                'type': 'slider',
                'key': 'earnings_per_share_value',
                'label': '每股收益',
                'min': 0,
                'max': 500,
                'step': 0.01,
                'group': 'earnings_per_share'
            }
        ],
        'increase_rate_of_business_revenue': [
            {
                'type': 'slider',
                'key': 'increase_rate_of_business_revenue_value',
                'label': '营业收入增长率',
                'min': -100,
                'max': 50000,
                'step': 1,
                'group': 'increase_rate_of_business_revenue'
            },
            {
                'type': 'input',
                'key': 'n_increase_rate_of_business_revenue_value',
                'label': '持续几年',
                'group': 'increase_rate_of_business_revenue'
            }
        ],
        'np_parent_company_owners_growth_rate': [
            {
                'type': 'slider',
                'key': 'np_parent_company_owners_growth_rate_value',
                'label': '净利润增长率',
                'min': -100,
                'max': 50000,
                'step': 1,
                'group': 'np_parent_company_owners_growth_rate'
            },
            {
                'type': 'input',
                'key': 'n_np_parent_company_owners_growth_rate_value',
                'label': '持续几年(5~7年)',
                'group': 'np_parent_company_owners_growth_rate'
            }
        ],
        'asset_liability_ratio': [
            {
                'type': 'slider',
                'key': 'asset_liability_ratio_value',
                'label': '资产负债率',
                'min': 0,
                'max': 100,
                'step': 1,
                'group': 'asset_liability_ratio'
            }
        ],
        'RSI_indicator': [
            {
                'type': 'slider',
                'key': 'RSI_indicator_scope_value',
                'label': 'RSI指标',
                'min': 0,
                'max': 100,
                'step': 1,
                'group': 'RSI_indicator'
            },
            {
                'type': 'input',
                'key': 'RSI_indicator_params_value',
                'label': 'RSI参数',
                'group': 'RSI_indicator'
            }
        ]

    }

    out = {
        'code': 0,
        'data': form_list
    }

    return JsonResponse(out)
