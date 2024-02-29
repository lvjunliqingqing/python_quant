import re

print(re.match(r"(\d{3,4})-(\d{6,8}) \1-\2", "020-12345678 020-12345678").group(2))
