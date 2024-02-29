from django.db.models import Q
def return_on_assets_overlapping_code(symbol, row, stock_list, out_stock_list, cond, model_d, total_owner_equities, vt_symbol_map):
    if symbol == row['symbol']:
        if stock_list:
            row['total_owner_equities'] = round(total_owner_equities, 2)
            out_stock_list.append(row)
        else:
            if cond['start_date']:
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
                        'total_owner_equities': round(total_owner_equities, 2)
                    }
                )

    return out_stock_list


def equity_screener_duplicated_code(symbol, row, stock_list, out_stock_list, cond, model_d, vt_symbol_map, conditions_key, conditions_value):
    if symbol == row['symbol']:
        if stock_list:
            row[conditions_key] = round(conditions_value, 2)
            out_stock_list.append(row)
        else:
            if cond['start_date']:
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
                        conditions_key: round(conditions_value, 2)
                    }
                )

    return out_stock_list