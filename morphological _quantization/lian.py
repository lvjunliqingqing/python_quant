import math

import pandas as pd

df = pd.DataFrame({'name': [12, 12, 23, 22, 17], 'age': [23, 22, 17, 15, 20], 'age2': [10, 15, 20, 15, 20]})
# print(df.columns.get_indexer(['name', "age", 'age2']))
# print(df.index[0:2].tolist())
# print(df.loc[0:1, "name":"age2"])

t = math.pow(2.88, 1 / 365)
print(t)
t1 = pow(t, 365)
print(t1)
