# 5. Performance comparison

The sequential baseline computes one multiply-accumulate (MAC) per clock and therefore needs \(N^3\) compute cycles for an \(N \times N\) multiply. The systolic design needs \(3N-2\) compute cycles after skewing the operands through the array, plus one accumulator-clear cycle. At \(N=4\), these formulas give 64 sequential cycles and 11 systolic cycles end to end.

| Metric (N = 4) | Systolic array | Sequential baseline |
|---|---:|---:|
| Compute cycles | 10 | 64 |
| Total cycles including clear | 11 | 64 |
| End-to-end speed-up | 5.82x | 1x |
| Speed-up excluding systolic clear | 6.4x | 1x |
| Average MACs per compute cycle | 6.4 | 1 |

| N | Systolic total cycles | Sequential cycles | End-to-end speed-up |
|---:|---:|---:|---:|
| 2 | 5 | 8 | 1.6x |
| 4 | 11 | 64 | 5.8x |
| 8 | 23 | 512 | 22.3x |
| 16 | 47 | 4096 | 87.1x |

The cycle counts are derived from the controller schedule and the one-MAC loop bounds. Record the `tb_top` and `tb_sequential` outputs alongside this section when simulation results are available. The comparison plot is generated at `docs/speedup.png` by `model/plot_speedup.py`.

## Explanation for the report

1. The sequential baseline reuses one signed MAC unit for every output element.
2. It computes \(N^3\) products, one per clock, for an \(N \times N\) matrix multiply.
3. The systolic design places \(N^2\) processing elements (PEs) in a grid.
4. Skewed A and B inputs make matching operands arrive at each PE together.
5. For \(N=4\), the array uses 10 compute cycles after one clear cycle; the baseline takes 64 cycles.
6. That is a 5.82x end-to-end speed-up, or 6.4x when the clear cycle is excluded, at the cost of more multiplier hardware.
