import numpy as np

mean_threshold = 814047927.2074074
var_threshold = 2.4902001983892765e+17

data_ndarray = np.zeros((80, 7), dtype=int) # Put actual data here

# Uncomment for mean threshold
# data_mean = np.mean([s[0] ** 2 + s[1] ** 2 + s[2] ** 2 for s in data_ndarray])
# if data_mean > mean_threshold:
#     # Send to FPGA
#     pass

# Uncomment for var threshold
# data_var = np.var([s[0] ** 2 + s[1] ** 2 + s[2] ** 2 for s in data_ndarray])
# if data_var > var_threshold:
#     # Send to FPGA
#     pass
