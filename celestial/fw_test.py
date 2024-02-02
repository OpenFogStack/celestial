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

import numba
import numpy as np
from scipy.sparse.csgraph import floyd_warshall
import time


def generate_test_mat(total: int) -> np.ndarray:  # type: ignore
    # Generate a random symmetric matrix with non-negative edge weights
    rng = np.random.default_rng(2)
    dist_matrix = rng.integers(1, 5, size=(total, total))

    # remove some random edges by ORing with a 0,1 matrix
    dist_matrix = dist_matrix * rng.choice([1.0, np.inf], size=(total, total))

    dist_matrix = dist_matrix + dist_matrix.T  # Ensure symmetry
    np.fill_diagonal(dist_matrix, 0)  # Diagonal elements should be zero

    # Save the matrix to a test file
    return dist_matrix


def test_floyd_warshall(m: np.ndarray) -> None:  # type: ignore
    # Load the matrix from the test file
    dist_matrix_orig = m.copy()

    print("Original matrix:")
    print(dist_matrix_orig)

    # Run the optimized Floyd-Warshall algorithm
    dist_matrix_opt = dist_matrix_orig.copy()
    next_hops = np.zeros_like(dist_matrix_opt, dtype=int)
    t1 = time.perf_counter()
    optimized_floyd_warshall(dist_matrix_opt, next_hops)
    t2 = time.perf_counter()

    print("Optimized matrix:")
    print(dist_matrix_opt)
    print("Next hops:")
    print(next_hops)

    # Run the scipy Floyd-Warshall algorithm
    dist_matrix_sci = dist_matrix_orig.copy()
    t3 = time.perf_counter()
    scipy_result = floyd_warshall(
        dist_matrix_sci, directed=False, return_predecessors=True
    )
    # weirdly the wrong way around
    next_hops_scipy = scipy_result[1].T
    # and replace the -9999 with -1
    next_hops_scipy[next_hops_scipy == -9999] = -1
    # and replace the middle line with the identity matrix
    next_hops_scipy[
        np.arange(len(next_hops_scipy)), np.arange(len(next_hops_scipy))
    ] = np.arange(len(next_hops_scipy))

    t4 = time.perf_counter()

    dist_matrix_sci_upper = scipy_result[0]

    print("Scipy matrix:")
    print(dist_matrix_sci_upper)
    print("Scipy next hops:")
    print(next_hops_scipy)

    print(f"Optimized time: {t2 - t1}")
    print(f"Scipy time: {t4 - t3}")

    # Compare the results
    assert np.array_equal(dist_matrix_opt, dist_matrix_sci_upper)
    assert np.array_equal(next_hops, next_hops_scipy)


@numba.njit  # type: ignore
def optimized_floyd_warshall(
    dist_matrix_orig: np.ndarray,  # type: ignore
    next_hops: np.ndarray,  # type: ignore
) -> None:
    """
    Actual implementation of _update_paths optimized with numba.
    """

    length = len(dist_matrix_orig)
    dist_matrix = np.empty((length, length), dtype=np.float32)

    # initialize all to inf
    for i in range(length):
        for j in range(length):
            dist_matrix[i, j] = np.inf
            next_hops[i, j] = -1

    # add the original links
    for i in range(length):
        for j in range(length):
            if dist_matrix_orig[i, j] != np.inf:
                dist_matrix[i, j] = dist_matrix_orig[i, j]
                next_hops[i, j] = j

    for i in range(length):
        dist_matrix[i, i] = 0
        next_hops[i, i] = i

    # Floyd-Warshall algorithm
    for k in range(length):
        for i in range(length):
            for j in range(i + 1, length):
                d_ik = dist_matrix[i, k]  # if i < k else dist_matrix[k, i]
                d_kj = dist_matrix[k, j]  # if k < j else dist_matrix[j, k]

                if dist_matrix[i, j] > d_ik + d_kj:
                    dist_matrix[i, j] = d_ik + d_kj
                    dist_matrix[j, i] = d_ik + d_kj
                    next_hops[i, j] = next_hops[i, k]
                    next_hops[j, i] = next_hops[j, k]

    for i in range(length):
        for j in range(i + 1, length):
            dist_matrix_orig[i, j] = dist_matrix[i, j]
            dist_matrix_orig[j, i] = dist_matrix[i, j]


if __name__ == "__main__":
    ts = [5, 10, 20, 72 * 22]  # Set the desired number of nodes

    for t in ts:
        # Generate the test file
        m = generate_test_mat(t)

        # Test the optimized Floyd-Warshall algorithm against scipy
        test_floyd_warshall(m)

    print("Test passed successfully!")
