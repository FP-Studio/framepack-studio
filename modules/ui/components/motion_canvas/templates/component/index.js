const {
  SvelteComponent: je,
  add_iframe_resize_listener: Ve,
  add_render_callback: Le,
  append_hydration: k,
  attr: i,
  binding_callbacks: Oe,
  children: A,
  claim_element: J,
  claim_space: ae,
  claim_svg_element: W,
  claim_text: Q,
  destroy_each: we,
  detach: b,
  element: K,
  empty: me,
  ensure_array_like: be,
  get_svelte_dataset: Ue,
  init: We,
  insert_hydration: R,
  listen: ue,
  noop: ke,
  run_all: qe,
  safe_not_equal: Xe,
  set_data: de,
  set_style: _e,
  space: re,
  src_url_equal: ze,
  svg_element: q,
  text: Z,
  toggle_class: $
} = window.__gradio__svelte__internal;
function pe(l) {
  const e = l.slice(), t = (
    /*draft*/
    e[19][0] * /*w*/
    e[9]
  );
  e[46] = t;
  const n = (
    /*draft*/
    e[19][1] * /*h*/
    e[10]
  );
  e[47] = n;
  const o = (
    /*draft*/
    e[19][2] * /*w*/
    e[9]
  );
  e[48] = o;
  const s = (
    /*draft*/
    e[19][3] * /*h*/
    e[10]
  );
  e[49] = s;
  const _ = ye(
    /*x0*/
    e[46],
    /*y0*/
    e[47],
    /*x1*/
    e[48],
    /*y1*/
    e[49],
    10
  );
  return e[50] = _[0], e[51] = _[1], e;
}
function Ee(l, e, t) {
  const n = l.slice();
  n[52] = e[t], n[56] = t;
  const o = (
    /*a*/
    n[52][0] * /*w*/
    n[9]
  );
  n[46] = o;
  const s = (
    /*a*/
    n[52][1] * /*h*/
    n[10]
  );
  n[47] = s;
  const _ = (
    /*a*/
    n[52][2] * /*w*/
    n[9]
  );
  n[48] = _;
  const r = (
    /*a*/
    n[52][3] * /*h*/
    n[10]
  );
  n[49] = r;
  const c = (
    /*selected*/
    n[11] === /*i*/
    n[56]
  );
  n[53] = c;
  const f = (
    /*sel*/
    n[53] ? 18 : 14
  );
  n[54] = f;
  const p = ye(
    /*x0*/
    n[46],
    /*y0*/
    n[47],
    /*x1*/
    n[48],
    /*y1*/
    n[49],
    /*hs*/
    n[54] * 0.7
  );
  return n[50] = p[0], n[51] = p[1], n;
}
function Me(l, e, t) {
  const n = l.slice();
  n[46] = e[t][0], n[47] = e[t][1], n[48] = e[t][2], n[49] = e[t][3];
  const o = ye(
    /*x0*/
    n[46],
    /*y0*/
    n[47],
    /*x1*/
    n[48],
    /*y1*/
    n[49],
    4
  );
  return n[50] = o[0], n[51] = o[1], n;
}
function De(l) {
  let e, t;
  return {
    c() {
      e = K("span"), t = Z(
        /*label*/
        l[4]
      ), this.h();
    },
    l(n) {
      e = J(n, "SPAN", { class: !0 });
      var o = A(e);
      t = Q(
        o,
        /*label*/
        l[4]
      ), o.forEach(b), this.h();
    },
    h() {
      i(e, "class", "block-label svelte-1t2zk1p");
    },
    m(n, o) {
      R(n, e, o), k(e, t);
    },
    p(n, o) {
      o[0] & /*label*/
      16 && de(
        t,
        /*label*/
        n[4]
      );
    },
    d(n) {
      n && b(e);
    }
  };
}
function Ge(l) {
  let e, t = '<span class="svelte-1t2zk1p">Add a start frame to draw on it</span>';
  return {
    c() {
      e = K("div"), e.innerHTML = t, this.h();
    },
    l(n) {
      e = J(n, "DIV", { class: !0, "data-svelte-h": !0 }), Ue(e) !== "svelte-h6jafv" && (e.innerHTML = t), this.h();
    },
    h() {
      i(e, "class", "hint-empty svelte-1t2zk1p");
    },
    m(n, o) {
      R(n, e, o);
    },
    p: ke,
    d(n) {
      n && b(e);
    }
  };
}
function Re(l) {
  let e, t, n, o;
  return {
    c() {
      e = K("img"), this.h();
    },
    l(s) {
      e = J(s, "IMG", {
        src: !0,
        alt: !0,
        draggable: !0,
        class: !0
      }), this.h();
    },
    h() {
      ze(e.src, t = /*src*/
      l[16]) || i(e, "src", t), i(e, "alt", "Start frame"), i(e, "draggable", "false"), i(e, "class", "svelte-1t2zk1p");
    },
    m(s, _) {
      R(s, e, _), n || (o = ue(
        e,
        "load",
        /*on_img_load*/
        l[30]
      ), n = !0);
    },
    p(s, _) {
      _[0] & /*src*/
      65536 && !ze(e.src, t = /*src*/
      s[16]) && i(e, "src", t);
    },
    d(s) {
      s && b(e), n = !1, o();
    }
  };
}
function Ne(l) {
  let e, t, n, o, s, _, r, c;
  return {
    c() {
      e = q("g"), t = q("line"), r = q("polygon"), this.h();
    },
    l(f) {
      e = W(f, "g", { class: !0 });
      var p = A(e);
      t = W(p, "line", {
        x1: !0,
        y1: !0,
        x2: !0,
        y2: !0,
        class: !0
      }), A(t).forEach(b), r = W(p, "polygon", { points: !0, class: !0 }), A(r).forEach(b), p.forEach(b), this.h();
    },
    h() {
      i(t, "x1", n = /*x0*/
      l[46]), i(t, "y1", o = /*y0*/
      l[47]), i(t, "x2", s = /*sx*/
      l[50]), i(t, "y2", _ = /*sy*/
      l[51]), i(t, "class", "svelte-1t2zk1p"), i(r, "points", c = ve(
        /*x0*/
        l[46],
        /*y0*/
        l[47],
        /*x1*/
        l[48],
        /*y1*/
        l[49],
        8
      )), i(r, "class", "svelte-1t2zk1p"), i(e, "class", "cam svelte-1t2zk1p");
    },
    m(f, p) {
      R(f, e, p), k(e, t), k(e, r);
    },
    p(f, p) {
      p[0] & /*cam_vectors*/
      2097152 && n !== (n = /*x0*/
      f[46]) && i(t, "x1", n), p[0] & /*cam_vectors*/
      2097152 && o !== (o = /*y0*/
      f[47]) && i(t, "y1", o), p[0] & /*cam_vectors*/
      2097152 && s !== (s = /*sx*/
      f[50]) && i(t, "x2", s), p[0] & /*cam_vectors*/
      2097152 && _ !== (_ = /*sy*/
      f[51]) && i(t, "y2", _), p[0] & /*cam_vectors*/
      2097152 && c !== (c = ve(
        /*x0*/
        f[46],
        /*y0*/
        f[47],
        /*x1*/
        f[48],
        /*y1*/
        f[49],
        8
      )) && i(r, "points", c);
    },
    d(f) {
      f && b(e);
    }
  };
}
function Ae(l) {
  let e, t, n, o, s, _, r, c, f, p, C, I, M, v, z, y, g, h, B, X, E, ee, G, ne;
  function se(...U) {
    return (
      /*pointerdown_handler*/
      l[41](
        /*i*/
        l[56],
        ...U
      )
    );
  }
  return {
    c() {
      e = q("g"), t = q("line"), r = q("line"), I = q("polygon"), v = q("circle"), h = q("line"), this.h();
    },
    l(U) {
      e = W(U, "g", { class: !0 });
      var w = A(e);
      t = W(w, "line", {
        class: !0,
        x1: !0,
        y1: !0,
        x2: !0,
        y2: !0
      }), A(t).forEach(b), r = W(w, "line", {
        class: !0,
        x1: !0,
        y1: !0,
        x2: !0,
        y2: !0
      }), A(r).forEach(b), I = W(w, "polygon", { points: !0, class: !0 }), A(I).forEach(b), v = W(w, "circle", { cx: !0, cy: !0, r: !0, class: !0 }), A(v).forEach(b), h = W(w, "line", {
        class: !0,
        x1: !0,
        y1: !0,
        x2: !0,
        y2: !0,
        role: !0,
        tabindex: !0,
        "aria-label": !0
      }), A(h).forEach(b), w.forEach(b), this.h();
    },
    h() {
      i(t, "class", "outline svelte-1t2zk1p"), i(t, "x1", n = /*x0*/
      l[46]), i(t, "y1", o = /*y0*/
      l[47]), i(t, "x2", s = /*sx*/
      l[50]), i(t, "y2", _ = /*sy*/
      l[51]), i(r, "class", "fill svelte-1t2zk1p"), i(r, "x1", c = /*x0*/
      l[46]), i(r, "y1", f = /*y0*/
      l[47]), i(r, "x2", p = /*sx*/
      l[50]), i(r, "y2", C = /*sy*/
      l[51]), i(I, "points", M = ve(
        /*x0*/
        l[46],
        /*y0*/
        l[47],
        /*x1*/
        l[48],
        /*y1*/
        l[49],
        /*hs*/
        l[54]
      )), i(I, "class", "svelte-1t2zk1p"), i(v, "cx", z = /*x0*/
      l[46]), i(v, "cy", y = /*y0*/
      l[47]), i(v, "r", g = /*sel*/
      l[53] ? 5.5 : 4.5), i(v, "class", "svelte-1t2zk1p"), i(h, "class", "hit svelte-1t2zk1p"), i(h, "x1", B = /*x0*/
      l[46]), i(h, "y1", X = /*y0*/
      l[47]), i(h, "x2", E = /*x1*/
      l[48]), i(h, "y2", ee = /*y1*/
      l[49]), i(h, "role", "button"), i(h, "tabindex", "-1"), i(h, "aria-label", "Arrow " + /*i*/
      (l[56] + 1)), i(e, "class", "arrow svelte-1t2zk1p"), $(
        e,
        "sel",
        /*sel*/
        l[53]
      );
    },
    m(U, w) {
      R(U, e, w), k(e, t), k(e, r), k(e, I), k(e, v), k(e, h), G || (ne = ue(h, "pointerdown", se), G = !0);
    },
    p(U, w) {
      l = U, w[0] & /*arrows, w*/
      4608 && n !== (n = /*x0*/
      l[46]) && i(t, "x1", n), w[0] & /*arrows, h*/
      5120 && o !== (o = /*y0*/
      l[47]) && i(t, "y1", o), w[0] & /*arrows, w, h, selected*/
      7680 && s !== (s = /*sx*/
      l[50]) && i(t, "x2", s), w[0] & /*arrows, w, h, selected*/
      7680 && _ !== (_ = /*sy*/
      l[51]) && i(t, "y2", _), w[0] & /*arrows, w*/
      4608 && c !== (c = /*x0*/
      l[46]) && i(r, "x1", c), w[0] & /*arrows, h*/
      5120 && f !== (f = /*y0*/
      l[47]) && i(r, "y1", f), w[0] & /*arrows, w, h, selected*/
      7680 && p !== (p = /*sx*/
      l[50]) && i(r, "x2", p), w[0] & /*arrows, w, h, selected*/
      7680 && C !== (C = /*sy*/
      l[51]) && i(r, "y2", C), w[0] & /*arrows, w, h, selected*/
      7680 && M !== (M = ve(
        /*x0*/
        l[46],
        /*y0*/
        l[47],
        /*x1*/
        l[48],
        /*y1*/
        l[49],
        /*hs*/
        l[54]
      )) && i(I, "points", M), w[0] & /*arrows, w*/
      4608 && z !== (z = /*x0*/
      l[46]) && i(v, "cx", z), w[0] & /*arrows, h*/
      5120 && y !== (y = /*y0*/
      l[47]) && i(v, "cy", y), w[0] & /*selected*/
      2048 && g !== (g = /*sel*/
      l[53] ? 5.5 : 4.5) && i(v, "r", g), w[0] & /*arrows, w*/
      4608 && B !== (B = /*x0*/
      l[46]) && i(h, "x1", B), w[0] & /*arrows, h*/
      5120 && X !== (X = /*y0*/
      l[47]) && i(h, "y1", X), w[0] & /*arrows, w*/
      4608 && E !== (E = /*x1*/
      l[48]) && i(h, "x2", E), w[0] & /*arrows, h*/
      5120 && ee !== (ee = /*y1*/
      l[49]) && i(h, "y2", ee), w[0] & /*selected*/
      2048 && $(
        e,
        "sel",
        /*sel*/
        l[53]
      );
    },
    d(U) {
      U && b(e), G = !1, ne();
    }
  };
}
function Ce(l) {
  let e, t, n, o, s, _, r, c, f, p, C, I = Math.hypot(
    /*x1*/
    l[48] - /*x0*/
    l[46],
    /*y1*/
    l[49] - /*y0*/
    l[47]
  ) > 6, M, v, z, y = I && Ie(l);
  return {
    c() {
      e = q("g"), t = q("line"), r = q("line"), y && y.c(), M = q("circle"), this.h();
    },
    l(g) {
      e = W(g, "g", { class: !0 });
      var h = A(e);
      t = W(h, "line", {
        class: !0,
        x1: !0,
        y1: !0,
        x2: !0,
        y2: !0
      }), A(t).forEach(b), r = W(h, "line", {
        class: !0,
        x1: !0,
        y1: !0,
        x2: !0,
        y2: !0
      }), A(r).forEach(b), y && y.l(h), M = W(h, "circle", { cx: !0, cy: !0, r: !0, class: !0 }), A(M).forEach(b), h.forEach(b), this.h();
    },
    h() {
      i(t, "class", "outline svelte-1t2zk1p"), i(t, "x1", n = /*x0*/
      l[46]), i(t, "y1", o = /*y0*/
      l[47]), i(t, "x2", s = /*sx*/
      l[50]), i(t, "y2", _ = /*sy*/
      l[51]), i(r, "class", "fill svelte-1t2zk1p"), i(r, "x1", c = /*x0*/
      l[46]), i(r, "y1", f = /*y0*/
      l[47]), i(r, "x2", p = /*sx*/
      l[50]), i(r, "y2", C = /*sy*/
      l[51]), i(M, "cx", v = /*x0*/
      l[46]), i(M, "cy", z = /*y0*/
      l[47]), i(M, "r", "4.5"), i(M, "class", "svelte-1t2zk1p"), i(e, "class", "arrow draft svelte-1t2zk1p");
    },
    m(g, h) {
      R(g, e, h), k(e, t), k(e, r), y && y.m(e, null), k(e, M);
    },
    p(g, h) {
      h[0] & /*draft, w*/
      524800 && n !== (n = /*x0*/
      g[46]) && i(t, "x1", n), h[0] & /*draft, h*/
      525312 && o !== (o = /*y0*/
      g[47]) && i(t, "y1", o), h[0] & /*draft, w, h*/
      525824 && s !== (s = /*sx*/
      g[50]) && i(t, "x2", s), h[0] & /*draft, w, h*/
      525824 && _ !== (_ = /*sy*/
      g[51]) && i(t, "y2", _), h[0] & /*draft, w*/
      524800 && c !== (c = /*x0*/
      g[46]) && i(r, "x1", c), h[0] & /*draft, h*/
      525312 && f !== (f = /*y0*/
      g[47]) && i(r, "y1", f), h[0] & /*draft, w, h*/
      525824 && p !== (p = /*sx*/
      g[50]) && i(r, "x2", p), h[0] & /*draft, w, h*/
      525824 && C !== (C = /*sy*/
      g[51]) && i(r, "y2", C), h[0] & /*draft, w, h*/
      525824 && (I = Math.hypot(
        /*x1*/
        g[48] - /*x0*/
        g[46],
        /*y1*/
        g[49] - /*y0*/
        g[47]
      ) > 6), I ? y ? y.p(g, h) : (y = Ie(g), y.c(), y.m(e, M)) : y && (y.d(1), y = null), h[0] & /*draft, w*/
      524800 && v !== (v = /*x0*/
      g[46]) && i(M, "cx", v), h[0] & /*draft, h*/
      525312 && z !== (z = /*y0*/
      g[47]) && i(M, "cy", z);
    },
    d(g) {
      g && b(e), y && y.d();
    }
  };
}
function Ie(l) {
  let e, t;
  return {
    c() {
      e = q("polygon"), this.h();
    },
    l(n) {
      e = W(n, "polygon", { points: !0, class: !0 }), A(e).forEach(b), this.h();
    },
    h() {
      i(e, "points", t = ve(
        /*x0*/
        l[46],
        /*y0*/
        l[47],
        /*x1*/
        l[48],
        /*y1*/
        l[49],
        14
      )), i(e, "class", "svelte-1t2zk1p");
    },
    m(n, o) {
      R(n, e, o);
    },
    p(n, o) {
      o[0] & /*draft, w, h*/
      525824 && t !== (t = ve(
        /*x0*/
        n[46],
        /*y0*/
        n[47],
        /*x1*/
        n[48],
        /*y1*/
        n[49],
        14
      )) && i(e, "points", t);
    },
    d(n) {
      n && b(e);
    }
  };
}
function Be(l) {
  let e, t, n, o, s = Math.round(
    /*amount*/
    l[13] * 100
  ) + "", _, r;
  return {
    c() {
      e = K("span"), t = Z("Camera: "), n = Z(
        /*camera*/
        l[14]
      ), o = Z(" · "), _ = Z(s), r = Z("%"), this.h();
    },
    l(c) {
      e = J(c, "SPAN", { class: !0 });
      var f = A(e);
      t = Q(f, "Camera: "), n = Q(
        f,
        /*camera*/
        l[14]
      ), o = Q(f, " · "), _ = Q(f, s), r = Q(f, "%"), f.forEach(b), this.h();
    },
    h() {
      i(e, "class", "chip svelte-1t2zk1p");
    },
    m(c, f) {
      R(c, e, f), k(e, t), k(e, n), k(e, o), k(e, _), k(e, r);
    },
    p(c, f) {
      f[0] & /*camera*/
      16384 && de(
        n,
        /*camera*/
        c[14]
      ), f[0] & /*amount*/
      8192 && s !== (s = Math.round(
        /*amount*/
        c[13] * 100
      ) + "") && de(_, s);
    },
    d(c) {
      c && b(e);
    }
  };
}
function Pe(l) {
  var n;
  let e, t = (
    /*value*/
    ((n = l[0]) == null ? void 0 : n.reason) && Se(l)
  );
  return {
    c() {
      e = K("div"), t && t.c(), this.h();
    },
    l(o) {
      e = J(o, "DIV", { class: !0 });
      var s = A(e);
      t && t.l(s), s.forEach(b), this.h();
    },
    h() {
      i(e, "class", "veil svelte-1t2zk1p");
    },
    m(o, s) {
      R(o, e, s), t && t.m(e, null);
    },
    p(o, s) {
      var _;
      /*value*/
      (_ = o[0]) != null && _.reason ? t ? t.p(o, s) : (t = Se(o), t.c(), t.m(e, null)) : t && (t.d(1), t = null);
    },
    d(o) {
      o && b(e), t && t.d();
    }
  };
}
function Se(l) {
  let e, t = (
    /*value*/
    l[0].reason + ""
  ), n;
  return {
    c() {
      e = K("span"), n = Z(t), this.h();
    },
    l(o) {
      e = J(o, "SPAN", { class: !0 });
      var s = A(e);
      n = Q(s, t), s.forEach(b), this.h();
    },
    h() {
      i(e, "class", "reason svelte-1t2zk1p");
    },
    m(o, s) {
      R(o, e, s), k(e, n);
    },
    p(o, s) {
      s[0] & /*value*/
      1 && t !== (t = /*value*/
      o[0].reason + "") && de(n, t);
    },
    d(o) {
      o && b(e);
    }
  };
}
function Ye(l) {
  let e;
  return {
    c() {
      e = Z("Drag on the frame to draw where things should move");
    },
    l(t) {
      e = Q(t, "Drag on the frame to draw where things should move");
    },
    m(t, n) {
      R(t, e, n);
    },
    d(t) {
      t && b(e);
    }
  };
}
function Fe(l) {
  let e;
  return {
    c() {
      e = Z("Arrow selected: press Delete to remove it");
    },
    l(t) {
      e = Q(t, "Arrow selected: press Delete to remove it");
    },
    m(t, n) {
      R(t, e, n);
    },
    d(t) {
      t && b(e);
    }
  };
}
function Te(l) {
  let e, t = (
    /*arrows*/
    l[12].length + ""
  ), n, o, s = (
    /*arrows*/
    l[12].length === 1 ? "arrow" : "arrows"
  ), _;
  return {
    c() {
      e = K("span"), n = Z(t), o = re(), _ = Z(s), this.h();
    },
    l(r) {
      e = J(r, "SPAN", { class: !0 });
      var c = A(e);
      n = Q(c, t), o = ae(c), _ = Q(c, s), c.forEach(b), this.h();
    },
    h() {
      i(e, "class", "count svelte-1t2zk1p");
    },
    m(r, c) {
      R(r, e, c), k(e, n), k(e, o), k(e, _);
    },
    p(r, c) {
      c[0] & /*arrows*/
      4096 && t !== (t = /*arrows*/
      r[12].length + "") && de(n, t), c[0] & /*arrows*/
      4096 && s !== (s = /*arrows*/
      r[12].length === 1 ? "arrow" : "arrows") && de(_, s);
    },
    d(r) {
      r && b(e);
    }
  };
}
function Je(l) {
  let e, t, n, o, s, _, r, c, f, p, C, I, M, v, z, y, g, h, B, X, E, ee, G, ne, se, U, w, he, H = (
    /*show_label*/
    l[5] && /*label*/
    l[4] && De(l)
  );
  function fe(a, m) {
    return (
      /*src*/
      a[16] ? Re : Ge
    );
  }
  let oe = fe(l), j = oe(l), Y = be(
    /*cam_vectors*/
    l[21]
  ), D = [];
  for (let a = 0; a < Y.length; a += 1)
    D[a] = Ne(Me(l, Y, a));
  let P = be(
    /*arrows*/
    l[12]
  ), T = [];
  for (let a = 0; a < P.length; a += 1)
    T[a] = Ae(Ee(l, P, a));
  let S = (
    /*draft*/
    l[19] && Ce(pe(l))
  ), V = (
    /*show_camera*/
    l[15] && Be(l)
  ), L = !/*enabled*/
  l[17] && Pe(l);
  function ge(a, m) {
    return (
      /*selected*/
      a[11] !== null ? Fe : Ye
    );
  }
  let ce = ge(l), le = ce(l), O = (
    /*arrows*/
    l[12].length && Te(l)
  );
  return {
    c() {
      e = K("div"), H && H.c(), t = re(), n = K("div"), j.c(), o = re(), s = q("svg");
      for (let a = 0; a < D.length; a += 1)
        D[a].c();
      _ = me();
      for (let a = 0; a < T.length; a += 1)
        T[a].c();
      r = me(), S && S.c(), f = re(), V && V.c(), p = re(), L && L.c(), M = re(), v = K("div"), z = K("button"), y = Z("Undo"), h = re(), B = K("button"), X = Z("Clear"), ee = re(), G = K("span"), le.c(), ne = re(), O && O.c(), this.h();
    },
    l(a) {
      e = J(a, "DIV", { id: !0, class: !0 });
      var m = A(e);
      H && H.l(m), t = ae(m), n = J(m, "DIV", {
        class: !0,
        style: !0,
        tabindex: !0,
        role: !0,
        "aria-label": !0
      });
      var d = A(n);
      j.l(d), o = ae(d), s = W(d, "svg", {
        width: !0,
        height: !0,
        viewBox: !0,
        class: !0
      });
      var x = A(s);
      for (let te = 0; te < D.length; te += 1)
        D[te].l(x);
      _ = me();
      for (let te = 0; te < T.length; te += 1)
        T[te].l(x);
      r = me(), S && S.l(x), x.forEach(b), f = ae(d), V && V.l(d), p = ae(d), L && L.l(d), d.forEach(b), M = ae(m), v = J(m, "DIV", { class: !0 });
      var ie = A(v);
      z = J(ie, "BUTTON", { type: !0, class: !0 });
      var u = A(z);
      y = Q(u, "Undo"), u.forEach(b), h = ae(ie), B = J(ie, "BUTTON", { type: !0, class: !0 });
      var N = A(B);
      X = Q(N, "Clear"), N.forEach(b), ee = ae(ie), G = J(ie, "SPAN", { class: !0 });
      var F = A(G);
      le.l(F), F.forEach(b), ne = ae(ie), O && O.l(ie), ie.forEach(b), m.forEach(b), this.h();
    },
    h() {
      i(
        s,
        "width",
        /*w*/
        l[9]
      ), i(
        s,
        "height",
        /*h*/
        l[10]
      ), i(s, "viewBox", c = "0 0 " + /*w*/
      (l[9] || 1) + " " + /*h*/
      (l[10] || 1)), i(s, "class", "svelte-1t2zk1p"), i(n, "class", "stage svelte-1t2zk1p"), _e(
        n,
        "aspect-ratio",
        /*ar*/
        l[22]
      ), _e(n, "width", "min(100%, " + He * /*ar*/
      l[22] + "px)"), i(n, "tabindex", C = /*editable*/
      l[20] ? 0 : -1), i(n, "role", "application"), i(n, "aria-label", "Motion canvas. Drag to draw an arrow; select an arrow and press Delete to remove it."), Le(() => (
        /*div0_elementresize_handler*/
        l[43].call(n)
      )), $(
        n,
        "editable",
        /*editable*/
        l[20]
      ), $(n, "disabled", !/*enabled*/
      l[17]), $(n, "empty", !/*src*/
      l[16]), i(z, "type", "button"), z.disabled = g = !/*editable*/
      l[20] || /*arrows*/
      l[12].length === 0, i(z, "class", "svelte-1t2zk1p"), i(B, "type", "button"), B.disabled = E = !/*editable*/
      l[20] || /*arrows*/
      l[12].length === 0, i(B, "class", "svelte-1t2zk1p"), i(G, "class", "hint svelte-1t2zk1p"), i(v, "class", "toolbar svelte-1t2zk1p"), i(e, "id", se = /*elem_id*/
      l[1] || null), i(e, "class", U = "fps-motion " + /*elem_classes*/
      l[2].join(" ") + " svelte-1t2zk1p"), $(e, "hidden", !/*visible*/
      l[3]), $(
        e,
        "boxed",
        /*container*/
        l[8]
      ), _e(
        e,
        "flex-grow",
        /*scale*/
        l[6]
      ), _e(
        e,
        "min-width",
        /*min_width*/
        l[7] ? `${/*min_width*/
        l[7]}px` : null
      );
    },
    m(a, m) {
      R(a, e, m), H && H.m(e, null), k(e, t), k(e, n), j.m(n, null), k(n, o), k(n, s);
      for (let d = 0; d < D.length; d += 1)
        D[d] && D[d].m(s, null);
      k(s, _);
      for (let d = 0; d < T.length; d += 1)
        T[d] && T[d].m(s, null);
      k(s, r), S && S.m(s, null), k(n, f), V && V.m(n, null), k(n, p), L && L.m(n, null), l[42](n), I = Ve(
        n,
        /*div0_elementresize_handler*/
        l[43].bind(n)
      ), k(e, M), k(e, v), k(v, z), k(z, y), k(v, h), k(v, B), k(B, X), k(v, ee), k(v, G), le.m(G, null), k(v, ne), O && O.m(v, null), w || (he = [
        ue(
          n,
          "pointerdown",
          /*on_down*/
          l[23]
        ),
        ue(
          n,
          "pointermove",
          /*on_move*/
          l[24]
        ),
        ue(
          n,
          "pointerup",
          /*on_up*/
          l[25]
        ),
        ue(
          n,
          "pointercancel",
          /*on_up*/
          l[25]
        ),
        ue(
          n,
          "keydown",
          /*on_key*/
          l[27]
        ),
        ue(
          z,
          "click",
          /*undo*/
          l[28]
        ),
        ue(
          B,
          "click",
          /*clear*/
          l[29]
        )
      ], w = !0);
    },
    p(a, m) {
      if (/*show_label*/
      a[5] && /*label*/
      a[4] ? H ? H.p(a, m) : (H = De(a), H.c(), H.m(e, t)) : H && (H.d(1), H = null), oe === (oe = fe(a)) && j ? j.p(a, m) : (j.d(1), j = oe(a), j && (j.c(), j.m(n, o))), m[0] & /*cam_vectors*/
      2097152) {
        Y = be(
          /*cam_vectors*/
          a[21]
        );
        let d;
        for (d = 0; d < Y.length; d += 1) {
          const x = Me(a, Y, d);
          D[d] ? D[d].p(x, m) : (D[d] = Ne(x), D[d].c(), D[d].m(s, _));
        }
        for (; d < D.length; d += 1)
          D[d].d(1);
        D.length = Y.length;
      }
      if (m[0] & /*selected, arrows, w, h, pick*/
      67116544) {
        P = be(
          /*arrows*/
          a[12]
        );
        let d;
        for (d = 0; d < P.length; d += 1) {
          const x = Ee(a, P, d);
          T[d] ? T[d].p(x, m) : (T[d] = Ae(x), T[d].c(), T[d].m(s, r));
        }
        for (; d < T.length; d += 1)
          T[d].d(1);
        T.length = P.length;
      }
      /*draft*/
      a[19] ? S ? S.p(pe(a), m) : (S = Ce(pe(a)), S.c(), S.m(s, null)) : S && (S.d(1), S = null), m[0] & /*w*/
      512 && i(
        s,
        "width",
        /*w*/
        a[9]
      ), m[0] & /*h*/
      1024 && i(
        s,
        "height",
        /*h*/
        a[10]
      ), m[0] & /*w, h*/
      1536 && c !== (c = "0 0 " + /*w*/
      (a[9] || 1) + " " + /*h*/
      (a[10] || 1)) && i(s, "viewBox", c), /*show_camera*/
      a[15] ? V ? V.p(a, m) : (V = Be(a), V.c(), V.m(n, p)) : V && (V.d(1), V = null), /*enabled*/
      a[17] ? L && (L.d(1), L = null) : L ? L.p(a, m) : (L = Pe(a), L.c(), L.m(n, null)), m[0] & /*ar*/
      4194304 && _e(
        n,
        "aspect-ratio",
        /*ar*/
        a[22]
      ), m[0] & /*ar*/
      4194304 && _e(n, "width", "min(100%, " + He * /*ar*/
      a[22] + "px)"), m[0] & /*editable*/
      1048576 && C !== (C = /*editable*/
      a[20] ? 0 : -1) && i(n, "tabindex", C), m[0] & /*editable*/
      1048576 && $(
        n,
        "editable",
        /*editable*/
        a[20]
      ), m[0] & /*enabled*/
      131072 && $(n, "disabled", !/*enabled*/
      a[17]), m[0] & /*src*/
      65536 && $(n, "empty", !/*src*/
      a[16]), m[0] & /*editable, arrows*/
      1052672 && g !== (g = !/*editable*/
      a[20] || /*arrows*/
      a[12].length === 0) && (z.disabled = g), m[0] & /*editable, arrows*/
      1052672 && E !== (E = !/*editable*/
      a[20] || /*arrows*/
      a[12].length === 0) && (B.disabled = E), ce !== (ce = ge(a)) && (le.d(1), le = ce(a), le && (le.c(), le.m(G, null))), /*arrows*/
      a[12].length ? O ? O.p(a, m) : (O = Te(a), O.c(), O.m(v, null)) : O && (O.d(1), O = null), m[0] & /*elem_id*/
      2 && se !== (se = /*elem_id*/
      a[1] || null) && i(e, "id", se), m[0] & /*elem_classes*/
      4 && U !== (U = "fps-motion " + /*elem_classes*/
      a[2].join(" ") + " svelte-1t2zk1p") && i(e, "class", U), m[0] & /*elem_classes, visible*/
      12 && $(e, "hidden", !/*visible*/
      a[3]), m[0] & /*elem_classes, container*/
      260 && $(
        e,
        "boxed",
        /*container*/
        a[8]
      ), m[0] & /*scale*/
      64 && _e(
        e,
        "flex-grow",
        /*scale*/
        a[6]
      ), m[0] & /*min_width*/
      128 && _e(
        e,
        "min-width",
        /*min_width*/
        a[7] ? `${/*min_width*/
        a[7]}px` : null
      );
    },
    i: ke,
    o: ke,
    d(a) {
      a && b(e), H && H.d(), j.d(), we(D, a), we(T, a), S && S.d(), V && V.d(), L && L.d(), l[42](null), I(), le.d(), O && O.d(), w = !1, qe(he);
    }
  };
}
const He = 360, Ke = 0.02;
function Qe(l, e, t, n) {
  if (!t || !n) return [];
  const o = l.toLowerCase(), s = 7, _ = Math.max(3, Math.round(s * n / t)), r = Math.min(t / s, n / _), c = r * (0.25 + 0.55 * e), f = [];
  for (let p = 0; p < _; p++)
    for (let C = 0; C < s; C++) {
      const I = (C + 0.5) / s * t, M = (p + 0.5) / _ * n;
      let v = 0, z = 0;
      if (o.includes("zoom")) {
        const y = I - t / 2, g = M - n / 2, h = Math.hypot(y, g);
        if (h < r * 0.6) continue;
        const B = c * (0.4 + 0.6 * h / Math.hypot(t / 2, n / 2)) / h, X = o.includes("out") ? -1 : 1;
        v = X * y * B, z = X * g * B;
      } else if (o.includes("left")) v = -c;
      else if (o.includes("right")) v = c;
      else if (o.includes("up")) z = -c;
      else if (o.includes("down")) z = c;
      else continue;
      f.push([I - v / 2, M - z / 2, I + v / 2, M + z / 2]);
    }
  return f;
}
function ve(l, e, t, n, o) {
  const s = Math.atan2(n - e, t - l), _ = (r) => `${t - o * Math.cos(s + r)},${n - o * Math.sin(s + r)}`;
  return `${t},${n} ${_(0.45)} ${_(-0.45)}`;
}
function ye(l, e, t, n, o) {
  const s = Math.hypot(t - l, n - e) || 1, _ = Math.max(0, s - o) / s;
  return [l + (t - l) * _, e + (n - e) * _];
}
function Ze(l, e, t) {
  let n, o, s, _, r, c, f, p, C, I;
  var M, v, z, y;
  let { gradio: g } = e, { elem_id: h = "" } = e, { elem_classes: B = [] } = e, { visible: X = !0 } = e, { value: E = null } = e, { label: ee = "" } = e, { show_label: G = !0 } = e, { interactive: ne = !0 } = e, { loading_status: se = void 0 } = e, { scale: U = null } = e, { min_width: w = void 0 } = e, { root: he = "" } = e, { container: H = !0 } = e, fe = 0, oe = 0, j, Y = null, D = null, P = null;
  function T(u) {
    const N = j.getBoundingClientRect(), F = (te) => Math.min(1, Math.max(0, te));
    return [F((u.clientX - N.left) / N.width), F((u.clientY - N.top) / N.height)];
  }
  function S(u) {
    t(0, E = Object.assign(Object.assign({}, E ?? { background: null, arrows: [] }), { arrows: u })), g.dispatch("change"), g.dispatch("input");
  }
  function V(u) {
    if (!s || u.button !== 0) return;
    j.focus(), j.setPointerCapture(u.pointerId);
    const [N, F] = T(u);
    t(19, D = [N, F, N, F]), u.preventDefault();
  }
  function L(u) {
    if (!D) return;
    const [N, F] = T(u);
    t(19, D = [D[0], D[1], N, F]);
  }
  function ge() {
    if (!D) return;
    const u = D;
    if (t(19, D = null), Math.hypot(u[2] - u[0], u[3] - u[1]) < Ke) {
      t(11, P = null);
      return;
    }
    const N = (F) => Math.round(F * 1e3) / 1e3;
    S([...n, u.map(N)]), t(11, P = null);
  }
  function ce(u, N) {
    s && (u.stopPropagation(), u.preventDefault(), j.focus(), t(11, P = P === N ? null : N));
  }
  function le(u) {
    if (s)
      if ((u.key === "Delete" || u.key === "Backspace") && P !== null) {
        u.preventDefault();
        const N = P;
        t(11, P = null), S(n.filter((F, te) => te !== N));
      } else u.key === "Escape" && t(11, P = null);
  }
  function O() {
    t(11, P = null), S(n.slice(0, -1));
  }
  function a() {
    t(11, P = null), S([]);
  }
  function m(u) {
    const N = u.currentTarget;
    N.naturalWidth && N.naturalHeight && t(39, Y = {
      w: N.naturalWidth,
      h: N.naturalHeight
    });
  }
  const d = (u, N) => ce(N, u);
  function x(u) {
    Oe[u ? "unshift" : "push"](() => {
      j = u, t(18, j);
    });
  }
  function ie() {
    fe = this.clientWidth, oe = this.clientHeight, t(9, fe), t(10, oe);
  }
  return l.$$set = (u) => {
    "gradio" in u && t(31, g = u.gradio), "elem_id" in u && t(1, h = u.elem_id), "elem_classes" in u && t(2, B = u.elem_classes), "visible" in u && t(3, X = u.visible), "value" in u && t(0, E = u.value), "label" in u && t(4, ee = u.label), "show_label" in u && t(5, G = u.show_label), "interactive" in u && t(32, ne = u.interactive), "loading_status" in u && t(33, se = u.loading_status), "scale" in u && t(6, U = u.scale), "min_width" in u && t(7, w = u.min_width), "root" in u && t(34, he = u.root), "container" in u && t(8, H = u.container);
  }, l.$$.update = () => {
    l.$$.dirty[0] & /*value*/
    1 | l.$$.dirty[1] & /*_a*/
    16 && t(12, n = t(35, M = E == null ? void 0 : E.arrows) !== null && M !== void 0 ? M : []), l.$$.dirty[0] & /*value*/
    1 && t(17, o = (E == null ? void 0 : E.enabled) !== !1), l.$$.dirty[0] & /*enabled*/
    131072 | l.$$.dirty[1] & /*interactive*/
    2 && t(20, s = ne !== !1 && o), l.$$.dirty[0] & /*value*/
    1 | l.$$.dirty[1] & /*_b*/
    32 && t(40, _ = t(36, v = E == null ? void 0 : E.background) !== null && v !== void 0 ? v : null), l.$$.dirty[1] & /*bg, root*/
    520 && t(16, r = _ ? _.url || `${he}/gradio_api/file=${_.path}` : null), l.$$.dirty[0] & /*src*/
    65536 && (r || t(39, Y = null)), l.$$.dirty[1] & /*natural*/
    256 && t(22, c = Y ? Y.w / Y.h : 16 / 9), l.$$.dirty[0] & /*value*/
    1 | l.$$.dirty[1] & /*_c*/
    64 && t(14, f = t(37, z = E == null ? void 0 : E.camera) !== null && z !== void 0 ? z : "None"), l.$$.dirty[0] & /*value*/
    1 | l.$$.dirty[1] & /*_d*/
    128 && t(13, p = Math.max(0, Math.min(1, t(38, y = E == null ? void 0 : E.camera_amount) !== null && y !== void 0 ? y : 0))), l.$$.dirty[0] & /*camera, amount*/
    24576 && t(15, C = f && f !== "None" && p > 0), l.$$.dirty[0] & /*show_camera, camera, amount, w, h*/
    58880 && t(21, I = C ? Qe(f, p, fe, oe) : []), l.$$.dirty[0] & /*selected, arrows*/
    6144 && P !== null && P >= n.length && t(11, P = null);
  }, [
    E,
    h,
    B,
    X,
    ee,
    G,
    U,
    w,
    H,
    fe,
    oe,
    P,
    n,
    p,
    f,
    C,
    r,
    o,
    j,
    D,
    s,
    I,
    c,
    V,
    L,
    ge,
    ce,
    le,
    O,
    a,
    m,
    g,
    ne,
    se,
    he,
    M,
    v,
    z,
    y,
    Y,
    _,
    d,
    x,
    ie
  ];
}
class xe extends je {
  constructor(e) {
    super(), We(
      this,
      e,
      Ze,
      Je,
      Xe,
      {
        gradio: 31,
        elem_id: 1,
        elem_classes: 2,
        visible: 3,
        value: 0,
        label: 4,
        show_label: 5,
        interactive: 32,
        loading_status: 33,
        scale: 6,
        min_width: 7,
        root: 34,
        container: 8
      },
      null,
      [-1, -1]
    );
  }
}
export {
  xe as default
};
