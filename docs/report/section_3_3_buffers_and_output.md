# Section 3.3: Input Buffers, Skew Logic, and Output Collector

**Author:** Abhijeet  
**Branch:** `abhijeet-buffers`  
**Modules Owned:** `rtl/input_buffer.v`, `rtl/output_collector.v`  
**Testbenches:** `tb/tb_input_buffer.v`, `tb/tb_output_collector.v`  

---

## 1. Purpose
The **input buffer** stores the input matrices $A$ and $B$, applying the required cycle-by-cycle "staircase" skew timing to feed the $4 \times 4$ systolic array. The **output collector** acts as a combinational $16:1$ multiplexer to extract any individual 32-bit signed element $C[i][j]$ from the flattened accumulator bus (`c_flat`) during or after execution.

---

## 2. Interface Specifications

### 2.1 `input_buffer.v` Interface
| Port | Direction | Width | Description |
| :--- | :---: | :---: | :--- |
| `clk` | Input | 1 | System clock (rising edge active). |
| `rst` | Input | 1 | Synchronous active-high reset; clears internal memories $A$ and $B$. |
| `load_en` | Input | 1 | Write-enable for loading matrix data prior to computation. |
| `load_sel` | Input | 1 | Select target matrix: `0` for Matrix $A$, `1` for Matrix $B$. |
| `load_row` | Input | 2 (`$clog2(N)`) | Row index for loading ($0 \dots 3$). |
| `load_col` | Input | 2 (`$clog2(N)`) | Column index for loading ($0 \dots 3$). |
| `load_data` | Input | 8 (`DW`) | 8-bit signed two's-complement element to store. |
| `feed_en` | Input | 1 | Array feed enable (active during `COMPUTE` phase). |
| `t` | Input | 8 (`TW`) | Global compute/drain cycle counter from the controller. |
| `a_left` | Output | 32 (`N*DW`) | Flattened vector `{row3, row2, row1, row0}` fed to systolic array left edge. |
| `b_top` | Output | 32 (`N*DW`) | Flattened vector `{col3, col2, col1, col0}` fed to systolic array top edge. |

### 2.2 `output_collector.v` Interface
| Port | Direction | Width | Description |
| :--- | :---: | :---: | :--- |
| `c_flat` | Input | 512 (`N*N*AW`) | Flattened bus from all 16 PEs' 32-bit accumulators. |
| `rd_row` | Input | 2 (`$clog2(N)`) | Target row index to read ($0 \dots 3$). |
| `rd_col` | Input | 2 (`$clog2(N)`) | Target column index to read ($0 \dots 3$). |
| `rd_data` | Output | 32 (`AW`) | 32-bit signed accumulated result $C[\text{rd\_row}][\text{rd\_col}]$. |

---

## 3. How It Works and Design Rationale

### 3.1 Why Input Skew is Necessary (The Skew Theory)
In an output-stationary systolic array, each Processing Element $\text{PE}(i, j)$ accumulates the inner product:
$$C[i][j] = \sum_{k=0}^{N-1} A[i][k] \times B[k][j]$$

1. Matrix $A$ elements flow horizontally from the left boundary to the right, advancing by one PE each clock cycle. Therefore, element $A[i][k]$ arrives at $\text{PE}(i, j)$ after $j$ clock cycles.
2. Matrix $B$ elements flow vertically from the top boundary downwards, advancing by one PE each clock cycle. Therefore, element $B[k][j]$ arrives at $\text{PE}(i, j)$ after $i$ clock cycles.
3. For the multiply-accumulate unit in $\text{PE}(i, j)$ to compute $A[i][k] \times B[k][j]$, both operands must arrive at $\text{PE}(i, j)$ on the exact same clock cycle $t$.
4. By delaying the injection of row $i$ of $A$ by $i$ clock cycles, and column $j$ of $B$ by $j$ clock cycles, operand $A[i][k]$ enters at cycle $i + k$ and arrives at $\text{PE}(i, j)$ at cycle $(i + k) + j = i + j + k$. Similarly, operand $B[k][j]$ enters at cycle $j + k$ and arrives at $(j + k) + i = i + j + k$.
5. Hence, both inputs meet simultaneously at cycle $t = i + j + k$.
6. This time-staggered delay forms the characteristic diagonal wavefront (staircase pattern). Without this skew logic, the PE multiplies unmatched matrix coordinates, corrupting all results except $C[0][0]$.

### 3.2 `input_buffer.v` Implementation Rationale
* **Internal Storage:** Two separate 1D register arrays `A[0:15]` and `B[0:15]` store 16 8-bit values each. Row-major mapping is used: `index = row * N + col`.
* **Synchronous Load:** Data is written at the rising clock edge when `load_en` is high. Reset initializes all memory cells to zero.
* **Combinational Skew Extraction:** Instead of using physical delay flip-flop shift chains for each row/column, `input_buffer.v` uses combinational multiplexing driven by `t` and `feed_en`:
  * Left edge slice $i$: $A[i][t - i]$ when $0 \le t - i < N$, else $0$.
  * Top edge slice $j$: $B[t - j][j]$ when $0 \le t - j < N$, else $0$.
  * Guard condition `t >= i` prevents negative bit indices or underflows.
  * When `feed_en = 0` (e.g., during `IDLE`, `CLEAR`, or `DRAIN`), all outputs evaluate strictly to `0`.

### 3.3 `output_collector.v` Implementation Rationale
* `output_collector.v` is implemented as a pure combinational bit-range select:
  $$\text{rd\_data} = c\_flat[(\text{rd\_row} \times N + \text{rd\_col}) \times \text{AW} +: \text{AW}]$$
* Because it is purely combinational, it adds **0 additional clock cycles of read latency**. Once the controller enters `DONE`, the host/testbench can read any element across the 16 results instantaneously in the same cycle by setting `rd_row` and `rd_col`.

---

## 4. Inter-Module Connectivity and Dependencies

```
                      +-------------------+
                      |   controller.v    | (Parrv)
                      |  (feed_en, t)     |
                      +---------+---------+
                                |
                                v
+------------------+    +---------------+    +--------------------+    +------------------+
| External Master  |--->| input_buffer  |--->|   systolic_array   |--->| output_collector |
| (load_en/data)   |    |  (Abhijeet)   |    |     (Ranjeet)      |    |   (Abhijeet)     |
+------------------+    +---------------+    +--------------------+    +--------+---------+
                                                     a_left, b_top              | rd_data
                                                                                v
                                                                        +------------------+
                                                                        | External Master  |
                                                                        | (rd_row, rd_col) |
                                                                        +------------------+
```

### Dependency Checklist:
1. **Can Abhijeet work independently?**
   * **Yes.** Both `input_buffer` and `output_collector` are leaf/standalone modules. Their unit testbenches (`tb_input_buffer.v`, `tb_output_collector.v`) drive stimulus directly and do not require files from Raghav, Ranjeet, Malhar, or Parrv.
2. **Who depends on Abhijeet's work?**
   * **Parrv (`systolic_top.v`):** Instantiates both `input_buffer` and `output_collector` at top level.
   * **Ranjeet (`systolic_array.v`):** Receives the skewed `a_left` and `b_top` buses produced by `input_buffer.v`.
3. **What is handed off?**
   * At the end of Phase 2, `rtl/input_buffer.v` and `rtl/output_collector.v` are delivered to Parrv for top-level integration.

---

## 5. Verification and Test Results

### 5.1 Input Buffer Verification (`tb/tb_input_buffer.v`)
* **Loaded Pattern:**
  * $A[r][c] = 16 \times (r + 1) + c \implies$ Row 0: `10 11 12 13`, Row 1: `20 21 22 23`, Row 2: `30 31 32 33`, Row 3: `40 41 42 43`.
  * $B[r][c] = 160 + 4r + c \implies$ Col 0: `a0 a4 a8 ac`, Col 1: `a1 a5 a9 ad`, Col 2: `a2 a6 aa ae`, Col 3: `a3 a7 ab af`.
* **Cycle-by-Cycle Skew Verification Table ($t = 0 \dots 9$):**
  | $t$ | `a_left` [0] | `a_left` [1] | `a_left` [2] | `a_left` [3] | `b_top` [0] | `b_top` [1] | `b_top` [2] | `b_top` [3] | Status |
  | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
  | **0** | `0x10` | `0x00` | `0x00` | `0x00` | `0xa0` | `0x00` | `0x00` | `0x00` | PASS |
  | **1** | `0x11` | `0x20` | `0x00` | `0x00` | `0xa4` | `0xa1` | `0x00` | `0x00` | PASS |
  | **2** | `0x12` | `0x21` | `0x30` | `0x00` | `0xa8` | `0xa5` | `0xa2` | `0x00` | PASS |
  | **3** | `0x13` | `0x22` | `0x31` | `0x40` | `0xac` | `0xa9` | `0xa6` | `0xa3` | PASS |
  | **4** | `0x00` | `0x23` | `0x32` | `0x41` | `0x00` | `0xad` | `0xaa` | `0xa7` | PASS |
  | **5** | `0x00` | `0x00` | `0x33` | `0x42` | `0x00` | `0x00` | `0xae` | `0xab` | PASS |
  | **6** | `0x00` | `0x00` | `0x00` | `0x43` | `0x00` | `0x00` | `0x00` | `0xaf` | PASS |
  | **7** | `0x00` | `0x00` | `0x00` | `0x00` | `0x00` | `0x00` | `0x00` | `0x00` | PASS |
  | **8** | `0x00` | `0x00` | `0x00` | `0x00` | `0x00` | `0x00` | `0x00` | `0x00` | PASS |
  | **9** | `0x00` | `0x00` | `0x00` | `0x00` | `0x00` | `0x00` | `0x00` | `0x00` | PASS |
* **Inactivation Check:** Tested with `feed_en = 0` for all $t \in [0, 9]$; verified all outputs remain `0x00000000`.
* **Result:** All checks passed with 0 errors.

### 5.2 Output Collector Verification (`tb/tb_output_collector.v`)
* **Test Vector Coverage:** Packed 16 distinct 32-bit signed integers into `c_flat`, covering:
  * Zero (`0`)
  * Positive values (`12345`, `42`, `1024`, `255`)
  * Negative small/medium values (`-1`, `-128`, `-99`, `-54321`)
  * Maximum theoretical boundaries ($4 \times 127 \times 127 = +64,516$, $4 \times (-128) \times (-128) = +65,536$, and $4 \times 127 \times (-128) = -65,024$).
* **Result:** All 16 positions read correctly with exact matching bit patterns and proper signed sign-extension. 0 errors.

---

## 6. Screenshot and Waveform Captions
1. **`docs/screenshots/skew_staircase.png`:** Waveform from `wave_input_buffer.vcd` showing `feed_en`, counter `t` advancing from $0$ to $9$, and the four individual byte slices of `a_left` and `b_top`. Notice how valid values for row/col $i$ start precisely at cycle $t = i$ and terminate after 4 cycles, verifying the staircase skew timing.
