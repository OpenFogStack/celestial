#
# This file is part of Celestial (https://github.com/OpenFogStack/celestial).
# Copyright (c) 2024 Tobias Pfandzelter, The OpenFogStack Team.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

import numpy as np
import numba
import time


@numba.njit  # type: ignore
def dot_product_manual(matrix_3x3: np.ndarray, vector_3x1: np.ndarray) -> np.ndarray:  # type: ignore
    result = np.zeros((3,), dtype=np.int64)

    for i in range(3):
        for j in range(3):
            result[i] += matrix_3x3[i, j] * vector_3x1[j]

    return result  # type: ignore


def dot_product(matrix_3x3: np.ndarray, vector_3x1: np.ndarray) -> np.ndarray:  # type: ignore
    result = np.dot(matrix_3x3, vector_3x1)
    return result  # type: ignore


if __name__ == "__main__":
    # Example usage
    matrix_3x3 = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    vector_3x1 = np.array([2, 3, 4])

    # Explicitly type the input arguments
    matrix_3x3 = matrix_3x3.astype(np.int64)
    vector_3x1 = vector_3x1.astype(np.int64)

    t1 = time.perf_counter()
    result = dot_product(matrix_3x3, vector_3x1)
    t2 = time.perf_counter()
    print(result)

    # Example usage
    matrix_3x3 = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    vector_3x1 = np.array([2, 3, 4])

    t3 = time.perf_counter()
    result_manual = dot_product_manual(matrix_3x3, vector_3x1)
    t4 = time.perf_counter()
    print(result_manual)

    print(f"dot_product took {t2 - t1} seconds")
    print(f"dot_product_manual took {t4 - t3} seconds")
