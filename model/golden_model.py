"""Generate deterministic signed 4x4 matrix-multiplication test vectors."""
from pathlib import Path

import numpy as np

N = 4
TEST_DIR = Path(__file__).resolve().parent.parent / "tests"


def random_matrix(rng: np.random.Generator) -> np.ndarray:
    """Return an N x N matrix of signed 8-bit values, stored in int64."""
    return rng.integers(-128, 128, size=(N, N), dtype=np.int64)


def write_hex(path: Path, matrix: np.ndarray, bits: int) -> None:
    """Write row-major two's-complement values, one fixed-width word per line."""
    mask = (1 << bits) - 1
    digits = bits // 4
    with path.open("w", encoding="ascii") as output:
        for value in matrix.flat:
            output.write(f"{int(value) & mask:0{digits}x}\n")


def build_cases() -> list[tuple[str, np.ndarray, np.ndarray]]:
    rng = np.random.default_rng(42)
    identity = np.eye(N, dtype=np.int64)
    zeros = np.zeros((N, N), dtype=np.int64)
    cases = [
        ("identity_x_random", identity, random_matrix(rng)),
        ("all_zeros", zeros, zeros.copy()),
        (
            "all_max_127",
            np.full((N, N), 127, dtype=np.int64),
            np.full((N, N), 127, dtype=np.int64),
        ),
        (
            "all_min_neg128",
            np.full((N, N), -128, dtype=np.int64),
            np.full((N, N), -128, dtype=np.int64),
        ),
        (
            "mixed_max_min",
            np.full((N, N), 127, dtype=np.int64),
            np.full((N, N), -128, dtype=np.int64),
        ),
    ]
    cases.extend(
        (f"random_{index}", random_matrix(rng), random_matrix(rng))
        for index in range(1, 6)
    )
    return cases


def main() -> None:
    TEST_DIR.mkdir(parents=True, exist_ok=True)
    for index, (name, matrix_a, matrix_b) in enumerate(build_cases()):
        matrix_c = matrix_a.astype(np.int64) @ matrix_b.astype(np.int64)
        write_hex(TEST_DIR / f"test_{index:02d}_A.hex", matrix_a, 8)
        write_hex(TEST_DIR / f"test_{index:02d}_B.hex", matrix_b, 8)
        write_hex(TEST_DIR / f"test_{index:02d}_C.hex", matrix_c, 32)
        print(f"test_{index:02d} {name:20s} C[0][0]={int(matrix_c[0, 0])}")


if __name__ == "__main__":
    main()
