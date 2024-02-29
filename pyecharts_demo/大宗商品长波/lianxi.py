#
# import tushare as ts
# pro = ts.pro_api(token="bb38ed990fcea5fbf2ddd938a7ab886bc3df08865e2bcc2cfb1e540d")
# df = pro.index_global(ts_code="XIN9", start_date="20221107", end_date="20221207")
#
# print(df)

import numpy as np
import pandas as pd

NP_NAT = np.array([pd.NaT], dtype=np.int64)[0]
print(NP_NAT)