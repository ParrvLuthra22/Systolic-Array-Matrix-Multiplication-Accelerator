"""
Project 12 - Systolic Array Matrix Multiplication Accelerator
3Blue1Brown-style explainer animation made with Manim Community (owner: Ranjeet).

Shows, cycle by cycle, how the 4x4 output-stationary systolic array in rtl/ computes
C = A x B: what one PE does (multiply-accumulate + pass-through registers), how the
input skew works, how A flows right and B flows down, and the controller timing
CLEAR (1) -> COMPUTE (t = 0..6) -> DRAIN (t = 7..9) -> DONE = 11 cycles.

Setup (once, from the repo root; macOS needs `brew install cairo pkg-config` first):
    python3 -m venv .venv && .venv/bin/pip install manim
Render (from the repo root):
    .venv/bin/manim -qh docs/animation/systolic_animation.py SystolicArrayExplained   # 1080p60
    .venv/bin/manim -ql docs/animation/systolic_animation.py SystolicArrayExplained   # fast preview
No LaTeX is needed: all text uses Text(), not MathTex().
"""
from manim import *
import numpy as np

# ---------------------------------------------------------------- data -------
N = 4
A = np.array([[1, 2, 0, 1],
              [3, 1, 2, 0],
              [0, 1, -1, 2],
              [2, 0, 1, 3]])
B = np.array([[1, 0, 2, 1],
              [2, 1, 0, 1],
              [0, 3, 1, 0],
              [1, 1, 0, 2]])
C = A @ B

# ---------------------------------------------------------------- style ------
BG = "#111318"
A_COL = "#58C4DD"      # A values: blue
B_COL = "#83C167"      # B values: green
P_COL = "#FFD84D"      # products: yellow
ACC_COL = "#FF9F43"    # accumulators / C: orange
PE_FILL = "#1C2735"
IDLE = "#6B7280"
DONE_COL = "#5CD67A"
MONO = "Menlo"

config.background_color = BG


def T(s, size=32, color=WHITE, **kw):
    return Text(s, font_size=size, color=color, **kw)


def fit_w(m, w):
    if m.width > w:
        m.scale_to_fit_width(w)
    return m


def num(v, h, color=WHITE, bold=False):
    """A number scaled to a fixed digit height (consistent across values)."""
    t = Text(str(v), color=color, weight=BOLD if bold else NORMAL)
    ref = Text("0", weight=BOLD if bold else NORMAL)
    t.scale(h / ref.height)
    return t


def token(v, color, w=0.4, h=0.34):
    box = RoundedRectangle(corner_radius=0.07, width=w, height=h,
                           stroke_width=0, fill_color=color, fill_opacity=1)
    t = num(v, h * 0.5, BLACK, bold=True)
    fit_w(t, w * 0.85).move_to(box)
    return VGroup(box, t)


def matrix_grid(M, color, cell=0.62, txt_color=WHITE):
    g = VGroup()
    for i in range(N):
        for j in range(N):
            sq = Square(cell, stroke_color=color, stroke_width=2,
                        fill_color=color, fill_opacity=0.08)
            sq.move_to([j * cell, -i * cell, 0])
            t = num(M[i][j], cell * 0.34, txt_color).move_to(sq)
            g.add(VGroup(sq, t))
    return g.move_to(ORIGIN)


def corner_path(*pts):
    p = VMobject()
    p.set_points_as_corners([np.array([x, y, 0]) for x, y in pts])
    return p


# ============================================================================
class SystolicArrayExplained(MovingCameraScene):
    def construct(self):
        self.intro()
        self.pe_anatomy()
        self.array_run()
        self.summary()

    def clear_scene(self, run_time=0.8):
        if self.mobjects:
            self.play(*[FadeOut(m) for m in self.mobjects if m is not self.camera.frame],
                      run_time=run_time)
        self.clear()

    # ------------------------------------------------------------ 1. intro ---
    def intro(self):
        title = T("Systolic Array Matrix Multiplication", 50, weight=BOLD)
        sub = T("A 4×4 output-stationary accelerator, one clock cycle at a time", 28, GREY_B)
        VGroup(title, sub).arrange(DOWN, buff=0.35)
        self.play(Write(title), run_time=1.6)
        self.play(FadeIn(sub, shift=0.2 * UP))
        self.wait(1.2)
        self.play(FadeOut(sub), title.animate.scale(0.6).to_edge(UP, buff=0.3))

        gA = matrix_grid(A, A_COL)
        gB = matrix_grid(B, B_COL)
        gC = matrix_grid(np.full((N, N), "?"), ACC_COL, txt_color=GREY_B)
        times, eq = T("×", 48), T("=", 48)
        row = VGroup(gA, times, gB, eq, gC).arrange(RIGHT, buff=0.5).shift(0.5 * UP)
        lA = T("A", 36, A_COL, weight=BOLD).next_to(gA, UP, buff=0.2)
        lB = T("B", 36, B_COL, weight=BOLD).next_to(gB, UP, buff=0.2)
        lC = T("C", 36, ACC_COL, weight=BOLD).next_to(gC, UP, buff=0.2)
        self.play(LaggedStart(FadeIn(gA), FadeIn(lA), Write(times), FadeIn(gB), FadeIn(lB),
                              Write(eq), FadeIn(gC), FadeIn(lC), lag_ratio=0.15), run_time=2.2)

        # one dot product
        rbox = SurroundingRectangle(VGroup(*gA[0:4]), color=P_COL, buff=0.04)
        cbox = SurroundingRectangle(VGroup(*[gB[k * N] for k in range(N)]), color=P_COL, buff=0.04)
        obox = SurroundingRectangle(gC[0], color=P_COL, buff=0.04)
        terms = " + ".join(f"{A[0][k]}·{B[k][0]}" for k in range(N))
        e1 = T(f"C[0][0] = {terms} = {C[0][0]}", 32).next_to(row, DOWN, buff=0.8)
        e2 = T("In general  C[i][j] = Σ  A[i][k] · B[k][j]   for k = 0..3", 28, GREY_B)
        e2.next_to(e1, DOWN, buff=0.3)
        self.play(Create(rbox), Create(cbox))
        self.play(Write(e1), run_time=1.5)
        self.play(Create(obox), Transform(gC[0][1], num(C[0][0], 0.62 * 0.34, ACC_COL).move_to(gC[0])))
        self.play(FadeIn(e2))
        self.wait(1.5)

        count = T("16 outputs × 4 products each = 64 multiply-accumulates (MACs)", 30, P_COL)
        count.move_to(e1)
        seq = T("A single MAC unit does one per clock  →  64 clock cycles", 30)
        seq.next_to(count, DOWN, buff=0.3)
        self.play(FadeOut(VGroup(e1, e2, rbox, cbox, obox)), FadeIn(count))
        self.play(FadeIn(seq))

        tr = ValueTracker(0)
        ctr = T("cycle 0 / 64", 24, GREY_B).next_to(gC, DOWN, buff=0.15)
        ctr.add_updater(lambda m: m.become(
            T(f"cycle {int(tr.get_value())} / 64", 24, GREY_B).next_to(gC, DOWN, buff=0.15)))
        self.add(ctr)
        fills = [Transform(gC[x][1], num(C[x // N][x % N], 0.62 * 0.34, ACC_COL).move_to(gC[x]))
                 for x in range(N * N)]
        self.play(tr.animate.set_value(64), LaggedStart(*fills, lag_ratio=1.0),
                  run_time=4.5, rate_func=linear)
        ctr.clear_updaters()
        self.wait(0.6)

        idea = T("Systolic idea: 16 MAC units (PEs) in a grid. Data is pumped through them\n"
                 "rhythmically, like blood through the heart (systole)  →  11 clock cycles",
                 28, WHITE, line_spacing=1.2)
        idea.move_to(VGroup(count, seq))
        self.play(FadeOut(count), FadeOut(seq), FadeIn(idea))
        self.wait(2.5)
        self.clear_scene()

    # ------------------------------------------------------- 2. PE anatomy ---
    def pe_anatomy(self):
        title = T("Inside one Processing Element: PE(i,j)", 40, weight=BOLD).to_edge(UP, buff=0.3)
        self.play(Write(title), run_time=1.2)

        box = RoundedRectangle(corner_radius=0.15, width=6, height=4.2, stroke_color=WHITE,
                               stroke_width=3, fill_color=PE_FILL, fill_opacity=0.7)
        box.move_to([-1.2, -0.5, 0])
        ox, oy = -1.2, -0.5          # shift of every coordinate below
        P = lambda x, y: np.array([x + ox, y + oy, 0])

        W = dict(stroke_width=4)
        a_in = Arrow(P(-5.0, 1.0), P(-3.0, 1.0), buff=0, color=A_COL, **W)
        a_wire = Line(P(-3.0, 1.0), P(1.85, 1.0), color=A_COL, **W)
        a_tap = Arrow(P(-0.8, 1.0), P(-0.8, 0.32), buff=0, color=A_COL, **W)
        b_in = Arrow(P(-2.2, 3.1), P(-2.2, 1.6), buff=0, color=B_COL, **W)
        b_wire = Line(P(-2.2, 1.6), P(-2.2, -1.75), color=B_COL, **W)
        b_tap = Arrow(P(-2.2, 0.0), P(-1.12, 0.0), buff=0, color=B_COL, **W)
        dots = VGroup(Dot(P(-0.8, 1.0), color=A_COL), Dot(P(-2.2, 0.0), color=B_COL))

        mult = Circle(0.32, color=P_COL, stroke_width=4).move_to(P(-0.8, 0.0))
        mult_s = T("×", 34, P_COL).move_to(mult)
        adder = Circle(0.32, color=ACC_COL, stroke_width=4).move_to(P(0.7, 0.0))
        add_s = T("+", 34, ACC_COL).move_to(adder)
        m2a = Arrow(P(-0.48, 0), P(0.38, 0), buff=0, color=P_COL, **W)
        a2acc = Arrow(P(0.7, -0.32), P(0.7, -0.95), buff=0, color=ACC_COL, **W)
        acc_box = Rectangle(width=1.6, height=0.7, color=ACC_COL, stroke_width=4,
                            fill_color=ACC_COL, fill_opacity=0.12).move_to(P(0.7, -1.3))
        acc_lbl = T("acc", 22, GREY_B).move_to(P(0.3, -1.3))
        acc_val = num(4, 0.26, WHITE, bold=True).move_to(P(1.1, -1.3))
        fb = VMobject(color=ACC_COL, stroke_width=4)
        fb.set_points_as_corners([P(1.5, -1.3), P(1.95, -1.3), P(1.95, 0), P(1.12, 0)])
        fb_tip = Arrow(P(1.4, 0), P(1.02, 0), buff=0, color=ACC_COL, **W)

        a_reg = Rectangle(width=0.9, height=0.5, color=A_COL, stroke_width=4).move_to(P(2.3, 1.0))
        b_reg = Rectangle(width=0.9, height=0.5, color=B_COL, stroke_width=4).move_to(P(-2.2, -2.0))
        a_out = Arrow(P(2.75, 1.0), P(4.4, 1.0), buff=0, color=A_COL, **W)
        b_out = Arrow(P(-2.2, -2.25), P(-2.2, -3.4), buff=0, color=B_COL, **W)

        en = Arrow(P(-1.2, -1.15), P(-0.1, -1.15), buff=0, color=GREY_B, stroke_width=3,
                   max_tip_length_to_length_ratio=0.15)
        clr = Arrow(P(-1.2, -1.45), P(-0.1, -1.45), buff=0, color=GREY_B, stroke_width=3,
                    max_tip_length_to_length_ratio=0.15)
        en_l = T("en", 18, GREY_B).next_to(en, LEFT, buff=0.08)
        clr_l = T("clear", 18, GREY_B).next_to(clr, LEFT, buff=0.08)

        labels = VGroup(
            T("a_in", 24, A_COL).next_to(a_in, UP, buff=0.08),
            T("b_in", 24, B_COL).next_to(b_in, RIGHT, buff=0.1),
            T("multiply", 18, GREY_B).next_to(mult, DOWN, buff=0.1),
            T("add", 18, GREY_B).next_to(adder, UP, buff=0.1).shift(0.25 * RIGHT),
            T("accumulator = C[i][j]", 18, GREY_B).next_to(acc_box, DOWN, buff=0.1),
            T("a_out reg", 18, A_COL).next_to(a_reg, UP, buff=0.08),
            T("b_out reg", 18, B_COL).next_to(b_reg, RIGHT, buff=0.1),
            T("to PE(i, j+1)", 20, A_COL).next_to(a_out, DOWN, buff=0.08),
            T("to PE(i+1, j)", 20, B_COL).next_to(b_out, RIGHT, buff=0.1),
        )
        pe_lbl = T("PE(i,j)", 22, GREY_B).move_to(box.get_corner(UR) + np.array([-0.6, -0.25, 0]))

        diagram = VGroup(box, a_wire, b_wire, a_tap, b_tap, dots, mult, mult_s, adder, add_s,
                         m2a, a2acc, acc_box, acc_lbl, acc_val, fb, fb_tip, a_reg, b_reg,
                         a_in, b_in, a_out, b_out, en, clr, en_l, clr_l, labels, pe_lbl)
        self.play(FadeIn(box), FadeIn(pe_lbl))
        self.play(LaggedStart(Create(a_in), Create(b_in), Create(a_wire), Create(b_wire),
                              Create(a_tap), Create(b_tap), FadeIn(dots), lag_ratio=0.15), run_time=1.6)
        self.play(LaggedStart(Create(mult), Write(mult_s), Create(m2a), Create(adder), Write(add_s),
                              Create(a2acc), Create(acc_box), FadeIn(acc_lbl), FadeIn(acc_val),
                              Create(fb), Create(fb_tip), lag_ratio=0.1), run_time=2)
        self.play(Create(a_reg), Create(b_reg), Create(a_out), Create(b_out),
                  FadeIn(en), FadeIn(clr), FadeIn(en_l), FadeIn(clr_l))
        self.play(FadeIn(labels))

        # caption area on the right
        cap_pos = np.array([5.0, -0.6, 0])
        cap = T("", 24)

        def caption(s):
            new = T(s, 24, WHITE, line_spacing=1.15)
            fit_w(new, 3.9).move_to(cap_pos)
            return new

        a_tok = token(3, A_COL, 0.5, 0.42).move_to(P(-4.4, 1.0))
        b_tok = token(2, B_COL, 0.5, 0.42).move_to(P(-2.2, 2.7))
        c1 = caption("1. One clock cycle.\na_in = 3 arrives from the\nleft, b_in = 2 from above.")
        self.play(FadeIn(a_tok, shift=RIGHT * 0.3), FadeIn(b_tok, shift=DOWN * 0.3), FadeIn(c1))
        cap = c1
        self.play(a_tok.animate.move_to(P(-0.8, 1.0)), b_tok.animate.move_to(P(-2.2, 0.0)), run_time=1.2)

        a_cp, b_cp = a_tok.copy(), b_tok.copy()
        self.add(a_cp, b_cp)
        c2 = caption("2. Each value is used here\nAND sent on to the next PE.")
        self.play(Transform(cap, c2),
                  a_cp.animate.move_to(P(-0.8, 0.0)), b_cp.animate.move_to(P(-0.8, 0.0)),
                  a_tok.animate.move_to(P(1.4, 1.0)), b_tok.animate.move_to(P(-2.2, -1.3)),
                  run_time=1.3)
        p_tok = token(6, P_COL, 0.5, 0.42).move_to(P(-0.8, 0.0))
        c3 = caption("3. Multiply:\n3 × 2 = 6")
        self.play(Transform(cap, c3), ReplacementTransform(VGroup(a_cp, b_cp), p_tok),
                  Flash(mult, color=P_COL, flash_radius=0.5))
        acc_cp = token(4, ACC_COL, 0.5, 0.42).move_to(acc_val)
        self.add(acc_cp)
        fb_path = corner_path((1.1 + ox, -1.3 + oy), (1.95 + ox, -1.3 + oy), (1.95 + ox, 0 + oy),
                              (0.7 + ox, 0 + oy))
        c4 = caption("4. Add to the running sum\nfed back from acc:\n4 + 6 = 10")
        self.play(Transform(cap, c4), p_tok.animate.move_to(P(0.7, 0)),
                  MoveAlongPath(acc_cp, fb_path), run_time=1.4)
        s_tok = token(10, ACC_COL, 0.5, 0.42).move_to(P(0.7, 0))
        self.play(ReplacementTransform(VGroup(p_tok, acc_cp), s_tok),
                  Flash(adder, color=ACC_COL, flash_radius=0.5))

        clk = T("▲ rising clock edge", 26, P_COL, weight=BOLD).move_to(P(1.3, 2.25))
        c5 = caption("5. On the rising clock edge\nall registers update together:\nacc ← 10, a_out ← 3, b_out ← 2")
        self.play(Transform(cap, c5), FadeIn(clk, scale=1.3))
        self.play(s_tok.animate.move_to(acc_val),
                  a_tok.animate.move_to(a_reg), b_tok.animate.move_to(b_reg), run_time=0.9)
        self.play(FadeOut(s_tok), Transform(acc_val, num(10, 0.26, WHITE, bold=True).move_to(acc_val)),
                  Indicate(acc_box, color=ACC_COL), Indicate(a_reg, color=A_COL),
                  Indicate(b_reg, color=B_COL))
        c6 = caption("6. Next cycle: 3 moves right\nand 2 moves down, while\nC[i][j] stays put.\n"
                     "(output-stationary)")
        self.play(Transform(cap, c6), FadeOut(clk),
                  a_tok.animate.move_to(P(3.9, 1.0)).set_opacity(0),
                  b_tok.animate.move_to(P(-2.2, -3.1)).set_opacity(0), run_time=1.4)
        self.remove(a_tok, b_tok)
        self.wait(1.2)

        # Verilog
        code_lines = [
            "always @(posedge clk) begin",
            "  if (rst) begin",
            "    a_out <= 0; b_out <= 0; acc <= 0;",
            "  end else begin",
            "    a_out <= a_in;      // pass right",
            "    b_out <= b_in;      // pass down",
            "    if (clear)   acc <= 0;",
            "    else if (en) acc <= acc + a_in*b_in;",
            "  end",
            "end",
        ]
        code = VGroup(*[T(l.replace(' ', '\u00a0'), 20, WHITE, font=MONO) for l in code_lines])
        code.arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        hl = {4: A_COL, 5: B_COL, 7: ACC_COL, 6: GREY_B}
        for idx, col in hl.items():
            code[idx].set_color(col)
        code_bg = SurroundingRectangle(code, buff=0.25, color=GREY_D, fill_color="#0B0D11",
                                       fill_opacity=1, corner_radius=0.1)
        code_t = T("rtl/pe.v", 22, GREY_B, font=MONO).next_to(code_bg, UP, buff=0.12, aligned_edge=LEFT)
        code_grp = VGroup(code_bg, code, code_t).move_to([3.35, -0.4, 0])
        self.play(FadeOut(cap), diagram.animate.scale(0.62).move_to([-3.9, -0.4, 0]))
        self.play(FadeIn(code_grp, shift=LEFT * 0.3))
        note = T("8-bit signed inputs, 32-bit signed accumulator", 22, GREY_B)
        note.next_to(code_grp, DOWN, buff=0.3)
        self.play(FadeIn(note))
        self.wait(3)
        self.clear_scene()

    # ------------------------------------------------------- 3. the array ---
    def array_run(self):
        frame = self.camera.frame
        H = 10.8
        K = H / frame.height
        frame.scale(K).move_to([4.0, 0.4, 0])

        def F(x):          # font size that looks like x at the default zoom
            return x * K

        S, OFF, Q = 1.2, 0.25, 0.55

        def ax(c):
            return c * S if c >= -1 else -S + (c + 1) * Q

        def a_pos(i, c):
            return np.array([ax(c) - OFF, -i * S + 0.2, 0])

        def b_pos(j, r):
            return np.array([j * S + OFF, -ax(r) + 0.2, 0])

        def pe_c(i, j):
            return np.array([j * S, -i * S, 0])

        # ---- right-hand panel
        PX = 5.4                     # panel left edge
        title = fit_w(T("4×4 output-stationary systolic array", F(26), weight=BOLD), 7.8)
        title.move_to([PX, 5.25, 0], aligned_edge=LEFT)
        t_txt = T("", F(40))
        cyc_txt = T("", F(26))
        state_txt = T("", F(28))
        mac_txt = T("", F(24))
        expl = T("", F(24))

        def mk_t(t):
            s = "t = –" if t is None else f"t = {t}"
            return T(s, F(42), P_COL, weight=BOLD).move_to([PX, 4.25, 0], aligned_edge=LEFT)

        def mk_cyc(c):
            return T(f"clock cycle {c} / 11", F(24), GREY_B).move_to([PX + 3.3, 4.2, 0], aligned_edge=LEFT)

        st_col = {"IDLE": GREY_B, "CLEAR": "#C77DFF", "COMPUTE": A_COL, "DRAIN": "#F78FB3", "DONE": DONE_COL}

        def mk_state(s, extra=""):
            g = VGroup(T("state:", F(26), GREY_B), T(s, F(26), st_col[s], weight=BOLD))
            if extra:
                g.add(T(extra, F(20), GREY_B))
            g.arrange(RIGHT, buff=0.25)
            return g.move_to([PX, 3.3, 0], aligned_edge=LEFT)

        def mk_mac(n):
            s = "" if n is None else f"MACs this cycle: {n} of 16"
            return T(s, F(24), P_COL).move_to([PX, 2.6, 0], aligned_edge=LEFT)

        def mk_expl(s):
            m = T(s, F(22), WHITE, line_spacing=1.2)
            fit_w(m, 7.6)
            return m.move_to([PX, 1.35, 0], aligned_edge=LEFT)

        rule = VGroup(
            T("PE(i,j) multiplies  A[i][k] × B[k][j]", F(22)),
            T("at cycle  t = i + j + k", F(22), P_COL, weight=BOLD),
        ).arrange(DOWN, buff=0.15, aligned_edge=LEFT)
        rule_box = SurroundingRectangle(rule, buff=0.2, color=GREY_D, corner_radius=0.1)
        rule_g = VGroup(rule_box, rule).move_to([PX, -0.35, 0], aligned_edge=LEFT)

        # timeline: CLEAR | t0..t6 COMPUTE | t7..t9 DRAIN | DONE
        cw = 0.56
        tl = VGroup()
        cols = ["CLEAR"] + ["COMPUTE"] * 7 + ["DRAIN"] * 3 + ["DONE"]
        for n, s in enumerate(cols):
            w = cw if s != "DONE" else 1.0
            r = Rectangle(width=w, height=0.45, stroke_color=BG, stroke_width=3,
                          fill_color=st_col[s], fill_opacity=0.55)
            tl.add(r)
        tl.arrange(RIGHT, buff=0).move_to([PX, -2.15, 0], aligned_edge=LEFT)
        tl_nums = VGroup(*[T(str(n + 1), F(16), WHITE).move_to(tl[n]) for n in range(11)])
        tl_nums.add(T("done", F(16), WHITE).move_to(tl[11]))
        tl_lbls = VGroup(
            T("CLEAR", F(14), st_col["CLEAR"]).next_to(tl[0], UP, buff=0.1),
            T("COMPUTE  t = 0..6", F(16), st_col["COMPUTE"]).next_to(VGroup(*tl[1:8]), UP, buff=0.1),
            T("DRAIN  t = 7..9", F(16), st_col["DRAIN"]).next_to(VGroup(*tl[8:11]), UP, buff=0.1),
        )
        tl_cap = T("start → done = 11 clock cycles", F(18), GREY_B).next_to(tl, DOWN, buff=0.45)
        tl_cap.align_to(tl, LEFT)
        ptr = Triangle(color=P_COL, fill_opacity=1).scale(0.12).rotate(PI)
        ptr.next_to(tl[0], DOWN, buff=0.06)
        ptr.set_opacity(0)

        legend = VGroup(
            VGroup(token("a", A_COL), T("A value (moves right)", F(18), GREY_B)).arrange(RIGHT, buff=0.15),
            VGroup(token("b", B_COL), T("B value (moves down)", F(18), GREY_B)).arrange(RIGHT, buff=0.15),
            VGroup(num(7, 0.24, WHITE, bold=True), T("accumulator C[i][j] (stays)", F(18), GREY_B)).arrange(RIGHT, buff=0.2),
        ).arrange(DOWN, buff=0.18, aligned_edge=LEFT).move_to([PX, -4.15, 0], aligned_edge=LEFT)

        # ---- array, tracks and edge labels
        tracks = VGroup()
        for i in range(N):
            tracks.add(Line([-4.95, -i * S + 0.2, 0], [4.45, -i * S + 0.2, 0],
                            color=A_COL, stroke_width=2, stroke_opacity=0.25))
        for j in range(N):
            tracks.add(Line([j * S + OFF, 5.05, 0], [j * S + OFF, -4.1, 0],
                            color=B_COL, stroke_width=2, stroke_opacity=0.25))
        pes, accs = {}, {}
        pe_grp, acc_grp = VGroup(), VGroup()
        for i in range(N):
            for j in range(N):
                sq = RoundedRectangle(corner_radius=0.08, width=1.0, height=1.0, stroke_color=IDLE,
                                      stroke_width=3, fill_color=PE_FILL, fill_opacity=0.85)
                sq.move_to(pe_c(i, j))
                pes[i, j] = sq
                pe_grp.add(sq)
                a = num("?", 0.26, GREY_B, bold=True).move_to(pe_c(i, j) + np.array([0, -0.24, 0]))
                accs[i, j] = a
                acc_grp.add(a)
        row_l = VGroup(*[T(f"row {i}", F(16), A_COL).move_to([-0.95, -i * S - 0.32, 0]) for i in range(N)])
        col_l = VGroup(*[T(f"col {j}", F(16), B_COL).move_to([j * S - 0.2, 0.92, 0]) for j in range(N)])
        a_head = fit_w(T("A enters from the left: row i feeds array row i", F(20), A_COL), 5.0)
        a_head.move_to([-2.6, -4.55, 0])
        b_head = T("B enters from the top:\ncolumn j feeds\narray column j", F(20), B_COL, line_spacing=1.1)
        b_head.move_to([-2.9, 4.2, 0])

        self.play(FadeIn(title))
        self.play(LaggedStart(*[FadeIn(sq, scale=0.8) for sq in pe_grp], lag_ratio=0.05), run_time=1.5)
        self.play(FadeIn(tracks), FadeIn(acc_grp), FadeIn(row_l), FadeIn(col_l))
        expl = mk_expl("16 PEs wired in a grid. Every PE talks only\nto its right and lower neighbour."
                       "\nPE(i,j) holds C[i][j] in its accumulator.")
        self.play(FadeIn(expl))
        self.wait(1.5)

        # ---- tokens: loaded, unskewed (element k = 0 nearest the array)
        a_tok, b_tok = {}, {}
        for i in range(N):
            for k in range(N):
                a_tok[i, k] = token(A[i][k], A_COL).move_to(a_pos(i, -1 - k))
        for k in range(N):
            for j in range(N):
                b_tok[k, j] = token(B[k][j], B_COL).move_to(b_pos(j, -1 - k))
        e = mk_expl("A and B wait in the input buffer.\nRow i of A will feed array row i (A[i][0] first);\n"
                    "column j of B will feed array column j (B[0][j] first).")
        self.play(Transform(expl, e), FadeIn(a_head), FadeIn(b_head),
                  LaggedStart(*[FadeIn(t, shift=0.2 * RIGHT) for t in a_tok.values()], lag_ratio=0.03),
                  LaggedStart(*[FadeIn(t, shift=0.2 * DOWN) for t in b_tok.values()], lag_ratio=0.03),
                  run_time=2.2)
        self.wait(2)

        # ---- skew
        e = mk_expl("Skew: row i of A is delayed by i cycles,\ncolumn j of B by j cycles.\n"
                    "Now matching pairs arrive at the right PE together.")
        self.play(Transform(expl, e))
        self.play(*[a_tok[i, k].animate.move_to(a_pos(i, -1 - k - i)) for i in range(N) for k in range(N)],
                  *[b_tok[k, j].animate.move_to(b_pos(j, -1 - k - j)) for k in range(N) for j in range(N)],
                  run_time=2)
        self.wait(1.5)
        self.play(FadeIn(rule_g, shift=0.2 * UP))
        self.wait(2.5)

        # ---- CLEAR
        t_txt = mk_t(None)
        cyc_txt = mk_cyc(1)
        state_txt = mk_state("CLEAR", "(start pulsed)")
        self.play(FadeIn(t_txt), FadeIn(cyc_txt), FadeIn(state_txt),
                  FadeIn(tl), FadeIn(tl_nums), FadeIn(tl_lbls), FadeIn(tl_cap), FadeIn(legend))
        ptr.set_opacity(1)
        self.play(FadeIn(ptr, shift=0.2 * DOWN),
                  Transform(expl, mk_expl("Cycle 1, CLEAR: clear = 1 resets all 16\naccumulators to 0.")))
        self.play(*[Transform(accs[i, j], num(0, 0.26, WHITE, bold=True).move_to(accs[i, j]))
                    for i in range(N) for j in range(N)],
                  *[sq.animate.set_stroke("#C77DFF") for sq in pe_grp], run_time=0.8)
        self.play(*[sq.animate.set_stroke(IDLE) for sq in pe_grp], run_time=0.5)
        self.wait(0.8)
        mac_txt = mk_mac(None)
        self.add(mac_txt)

        # ---- the 10 compute / drain cycles
        acc_v = np.zeros((N, N), dtype=int)
        alive_a = set(a_tok.keys())
        alive_b = set(b_tok.keys())

        notes = {
            0: "t = 0: only PE(0,0) has a matching pair:\nA[0][0] meets B[0][0].",
            1: "t = 1: every value moved one PE (A right, B down).\nPE(0,1) and PE(1,0) start; PE(0,0) does its 2nd MAC.",
            2: "t = 2: the active region is a diagonal wavefront\nsweeping from the top-left to the bottom-right.",
            3: "t = 3: PE(0,0) has done all 4 products:\nC[0][0] is final (green).",
            4: "t = 4: 12 PEs busy at once: this parallelism\nis where the speed-up comes from.",
            5: "t = 5: still 12 MACs in one clock cycle.\nThe one-MAC baseline does 1.",
            6: "t = 6: the last inputs A[3][3] and B[3][3] enter.\nCOMPUTE ends; feed_en drops to 0.",
            7: "t = 7, DRAIN: no new inputs, zeros come in.\nValues already inside keep flowing; en stays 1.",
            8: "t = 8: only the bottom-right corner is still working.",
            9: "t = 9 = 3N − 3: PE(3,3) does the very last product\nA[3][3] × B[3][3].",
        }

        for t in range(10):
            fast = t >= 3
            rt = 0.7 if fast else 1.1
            # (1) clock edge: every value advances one PE
            moves, exits = [], []
            for (i, k) in list(alive_a):
                c = t - i - k
                if c <= 3:
                    moves.append(a_tok[i, k].animate.move_to(a_pos(i, c)))
                elif c == 4:
                    exits.append(a_tok[i, k])
                    moves.append(a_tok[i, k].animate.move_to(a_pos(i, 4)).set_opacity(0))
                    alive_a.discard((i, k))
            for (k, j) in list(alive_b):
                r = t - j - k
                if r <= 3:
                    moves.append(b_tok[k, j].animate.move_to(b_pos(j, r)))
                elif r == 4:
                    exits.append(b_tok[k, j])
                    moves.append(b_tok[k, j].animate.move_to(b_pos(j, 4)).set_opacity(0))
                    alive_b.discard((k, j))
            active = [(i, j) for i in range(N) for j in range(N) if 0 <= t - i - j < N]
            state = "COMPUTE" if t <= 6 else "DRAIN"
            extra = "(feed_en = 1, en = 1)" if t <= 6 else "(feed_en = 0, en = 1)"
            pe_anims = []
            for (i, j) in active:
                pe_anims.append(pes[i, j].animate.set_stroke(P_COL, width=5))
            self.play(*moves,
                      Transform(t_txt, mk_t(t)), Transform(cyc_txt, mk_cyc(t + 2)),
                      Transform(state_txt, mk_state(state, extra)),
                      Transform(mac_txt, mk_mac(len(active))),
                      ptr.animate.next_to(tl[t + 1], DOWN, buff=0.06),
                      Transform(expl, mk_expl(notes[t])),
                      *pe_anims, run_time=rt)
            self.remove(*exits)

            # (2) every active PE multiplies its pair and adds to acc
            plus, glow = [], []
            for (i, j) in active:
                k = t - i - j
                p = int(A[i][k] * B[k][j])
                s = f"+{p}" if p >= 0 else f"−{-p}"
                pl = T(s, F(18), P_COL, weight=BOLD).move_to(pe_c(i, j) + np.array([0, -0.02, 0]))
                pl.set_stroke(BG, width=4, background=True)
                plus.append(pl)
                glow.append(pes[i, j].animate.set_fill(P_COL, opacity=0.35))
            self.play(*[FadeIn(pl, scale=0.6) for pl in plus], *glow, run_time=0.45 if fast else 0.7)
            upd = []
            for n, (i, j) in enumerate(active):
                k = t - i - j
                acc_v[i, j] += int(A[i][k] * B[k][j])
                upd.append(Transform(accs[i, j], num(acc_v[i, j], 0.26, WHITE, bold=True).move_to(accs[i, j])))
                upd.append(plus[n].animate.move_to(accs[i, j]).set_opacity(0))
                fin = (t - i - j == N - 1)
                upd.append(pes[i, j].animate.set_fill(PE_FILL, opacity=0.85)
                           .set_stroke(DONE_COL if fin else P_COL, width=5 if fin else 5))
            self.play(*upd, run_time=0.5 if fast else 0.8)
            self.remove(*plus)
            # PEs that were active last cycle but not now: done (green) - already handled; idle stays grey
            self.wait(0.6 if fast else 1.6)
            # active-but-not-finished PEs go back to grey before the next edge
            back = [pes[i, j].animate.set_stroke(IDLE, width=3)
                    for (i, j) in active if t - i - j < N - 1]
            if back:
                self.play(*back, run_time=0.2)

        # ---- DONE
        moves = []
        for (i, k) in list(alive_a):
            moves.append(a_tok[i, k].animate.move_to(a_pos(i, 4)).set_opacity(0))
        for (k, j) in list(alive_b):
            moves.append(b_tok[k, j].animate.move_to(b_pos(j, 4)).set_opacity(0))
        self.play(*moves, Transform(t_txt, mk_t(None)), Transform(cyc_txt, mk_cyc(11)),
                  Transform(state_txt, mk_state("DONE", "(done = 1, busy = 0)")),
                  Transform(mac_txt, mk_mac(None)),
                  ptr.animate.next_to(tl[11], DOWN, buff=0.06),
                  Transform(expl, mk_expl("DONE after 11 clock cycles. C stays in the\n"
                                          "accumulators; the output collector reads\nC[r][c] by row and column.")),
                  run_time=1.0)
        self.remove(*[a_tok[x] for x in alive_a], *[b_tok[x] for x in alive_b])
        self.wait(1.5)

        # ---- check against numpy
        gC = matrix_grid(C, ACC_COL, cell=0.62)
        lbl = T("Expected C = A × B (numpy)", F(22), ACC_COL)
        VGroup(lbl, gC).arrange(DOWN, buff=0.25).move_to([PX + 3.3, 1.4, 0])
        self.play(FadeOut(VGroup(t_txt, cyc_txt, state_txt, mac_txt, expl, rule_g)), FadeIn(lbl), FadeIn(gC))
        ok = bool((acc_v == C).all())
        self.play(LaggedStart(*[Indicate(VGroup(pes[i, j], gC[i * N + j]), color=DONE_COL, scale_factor=1.06)
                                for i in range(N) for j in range(N)], lag_ratio=0.08), run_time=2.4)
        verdict = T("✓  16 / 16 accumulators match" if ok else "✗  mismatch", F(28),
                    DONE_COL if ok else RED, weight=BOLD).next_to(gC, DOWN, buff=0.3)
        self.play(Write(verdict))
        self.wait(2.5)
        self.clear_scene()
        frame.scale(1 / K).move_to(ORIGIN)

    # ---------------------------------------------------------- 4. summary ---
    def summary(self):
        title = T("Systolic array vs one-MAC baseline", 40, weight=BOLD).to_edge(UP, buff=0.4)
        sub = T("Vivado 2026.1, Basys 3 (Artix-7 xc7a35t), 100 MHz target", 22, GREY_B)
        sub.next_to(title, DOWN, buff=0.15)
        self.play(Write(title), FadeIn(sub))

        unit = 0.13
        seq_bar = Rectangle(width=64 * unit, height=0.55, stroke_width=0, fill_color="#E06C75", fill_opacity=0.9)
        sys_bar = Rectangle(width=11 * unit, height=0.55, stroke_width=0, fill_color=A_COL, fill_opacity=0.9)
        seq_l = T("sequential_mac", 26, font=MONO)
        sys_l = T("systolic_top", 26, font=MONO)
        labels = VGroup(seq_l, sys_l).arrange(DOWN, buff=0.6, aligned_edge=RIGHT).move_to([-4.6, 1.0, 0])
        seq_bar.next_to(seq_l, RIGHT, buff=0.3)
        sys_bar.next_to(sys_l, RIGHT, buff=0.3)
        sys_bar.align_to(seq_bar, LEFT)
        seq_v = T("64 cycles", 26).next_to(seq_bar, RIGHT, buff=0.2)
        sys_v = T("11 cycles", 26, A_COL, weight=BOLD).next_to(sys_bar, RIGHT, buff=0.2)
        self.play(FadeIn(labels))
        self.play(GrowFromEdge(seq_bar, LEFT), GrowFromEdge(sys_bar, LEFT), run_time=1.5)
        self.play(FadeIn(seq_v), FadeIn(sys_v))

        rows = [
            ("", "baseline", "systolic", ""),
            ("Fmax", "94.9 MHz", "99.4 MHz", ""),
            ("Time per 4×4 multiply", "674.4 ns", "110.6 ns", "6.1× faster"),
            ("LUTs", "390", "1,940", "≈ 5× more area"),
            ("Flip-flops", "825", "987", "1.2× more"),
        ]
        tbl = VGroup()
        for r, row in enumerate(rows):
            cells = VGroup(
                T(row[0], 24, GREY_B),
                T(row[1], 24, WHITE if r else GREY_B),
                T(row[2], 24, A_COL if r else GREY_B, weight=BOLD if r else NORMAL),
                T(row[3], 24, P_COL, weight=BOLD),
            )
            xs = [-5.6, -0.6, 1.6, 3.8]
            for c, m in zip(cells, xs):
                c.move_to([m, 0, 0], aligned_edge=LEFT)
            cells.shift(DOWN * (0.7 + 0.5 * r))
            tbl.add(cells)
        self.play(LaggedStart(*[FadeIn(r, shift=0.15 * UP) for r in tbl], lag_ratio=0.25), run_time=2)
        why = T("Up to 12 MACs per cycle, and every wire is short: each PE only talks to its neighbours.",
                24, WHITE)
        fit_w(why, 12.5).to_edge(DOWN, buff=0.45)
        self.play(FadeIn(why))
        self.wait(4)
        self.clear_scene()

        end = VGroup(
            T("Project 12: Systolic Array Matrix Multiplication Accelerator", 34, weight=BOLD),
            T("Modern Computer Architecture", 26, GREY_B),
            T("Parrv · Raghav · Ranjeet · Abhijeet · Malhar", 26, A_COL),
        ).arrange(DOWN, buff=0.35)
        self.play(FadeIn(end, shift=0.2 * UP))
        self.wait(3)
        self.play(FadeOut(end))
