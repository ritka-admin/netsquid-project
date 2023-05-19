import numpy as np


s0 = np.array([[1], [0]], dtype=complex)  # |0>
s1 = np.array([[0], [1]], dtype=complex)  # |1>
s11 = np.kron(s1, s1)
s00 = np.kron(s0, s0)
b00 = (s00 + s11) / np.sqrt(2)
