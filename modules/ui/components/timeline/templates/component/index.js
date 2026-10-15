const {
  SvelteComponent: ll,
  add_iframe_resize_listener: tl,
  add_render_callback: nl,
  append_hydration: k,
  attr: d,
  binding_callbacks: sl,
  children: I,
  claim_element: E,
  claim_space: S,
  claim_text: x,
  destroy_each: ke,
  detach: h,
  element: y,
  empty: Ne,
  ensure_array_like: ne,
  get_svelte_dataset: ye,
  init: il,
  insert_hydration: V,
  listen: we,
  noop: Ie,
  run_all: al,
  safe_not_equal: ol,
  set_data: ie,
  set_style: Z,
  space: A,
  text: ee,
  toggle_class: K
} = window.__gradio__svelte__internal, { onMount: fl } = window.__gradio__svelte__internal;
function Se(e, l, n) {
  const t = e.slice();
  return t[52] = l[n], t;
}
function Ae(e, l, n) {
  const t = e.slice();
  t[55] = l[n], t[59] = n;
  const s = (
    /*drag*/
    t[14] && /*drag*/
    t[14].i === /*i*/
    t[59] ? (
      /*drag*/
      t[14].t
    ) : (
      /*f*/
      t[55].t
    )
  );
  t[56] = s;
  const i = (
    /*editable*/
    t[17] && /*f*/
    t[55].kind === "key"
  );
  return t[57] = i, t;
}
function Pe(e, l, n) {
  const t = e.slice();
  return t[60] = l[n], t[59] = n, t;
}
function je(e, l, n) {
  const t = e.slice();
  return t[60] = l[n], t[59] = n, t;
}
function Oe(e, l, n) {
  const t = e.slice();
  t[63] = l[n], t[59] = n;
  const s = (
    /*cell_state*/
    t[27](
      /*s*/
      t[63],
      /*i*/
      t[59]
    )
  );
  t[64] = s;
  const i = (
    /*s*/
    (t[63].end - /*s*/
    t[63].start) / /*duration*/
    t[11] * /*track_width*/
    t[9]
  );
  return t[65] = i, t;
}
function Te(e, l, n) {
  const t = e.slice();
  return t[67] = l[n], t;
}
function Be(e) {
  let l, n, t = (
    /*show_label*/
    e[5] && /*label*/
    e[4] && Fe(e)
  ), s = (
    /*duration*/
    e[11] && /*caption*/
    e[19] && ze(e)
  );
  return {
    c() {
      l = y("div"), t && t.c(), n = A(), s && s.c(), this.h();
    },
    l(i) {
      l = E(i, "DIV", { class: !0 });
      var a = I(l);
      t && t.l(a), n = S(a), s && s.l(a), a.forEach(h), this.h();
    },
    h() {
      d(l, "class", "head svelte-10gs4o2");
    },
    m(i, a) {
      V(i, l, a), t && t.m(l, null), k(l, n), s && s.m(l, null);
    },
    p(i, a) {
      /*show_label*/
      i[5] && /*label*/
      i[4] ? t ? t.p(i, a) : (t = Fe(i), t.c(), t.m(l, n)) : t && (t.d(1), t = null), /*duration*/
      i[11] && /*caption*/
      i[19] ? s ? s.p(i, a) : (s = ze(i), s.c(), s.m(l, null)) : s && (s.d(1), s = null);
    },
    d(i) {
      i && h(l), t && t.d(), s && s.d();
    }
  };
}
function Fe(e) {
  let l, n;
  return {
    c() {
      l = y("span"), n = ee(
        /*label*/
        e[4]
      ), this.h();
    },
    l(t) {
      l = E(t, "SPAN", { class: !0 });
      var s = I(l);
      n = x(
        s,
        /*label*/
        e[4]
      ), s.forEach(h), this.h();
    },
    h() {
      d(l, "class", "block-label svelte-10gs4o2");
    },
    m(t, s) {
      V(t, l, s), k(l, n);
    },
    p(t, s) {
      s[0] & /*label*/
      16 && ie(
        n,
        /*label*/
        t[4]
      );
    },
    d(t) {
      t && h(l);
    }
  };
}
function ze(e) {
  let l, n;
  return {
    c() {
      l = y("span"), n = ee(
        /*caption*/
        e[19]
      ), this.h();
    },
    l(t) {
      l = E(t, "SPAN", { class: !0 });
      var s = I(l);
      n = x(
        s,
        /*caption*/
        e[19]
      ), s.forEach(h), this.h();
    },
    h() {
      d(l, "class", "caption svelte-10gs4o2");
    },
    m(t, s) {
      V(t, l, s), k(l, n);
    },
    p(t, s) {
      s[0] & /*caption*/
      524288 && ie(
        n,
        /*caption*/
        t[19]
      );
    },
    d(t) {
      t && h(l);
    }
  };
}
function rl(e) {
  let l, n, t, s, i, a, f, v = "Sections", m, c, W, P, D, j = "Prompt", b, w, X, N, $, de, M, u = "Frames", oe, G, fe, me, ve, ge, be, re = ne(
    /*ticks*/
    e[18]
  ), O = [];
  for (let r = 0; r < re.length; r += 1)
    O[r] = Le(Te(e, re, r));
  let se = ne(
    /*sections*/
    e[10]
  ), C = [];
  for (let r = 0; r < se.length; r += 1)
    C[r] = Ke(Oe(e, se, r));
  let R = (
    /*playhead*/
    e[15] != null && Re(e)
  ), H = (
    /*prompts*/
    e[22].length === 0 && Ue()
  ), ue = ne(
    /*prompts*/
    e[22]
  ), z = [];
  for (let r = 0; r < ue.length; r += 1)
    z[r] = We(je(e, ue, r));
  let T = (
    /*blend*/
    e[20] > 0 && Xe(e)
  ), J = (
    /*playhead*/
    e[15] != null && He(e)
  ), Q = (
    /*playhead*/
    e[15] != null && Je(e)
  ), he = ne(
    /*frames*/
    e[16]
  ), L = [];
  for (let r = 0; r < he.length; r += 1)
    L[r] = Ye(Ae(e, he, r));
  let Y = !/*keys_enabled*/
  e[12] && /*value*/
  e[0].keyframes_reason && Ze(e), _e = ne(
    /*lanes*/
    e[21]
  ), U = [];
  for (let r = 0; r < _e.length; r += 1)
    U[r] = $e(Se(e, _e, r));
  return {
    c() {
      l = y("div"), n = y("div"), t = A(), s = y("div");
      for (let r = 0; r < O.length; r += 1)
        O[r].c();
      a = A(), f = y("div"), f.textContent = v, m = A(), c = y("div");
      for (let r = 0; r < C.length; r += 1)
        C[r].c();
      W = A(), R && R.c(), P = A(), D = y("div"), D.textContent = j, b = A(), w = y("div"), H && H.c(), X = A();
      for (let r = 0; r < z.length; r += 1)
        z[r].c();
      N = A(), T && T.c(), $ = A(), J && J.c(), de = A(), M = y("div"), M.textContent = u, oe = A(), G = y("div"), fe = y("div"), me = A(), Q && Q.c(), ve = A();
      for (let r = 0; r < L.length; r += 1)
        L[r].c();
      ge = A(), Y && Y.c(), be = A();
      for (let r = 0; r < U.length; r += 1)
        U[r].c();
      this.h();
    },
    l(r) {
      l = E(r, "DIV", { class: !0 });
      var g = I(l);
      n = E(g, "DIV", { class: !0 }), I(n).forEach(h), t = S(g), s = E(g, "DIV", { class: !0 });
      var o = I(s);
      for (let F = 0; F < O.length; F += 1)
        O[F].l(o);
      o.forEach(h), a = S(g), f = E(g, "DIV", { class: !0, "data-svelte-h": !0 }), ye(f) !== "svelte-1e5iyc6" && (f.textContent = v), m = S(g), c = E(g, "DIV", { class: !0 });
      var B = I(c);
      for (let F = 0; F < C.length; F += 1)
        C[F].l(B);
      W = S(B), R && R.l(B), B.forEach(h), P = S(g), D = E(g, "DIV", { class: !0, "data-svelte-h": !0 }), ye(D) !== "svelte-lym768" && (D.textContent = j), b = S(g), w = E(g, "DIV", { class: !0 });
      var ae = I(w);
      H && H.l(ae), X = S(ae);
      for (let F = 0; F < z.length; F += 1)
        z[F].l(ae);
      N = S(ae), T && T.l(ae), $ = S(ae), J && J.l(ae), ae.forEach(h), de = S(g), M = E(g, "DIV", { class: !0, "data-svelte-h": !0 }), ye(M) !== "svelte-144t6rb" && (M.textContent = u), oe = S(g), G = E(g, "DIV", { class: !0 });
      var ce = I(G);
      fe = E(ce, "DIV", { class: !0 }), I(fe).forEach(h), me = S(ce), Q && Q.l(ce), ve = S(ce);
      for (let F = 0; F < L.length; F += 1)
        L[F].l(ce);
      ce.forEach(h), ge = S(g), Y && Y.l(g), be = S(g);
      for (let F = 0; F < U.length; F += 1)
        U[F].l(g);
      g.forEach(h), this.h();
    },
    h() {
      d(n, "class", "lane-label svelte-10gs4o2"), d(s, "class", "track ruler svelte-10gs4o2"), nl(() => (
        /*div1_elementresize_handler*/
        e[43].call(s)
      )), d(f, "class", "lane-label svelte-10gs4o2"), d(c, "class", "track sections svelte-10gs4o2"), d(D, "class", "lane-label svelte-10gs4o2"), d(w, "class", "track prompts svelte-10gs4o2"), d(M, "class", "lane-label top svelte-10gs4o2"), d(fe, "class", "axis svelte-10gs4o2"), d(G, "class", "track frames svelte-10gs4o2"), K(G, "disabled", !/*keys_enabled*/
      e[12]), d(l, "class", "grid svelte-10gs4o2");
    },
    m(r, g) {
      V(r, l, g), k(l, n), k(l, t), k(l, s);
      for (let o = 0; o < O.length; o += 1)
        O[o] && O[o].m(s, null);
      i = tl(
        s,
        /*div1_elementresize_handler*/
        e[43].bind(s)
      ), k(l, a), k(l, f), k(l, m), k(l, c);
      for (let o = 0; o < C.length; o += 1)
        C[o] && C[o].m(c, null);
      k(c, W), R && R.m(c, null), k(l, P), k(l, D), k(l, b), k(l, w), H && H.m(w, null), k(w, X);
      for (let o = 0; o < z.length; o += 1)
        z[o] && z[o].m(w, null);
      k(w, N), T && T.m(w, null), k(w, $), J && J.m(w, null), k(l, de), k(l, M), k(l, oe), k(l, G), k(G, fe), k(G, me), Q && Q.m(G, null), k(G, ve);
      for (let o = 0; o < L.length; o += 1)
        L[o] && L[o].m(G, null);
      e[47](G), k(l, ge), Y && Y.m(l, null), k(l, be);
      for (let o = 0; o < U.length; o += 1)
        U[o] && U[o].m(l, null);
    },
    p(r, g) {
      if (g[0] & /*ticks, pct, fmt*/
      42205184) {
        re = ne(
          /*ticks*/
          r[18]
        );
        let o;
        for (o = 0; o < re.length; o += 1) {
          const B = Te(r, re, o);
          O[o] ? O[o].p(B, g) : (O[o] = Le(B), O[o].c(), O[o].m(s, null));
        }
        for (; o < O.length; o += 1)
          O[o].d(1);
        O.length = re.length;
      }
      if (g[0] & /*cell_state, sections, span, value, fmt, duration, track_width*/
      184552961 | g[1] & /*select_section*/
      2) {
        se = ne(
          /*sections*/
          r[10]
        );
        let o;
        for (o = 0; o < se.length; o += 1) {
          const B = Oe(r, se, o);
          C[o] ? C[o].p(B, g) : (C[o] = Ke(B), C[o].c(), C[o].m(c, W));
        }
        for (; o < C.length; o += 1)
          C[o].d(1);
        C.length = se.length;
      }
      if (/*playhead*/
      r[15] != null ? R ? R.p(r, g) : (R = Re(r), R.c(), R.m(c, null)) : R && (R.d(1), R = null), /*prompts*/
      r[22].length === 0 ? H || (H = Ue(), H.c(), H.m(w, X)) : H && (H.d(1), H = null), g[0] & /*span, prompts*/
      20971520) {
        ue = ne(
          /*prompts*/
          r[22]
        );
        let o;
        for (o = 0; o < ue.length; o += 1) {
          const B = je(r, ue, o);
          z[o] ? z[o].p(B, g) : (z[o] = We(B), z[o].c(), z[o].m(w, N));
        }
        for (; o < z.length; o += 1)
          z[o].d(1);
        z.length = ue.length;
      }
      if (/*blend*/
      r[20] > 0 ? T ? T.p(r, g) : (T = Xe(r), T.c(), T.m(w, $)) : T && (T.d(1), T = null), /*playhead*/
      r[15] != null ? J ? J.p(r, g) : (J = He(r), J.c(), J.m(w, null)) : J && (J.d(1), J = null), /*playhead*/
      r[15] != null ? Q ? Q.p(r, g) : (Q = Je(r), Q.c(), Q.m(G, ve)) : Q && (Q.d(1), Q = null), g[0] & /*frames, fmt, editable, drag, pct, on_down, on_move, on_up, anchor, span*/
      2005090304 | g[1] & /*frame_label, on_key*/
      5) {
        he = ne(
          /*frames*/
          r[16]
        );
        let o;
        for (o = 0; o < he.length; o += 1) {
          const B = Ae(r, he, o);
          L[o] ? L[o].p(B, g) : (L[o] = Ye(B), L[o].c(), L[o].m(G, null));
        }
        for (; o < L.length; o += 1)
          L[o].d(1);
        L.length = he.length;
      }
      if (g[0] & /*keys_enabled*/
      4096 && K(G, "disabled", !/*keys_enabled*/
      r[12]), !/*keys_enabled*/
      r[12] && /*value*/
      r[0].keyframes_reason ? Y ? Y.p(r, g) : (Y = Ze(r), Y.c(), Y.m(l, be)) : Y && (Y.d(1), Y = null), g[0] & /*span, lanes*/
      18874368) {
        _e = ne(
          /*lanes*/
          r[21]
        );
        let o;
        for (o = 0; o < _e.length; o += 1) {
          const B = Se(r, _e, o);
          U[o] ? U[o].p(B, g) : (U[o] = $e(B), U[o].c(), U[o].m(l, null));
        }
        for (; o < U.length; o += 1)
          U[o].d(1);
        U.length = _e.length;
      }
    },
    d(r) {
      r && h(l), ke(O, r), i(), ke(C, r), R && R.d(), H && H.d(), ke(z, r), T && T.d(), J && J.d(), Q && Q.d(), ke(L, r), e[47](null), Y && Y.d(), ke(U, r);
    }
  };
}
function _l(e) {
  let l, n = "Timeline appears once a length is set";
  return {
    c() {
      l = y("div"), l.textContent = n, this.h();
    },
    l(t) {
      l = E(t, "DIV", { class: !0, "data-svelte-h": !0 }), ye(l) !== "svelte-16hw8yd" && (l.textContent = n), this.h();
    },
    h() {
      d(l, "class", "placeholder svelte-10gs4o2");
    },
    m(t, s) {
      V(t, l, s);
    },
    p: Ie,
    d(t) {
      t && h(l);
    }
  };
}
function Le(e) {
  let l, n = (
    /*fmt*/
    e[25](
      /*tk*/
      e[67].t
    ) + ""
  ), t, s, i;
  return {
    c() {
      l = y("span"), t = ee(n), s = ee("s"), this.h();
    },
    l(a) {
      l = E(a, "SPAN", { class: !0 });
      var f = I(l);
      t = x(f, n), s = x(f, "s"), f.forEach(h), this.h();
    },
    h() {
      d(l, "class", i = "tick " + /*tk*/
      e[67].anchor + " svelte-10gs4o2"), Z(
        l,
        "left",
        /*pct*/
        e[23](
          /*tk*/
          e[67].t
        )
      );
    },
    m(a, f) {
      V(a, l, f), k(l, t), k(l, s);
    },
    p(a, f) {
      f[0] & /*ticks*/
      262144 && n !== (n = /*fmt*/
      a[25](
        /*tk*/
        a[67].t
      ) + "") && ie(t, n), f[0] & /*ticks*/
      262144 && i !== (i = "tick " + /*tk*/
      a[67].anchor + " svelte-10gs4o2") && d(l, "class", i), f[0] & /*ticks*/
      262144 && Z(
        l,
        "left",
        /*pct*/
        a[23](
          /*tk*/
          a[67].t
        )
      );
    },
    d(a) {
      a && h(l);
    }
  };
}
function qe(e) {
  let l, n = (
    /*s*/
    e[63].order + ""
  ), t;
  return {
    c() {
      l = y("span"), t = ee(n), this.h();
    },
    l(s) {
      l = E(s, "SPAN", { class: !0 });
      var i = I(l);
      t = x(i, n), i.forEach(h), this.h();
    },
    h() {
      d(l, "class", "order svelte-10gs4o2");
    },
    m(s, i) {
      V(s, l, i), k(l, t);
    },
    p(s, i) {
      i[0] & /*sections*/
      1024 && n !== (n = /*s*/
      s[63].order + "") && ie(t, n);
    },
    d(s) {
      s && h(l);
    }
  };
}
function Ke(e) {
  let l, n, t, s, i, a, f, v, m, c = (
    /*s*/
    e[63].order != null && /*w*/
    e[65] >= 16 && qe(e)
  );
  function W() {
    return (
      /*click_handler*/
      e[44](
        /*i*/
        e[59]
      )
    );
  }
  return {
    c() {
      l = y("button"), c && c.c(), this.h();
    },
    l(P) {
      l = E(P, "BUTTON", {
        type: !0,
        class: !0,
        style: !0,
        tabindex: !0,
        "aria-disabled": !0,
        title: !0,
        "aria-label": !0
      });
      var D = I(l);
      c && c.l(D), D.forEach(h), this.h();
    },
    h() {
      d(l, "type", "button"), d(l, "class", n = "cell " + /*st*/
      e[64] + " svelte-10gs4o2"), d(l, "style", t = /*span*/
      e[24](
        /*s*/
        e[63].start,
        /*s*/
        e[63].end
      )), d(l, "tabindex", s = /*value*/
      e[0].selectable ? 0 : -1), d(l, "aria-disabled", i = !/*value*/
      e[0].selectable), d(l, "title", a = `${/*fmt*/
      e[25](
        /*s*/
        e[63].start
      )}–${/*fmt*/
      e[25](
        /*s*/
        e[63].end
      )} s${/*s*/
      e[63].order != null ? `, generated #${/*s*/
      e[63].order}` : ""}${/*st*/
      e[64] !== "normal" ? ` (${/*st*/
      e[64]})` : ""}`), d(l, "aria-label", f = `Section ${/*i*/
      e[59] + 1}, ${/*fmt*/
      e[25](
        /*s*/
        e[63].start
      )} to ${/*fmt*/
      e[25](
        /*s*/
        e[63].end
      )} seconds`), K(
        l,
        "alt",
        /*i*/
        e[59] % 2 === 1
      ), K(
        l,
        "clickable",
        /*value*/
        e[0].selectable
      );
    },
    m(P, D) {
      V(P, l, D), c && c.m(l, null), v || (m = we(l, "click", W), v = !0);
    },
    p(P, D) {
      e = P, /*s*/
      e[63].order != null && /*w*/
      e[65] >= 16 ? c ? c.p(e, D) : (c = qe(e), c.c(), c.m(l, null)) : c && (c.d(1), c = null), D[0] & /*sections*/
      1024 && n !== (n = "cell " + /*st*/
      e[64] + " svelte-10gs4o2") && d(l, "class", n), D[0] & /*sections*/
      1024 && t !== (t = /*span*/
      e[24](
        /*s*/
        e[63].start,
        /*s*/
        e[63].end
      )) && d(l, "style", t), D[0] & /*value*/
      1 && s !== (s = /*value*/
      e[0].selectable ? 0 : -1) && d(l, "tabindex", s), D[0] & /*value*/
      1 && i !== (i = !/*value*/
      e[0].selectable) && d(l, "aria-disabled", i), D[0] & /*sections*/
      1024 && a !== (a = `${/*fmt*/
      e[25](
        /*s*/
        e[63].start
      )}–${/*fmt*/
      e[25](
        /*s*/
        e[63].end
      )} s${/*s*/
      e[63].order != null ? `, generated #${/*s*/
      e[63].order}` : ""}${/*st*/
      e[64] !== "normal" ? ` (${/*st*/
      e[64]})` : ""}`) && d(l, "title", a), D[0] & /*sections*/
      1024 && f !== (f = `Section ${/*i*/
      e[59] + 1}, ${/*fmt*/
      e[25](
        /*s*/
        e[63].start
      )} to ${/*fmt*/
      e[25](
        /*s*/
        e[63].end
      )} seconds`) && d(l, "aria-label", f), D[0] & /*sections*/
      1024 && K(
        l,
        "alt",
        /*i*/
        e[59] % 2 === 1
      ), D[0] & /*sections, value*/
      1025 && K(
        l,
        "clickable",
        /*value*/
        e[0].selectable
      );
    },
    d(P) {
      P && h(l), c && c.d(), v = !1, m();
    }
  };
}
function Re(e) {
  let l;
  return {
    c() {
      l = y("div"), this.h();
    },
    l(n) {
      l = E(n, "DIV", { class: !0 }), I(l).forEach(h), this.h();
    },
    h() {
      d(l, "class", "playhead svelte-10gs4o2"), Z(
        l,
        "left",
        /*pct*/
        e[23](
          /*playhead*/
          e[15]
        )
      );
    },
    m(n, t) {
      V(n, l, t);
    },
    p(n, t) {
      t[0] & /*playhead*/
      32768 && Z(
        l,
        "left",
        /*pct*/
        n[23](
          /*playhead*/
          n[15]
        )
      );
    },
    d(n) {
      n && h(l);
    }
  };
}
function Ue(e) {
  let l, n = "No prompt";
  return {
    c() {
      l = y("span"), l.textContent = n, this.h();
    },
    l(t) {
      l = E(t, "SPAN", { class: !0, "data-svelte-h": !0 }), ye(l) !== "svelte-e7elkq" && (l.textContent = n), this.h();
    },
    h() {
      d(l, "class", "empty-note svelte-10gs4o2");
    },
    m(t, s) {
      V(t, l, s);
    },
    d(t) {
      t && h(l);
    }
  };
}
function We(e) {
  let l, n, t = (
    /*p*/
    e[60].text + ""
  ), s, i, a;
  return {
    c() {
      l = y("div"), n = y("span"), s = ee(t), this.h();
    },
    l(f) {
      l = E(f, "DIV", { class: !0, style: !0, title: !0 });
      var v = I(l);
      n = E(v, "SPAN", { class: !0 });
      var m = I(n);
      s = x(m, t), m.forEach(h), v.forEach(h), this.h();
    },
    h() {
      d(n, "class", "txt svelte-10gs4o2"), d(l, "class", "bar prompt svelte-10gs4o2"), d(l, "style", i = /*span*/
      e[24](
        /*p*/
        e[60].start,
        /*p*/
        e[60].end
      )), d(l, "title", a = /*p*/
      e[60].text), K(
        l,
        "alt",
        /*i*/
        e[59] % 2 === 1
      );
    },
    m(f, v) {
      V(f, l, v), k(l, n), k(n, s);
    },
    p(f, v) {
      v[0] & /*prompts*/
      4194304 && t !== (t = /*p*/
      f[60].text + "") && ie(s, t), v[0] & /*prompts*/
      4194304 && i !== (i = /*span*/
      f[24](
        /*p*/
        f[60].start,
        /*p*/
        f[60].end
      )) && d(l, "style", i), v[0] & /*prompts*/
      4194304 && a !== (a = /*p*/
      f[60].text) && d(l, "title", a);
    },
    d(f) {
      f && h(l);
    }
  };
}
function Xe(e) {
  let l, n = ne(
    /*prompts*/
    e[22].slice(1)
  ), t = [];
  for (let s = 0; s < n.length; s += 1)
    t[s] = Ge(Pe(e, n, s));
  return {
    c() {
      for (let s = 0; s < t.length; s += 1)
        t[s].c();
      l = Ne();
    },
    l(s) {
      for (let i = 0; i < t.length; i += 1)
        t[i].l(s);
      l = Ne();
    },
    m(s, i) {
      for (let a = 0; a < t.length; a += 1)
        t[a] && t[a].m(s, i);
      V(s, l, i);
    },
    p(s, i) {
      if (i[0] & /*span, prompts, blend, fmt*/
      55574528) {
        n = ne(
          /*prompts*/
          s[22].slice(1)
        );
        let a;
        for (a = 0; a < n.length; a += 1) {
          const f = Pe(s, n, a);
          t[a] ? t[a].p(f, i) : (t[a] = Ge(f), t[a].c(), t[a].m(l.parentNode, l));
        }
        for (; a < t.length; a += 1)
          t[a].d(1);
        t.length = n.length;
      }
    },
    d(s) {
      s && h(l), ke(t, s);
    }
  };
}
function Ge(e) {
  let l, n, t;
  return {
    c() {
      l = y("div"), this.h();
    },
    l(s) {
      l = E(s, "DIV", { class: !0, style: !0, title: !0 }), I(l).forEach(h), this.h();
    },
    h() {
      d(l, "class", "blend svelte-10gs4o2"), d(l, "style", n = /*span*/
      e[24](
        /*p*/
        e[60].start - /*blend*/
        e[20] / 2,
        /*p*/
        e[60].start + /*blend*/
        e[20] / 2
      )), d(l, "title", t = `Blend ${/*fmt*/
      e[25](
        /*blend*/
        e[20]
      )} s`), K(
        l,
        "rev",
        /*i*/
        e[59] % 2 === 1
      );
    },
    m(s, i) {
      V(s, l, i);
    },
    p(s, i) {
      i[0] & /*prompts, blend*/
      5242880 && n !== (n = /*span*/
      s[24](
        /*p*/
        s[60].start - /*blend*/
        s[20] / 2,
        /*p*/
        s[60].start + /*blend*/
        s[20] / 2
      )) && d(l, "style", n), i[0] & /*blend*/
      1048576 && t !== (t = `Blend ${/*fmt*/
      s[25](
        /*blend*/
        s[20]
      )} s`) && d(l, "title", t);
    },
    d(s) {
      s && h(l);
    }
  };
}
function He(e) {
  let l;
  return {
    c() {
      l = y("div"), this.h();
    },
    l(n) {
      l = E(n, "DIV", { class: !0 }), I(l).forEach(h), this.h();
    },
    h() {
      d(l, "class", "playhead svelte-10gs4o2"), Z(
        l,
        "left",
        /*pct*/
        e[23](
          /*playhead*/
          e[15]
        )
      );
    },
    m(n, t) {
      V(n, l, t);
    },
    p(n, t) {
      t[0] & /*playhead*/
      32768 && Z(
        l,
        "left",
        /*pct*/
        n[23](
          /*playhead*/
          n[15]
        )
      );
    },
    d(n) {
      n && h(l);
    }
  };
}
function Je(e) {
  let l;
  return {
    c() {
      l = y("div"), this.h();
    },
    l(n) {
      l = E(n, "DIV", { class: !0 }), I(l).forEach(h), this.h();
    },
    h() {
      d(l, "class", "playhead svelte-10gs4o2"), Z(
        l,
        "left",
        /*pct*/
        e[23](
          /*playhead*/
          e[15]
        )
      );
    },
    m(n, t) {
      V(n, l, t);
    },
    p(n, t) {
      t[0] & /*playhead*/
      32768 && Z(
        l,
        "left",
        /*pct*/
        n[23](
          /*playhead*/
          n[15]
        )
      );
    },
    d(n) {
      n && h(l);
    }
  };
}
function Qe(e) {
  let l, n, t, s, i, a;
  return {
    c() {
      l = y("div"), t = A(), s = y("div"), i = y("span"), this.h();
    },
    l(f) {
      l = E(f, "DIV", { class: !0, style: !0 }), I(l).forEach(h), t = S(f), s = E(f, "DIV", { class: !0, title: !0 });
      var v = I(s);
      i = E(v, "SPAN", { class: !0 }), I(i).forEach(h), v.forEach(h), this.h();
    },
    h() {
      d(l, "class", "snap-line svelte-10gs4o2"), d(l, "style", n = /*span*/
      e[24](Math.min(
        /*f*/
        e[55].t,
        /*f*/
        e[55].snapped
      ), Math.max(
        /*f*/
        e[55].t,
        /*f*/
        e[55].snapped
      ))), d(i, "class", "diamond svelte-10gs4o2"), d(s, "class", "marker ghost svelte-10gs4o2"), d(s, "title", a = `snaps to ${/*fmt*/
      e[25](
        /*f*/
        e[55].snapped
      )} s`), Z(
        s,
        "left",
        /*pct*/
        e[23](
          /*f*/
          e[55].snapped
        )
      );
    },
    m(f, v) {
      V(f, l, v), V(f, t, v), V(f, s, v), k(s, i);
    },
    p(f, v) {
      v[0] & /*frames*/
      65536 && n !== (n = /*span*/
      f[24](Math.min(
        /*f*/
        f[55].t,
        /*f*/
        f[55].snapped
      ), Math.max(
        /*f*/
        f[55].t,
        /*f*/
        f[55].snapped
      ))) && d(l, "style", n), v[0] & /*frames*/
      65536 && a !== (a = `snaps to ${/*fmt*/
      f[25](
        /*f*/
        f[55].snapped
      )} s`) && d(s, "title", a), v[0] & /*frames*/
      65536 && Z(
        s,
        "left",
        /*pct*/
        f[23](
          /*f*/
          f[55].snapped
        )
      );
    },
    d(f) {
      f && (h(l), h(t), h(s));
    }
  };
}
function dl(e) {
  let l = (
    /*f*/
    (e[55].label ?? "") + ""
  ), n;
  return {
    c() {
      n = ee(l);
    },
    l(t) {
      n = x(t, l);
    },
    m(t, s) {
      V(t, n, s);
    },
    p(t, s) {
      s[0] & /*frames*/
      65536 && l !== (l = /*f*/
      (t[55].label ?? "") + "") && ie(n, l);
    },
    d(t) {
      t && h(n);
    }
  };
}
function ul(e) {
  let l = (
    /*t*/
    e[56].toFixed(2) + ""
  ), n, t;
  return {
    c() {
      n = ee(l), t = ee(" s");
    },
    l(s) {
      n = x(s, l), t = x(s, " s");
    },
    m(s, i) {
      V(s, n, i), V(s, t, i);
    },
    p(s, i) {
      i[0] & /*drag, frames*/
      81920 && l !== (l = /*t*/
      s[56].toFixed(2) + "") && ie(n, l);
    },
    d(s) {
      s && (h(n), h(t));
    }
  };
}
function Ye(e) {
  let l = (
    /*f*/
    e[55].kind === "key" && /*f*/
    e[55].snapped != null && Math.abs(
      /*f*/
      e[55].snapped - /*f*/
      e[55].t
    ) > 0.05 && !/*drag*/
    (e[14] && /*drag*/
    e[14].i === /*i*/
    e[59])
  ), n, t, s, i, a, f, v, m, c, W, P, D, j, b = l && Qe(e);
  function w(M, u) {
    return (
      /*drag*/
      M[14] && /*drag*/
      M[14].i === /*i*/
      M[59] ? ul : dl
    );
  }
  let X = w(e), N = X(e);
  function $(...M) {
    return (
      /*pointerdown_handler*/
      e[45](
        /*i*/
        e[59],
        ...M
      )
    );
  }
  function de(...M) {
    return (
      /*keydown_handler*/
      e[46](
        /*i*/
        e[59],
        ...M
      )
    );
  }
  return {
    c() {
      b && b.c(), n = A(), t = y("button"), s = y("span"), i = A(), a = y("span"), N.c(), v = A(), this.h();
    },
    l(M) {
      b && b.l(M), n = S(M), t = E(M, "BUTTON", {
        type: !0,
        class: !0,
        "aria-label": !0,
        title: !0,
        tabindex: !0
      });
      var u = I(t);
      s = E(u, "SPAN", { class: !0 }), I(s).forEach(h), i = S(u), a = E(u, "SPAN", { class: !0 });
      var oe = I(a);
      N.l(oe), oe.forEach(h), v = S(u), u.forEach(h), this.h();
    },
    h() {
      d(s, "class", "diamond svelte-10gs4o2"), d(a, "class", f = "mlabel " + /*anchor*/
      e[26](
        /*t*/
        e[56]
      ) + " svelte-10gs4o2"), d(t, "type", "button"), d(t, "class", m = "marker " + /*f*/
      e[55].kind + " svelte-10gs4o2"), d(t, "aria-label", c = /*frame_label*/
      e[33](
        /*f*/
        e[55]
      )), d(t, "title", W = /*f*/
      e[55].kind === "key" && /*f*/
      e[55].snapped != null && Math.abs(
        /*f*/
        e[55].snapped - /*f*/
        e[55].t
      ) > 0.05 ? `${/*f*/
      e[55].label ?? "Key"} at ${/*fmt*/
      e[25](
        /*f*/
        e[55].t
      )} s, snaps to ${/*fmt*/
      e[25](
        /*f*/
        e[55].snapped
      )} s` : `${/*f*/
      e[55].label ?? /*f*/
      e[55].kind} at ${/*fmt*/
      e[25](
        /*f*/
        e[55].t
      )} s`), d(t, "tabindex", P = /*draggable*/
      e[57] || /*f*/
      e[55].kind !== "key" ? 0 : -1), K(
        t,
        "unset",
        /*f*/
        e[55].set === !1
      ), K(
        t,
        "draggable",
        /*draggable*/
        e[57]
      ), K(
        t,
        "dragging",
        /*drag*/
        e[14] && /*drag*/
        e[14].i === /*i*/
        e[59]
      ), Z(
        t,
        "left",
        /*pct*/
        e[23](
          /*t*/
          e[56]
        )
      );
    },
    m(M, u) {
      b && b.m(M, u), V(M, n, u), V(M, t, u), k(t, s), k(t, i), k(t, a), N.m(a, null), k(t, v), D || (j = [
        we(t, "pointerdown", $),
        we(
          t,
          "pointermove",
          /*on_move*/
          e[29]
        ),
        we(
          t,
          "pointerup",
          /*on_up*/
          e[30]
        ),
        we(
          t,
          "pointercancel",
          /*on_up*/
          e[30]
        ),
        we(t, "keydown", de)
      ], D = !0);
    },
    p(M, u) {
      e = M, u[0] & /*frames, drag*/
      81920 && (l = /*f*/
      e[55].kind === "key" && /*f*/
      e[55].snapped != null && Math.abs(
        /*f*/
        e[55].snapped - /*f*/
        e[55].t
      ) > 0.05 && !/*drag*/
      (e[14] && /*drag*/
      e[14].i === /*i*/
      e[59])), l ? b ? b.p(e, u) : (b = Qe(e), b.c(), b.m(n.parentNode, n)) : b && (b.d(1), b = null), X === (X = w(e)) && N ? N.p(e, u) : (N.d(1), N = X(e), N && (N.c(), N.m(a, null))), u[0] & /*drag, frames*/
      81920 && f !== (f = "mlabel " + /*anchor*/
      e[26](
        /*t*/
        e[56]
      ) + " svelte-10gs4o2") && d(a, "class", f), u[0] & /*frames*/
      65536 && m !== (m = "marker " + /*f*/
      e[55].kind + " svelte-10gs4o2") && d(t, "class", m), u[0] & /*frames*/
      65536 && c !== (c = /*frame_label*/
      e[33](
        /*f*/
        e[55]
      )) && d(t, "aria-label", c), u[0] & /*frames*/
      65536 && W !== (W = /*f*/
      e[55].kind === "key" && /*f*/
      e[55].snapped != null && Math.abs(
        /*f*/
        e[55].snapped - /*f*/
        e[55].t
      ) > 0.05 ? `${/*f*/
      e[55].label ?? "Key"} at ${/*fmt*/
      e[25](
        /*f*/
        e[55].t
      )} s, snaps to ${/*fmt*/
      e[25](
        /*f*/
        e[55].snapped
      )} s` : `${/*f*/
      e[55].label ?? /*f*/
      e[55].kind} at ${/*fmt*/
      e[25](
        /*f*/
        e[55].t
      )} s`) && d(t, "title", W), u[0] & /*editable, frames*/
      196608 && P !== (P = /*draggable*/
      e[57] || /*f*/
      e[55].kind !== "key" ? 0 : -1) && d(t, "tabindex", P), u[0] & /*frames, frames*/
      65536 && K(
        t,
        "unset",
        /*f*/
        e[55].set === !1
      ), u[0] & /*frames, editable, frames*/
      196608 && K(
        t,
        "draggable",
        /*draggable*/
        e[57]
      ), u[0] & /*frames, drag*/
      81920 && K(
        t,
        "dragging",
        /*drag*/
        e[14] && /*drag*/
        e[14].i === /*i*/
        e[59]
      ), u[0] & /*drag, frames*/
      81920 && Z(
        t,
        "left",
        /*pct*/
        e[23](
          /*t*/
          e[56]
        )
      );
    },
    d(M) {
      M && (h(n), h(t)), b && b.d(M), N.d(), D = !1, al(j);
    }
  };
}
function Ze(e) {
  let l, n, t, s = (
    /*value*/
    e[0].keyframes_reason + ""
  ), i;
  return {
    c() {
      l = y("div"), n = A(), t = y("div"), i = ee(s), this.h();
    },
    l(a) {
      l = E(a, "DIV", { class: !0 }), I(l).forEach(h), n = S(a), t = E(a, "DIV", { class: !0 });
      var f = I(t);
      i = x(f, s), f.forEach(h), this.h();
    },
    h() {
      d(l, "class", "lane-label svelte-10gs4o2"), d(t, "class", "note svelte-10gs4o2");
    },
    m(a, f) {
      V(a, l, f), V(a, n, f), V(a, t, f), k(t, i);
    },
    p(a, f) {
      f[0] & /*value*/
      1 && s !== (s = /*value*/
      a[0].keyframes_reason + "") && ie(i, s);
    },
    d(a) {
      a && (h(l), h(n), h(t));
    }
  };
}
function hl(e) {
  let l = (
    /*ln*/
    (e[52].text ?? "") + ""
  ), n;
  return {
    c() {
      n = ee(l);
    },
    l(t) {
      n = x(t, l);
    },
    m(t, s) {
      V(t, n, s);
    },
    p(t, s) {
      s[0] & /*lanes*/
      2097152 && l !== (l = /*ln*/
      (t[52].text ?? "") + "") && ie(n, l);
    },
    d(t) {
      t && h(n);
    }
  };
}
function cl(e) {
  let l = (
    /*ln*/
    (e[52].reason || "Disabled") + ""
  ), n;
  return {
    c() {
      n = ee(l);
    },
    l(t) {
      n = x(t, l);
    },
    m(t, s) {
      V(t, n, s);
    },
    p(t, s) {
      s[0] & /*lanes*/
      2097152 && l !== (l = /*ln*/
      (t[52].reason || "Disabled") + "") && ie(n, l);
    },
    d(t) {
      t && h(n);
    }
  };
}
function $e(e) {
  let l, n = (
    /*ln*/
    e[52].label + ""
  ), t, s, i, a, f, v, m, c, W;
  function P(b, w) {
    return (
      /*ln*/
      b[52].enabled === !1 ? cl : hl
    );
  }
  let D = P(e), j = D(e);
  return {
    c() {
      l = y("div"), t = ee(n), i = A(), a = y("div"), f = y("div"), v = y("span"), j.c(), W = A(), this.h();
    },
    l(b) {
      l = E(b, "DIV", { class: !0, title: !0 });
      var w = I(l);
      t = x(w, n), w.forEach(h), i = S(b), a = E(b, "DIV", { class: !0 });
      var X = I(a);
      f = E(X, "DIV", { class: !0, style: !0, title: !0 });
      var N = I(f);
      v = E(N, "SPAN", { class: !0 });
      var $ = I(v);
      j.l($), $.forEach(h), N.forEach(h), W = S(X), X.forEach(h), this.h();
    },
    h() {
      d(l, "class", "lane-label svelte-10gs4o2"), d(l, "title", s = /*ln*/
      e[52].label), d(v, "class", "txt svelte-10gs4o2"), d(f, "class", "bar extra svelte-10gs4o2"), d(f, "style", m = /*span*/
      e[24](
        /*ln*/
        e[52].start,
        /*ln*/
        e[52].end
      )), d(f, "title", c = /*ln*/
      e[52].enabled === !1 ? `${/*ln*/
      e[52].text ?? ""} (${/*ln*/
      e[52].reason ?? "disabled"})` : (
        /*ln*/
        e[52].text
      )), K(
        f,
        "off",
        /*ln*/
        e[52].enabled === !1
      ), d(a, "class", "track lane svelte-10gs4o2");
    },
    m(b, w) {
      V(b, l, w), k(l, t), V(b, i, w), V(b, a, w), k(a, f), k(f, v), j.m(v, null), k(a, W);
    },
    p(b, w) {
      w[0] & /*lanes*/
      2097152 && n !== (n = /*ln*/
      b[52].label + "") && ie(t, n), w[0] & /*lanes*/
      2097152 && s !== (s = /*ln*/
      b[52].label) && d(l, "title", s), D === (D = P(b)) && j ? j.p(b, w) : (j.d(1), j = D(b), j && (j.c(), j.m(v, null))), w[0] & /*lanes*/
      2097152 && m !== (m = /*span*/
      b[24](
        /*ln*/
        b[52].start,
        /*ln*/
        b[52].end
      )) && d(f, "style", m), w[0] & /*lanes*/
      2097152 && c !== (c = /*ln*/
      b[52].enabled === !1 ? `${/*ln*/
      b[52].text ?? ""} (${/*ln*/
      b[52].reason ?? "disabled"})` : (
        /*ln*/
        b[52].text
      )) && d(f, "title", c), w[0] & /*lanes*/
      2097152 && K(
        f,
        "off",
        /*ln*/
        b[52].enabled === !1
      );
    },
    d(b) {
      b && (h(l), h(i), h(a)), j.d();
    }
  };
}
function vl(e) {
  let l, n, t, s, i = (
    /*show_label*/
    (e[5] && /*label*/
    e[4] || /*duration*/
    e[11] && /*caption*/
    e[19]) && Be(e)
  );
  function a(m, c) {
    return (
      /*duration*/
      m[11] ? rl : _l
    );
  }
  let f = a(e), v = f(e);
  return {
    c() {
      l = y("div"), i && i.c(), n = A(), v.c(), this.h();
    },
    l(m) {
      l = E(m, "DIV", { id: !0, class: !0 });
      var c = I(l);
      i && i.l(c), n = S(c), v.l(c), c.forEach(h), this.h();
    },
    h() {
      d(l, "id", t = /*elem_id*/
      e[1] || null), d(l, "class", s = "fps-timeline " + /*elem_classes*/
      e[2].join(" ") + " svelte-10gs4o2"), K(l, "hidden", !/*visible*/
      e[3]), K(
        l,
        "boxed",
        /*container*/
        e[8]
      ), Z(
        l,
        "flex-grow",
        /*scale*/
        e[6]
      ), Z(
        l,
        "min-width",
        /*min_width*/
        e[7] ? `${/*min_width*/
        e[7]}px` : null
      );
    },
    m(m, c) {
      V(m, l, c), i && i.m(l, null), k(l, n), v.m(l, null);
    },
    p(m, c) {
      /*show_label*/
      m[5] && /*label*/
      m[4] || /*duration*/
      m[11] && /*caption*/
      m[19] ? i ? i.p(m, c) : (i = Be(m), i.c(), i.m(l, n)) : i && (i.d(1), i = null), f === (f = a(m)) && v ? v.p(m, c) : (v.d(1), v = f(m), v && (v.c(), v.m(l, null))), c[0] & /*elem_id*/
      2 && t !== (t = /*elem_id*/
      m[1] || null) && d(l, "id", t), c[0] & /*elem_classes*/
      4 && s !== (s = "fps-timeline " + /*elem_classes*/
      m[2].join(" ") + " svelte-10gs4o2") && d(l, "class", s), c[0] & /*elem_classes, visible*/
      12 && K(l, "hidden", !/*visible*/
      m[3]), c[0] & /*elem_classes, container*/
      260 && K(
        l,
        "boxed",
        /*container*/
        m[8]
      ), c[0] & /*scale*/
      64 && Z(
        l,
        "flex-grow",
        /*scale*/
        m[6]
      ), c[0] & /*min_width*/
      128 && Z(
        l,
        "min-width",
        /*min_width*/
        m[7] ? `${/*min_width*/
        m[7]}px` : null
      );
    },
    i: Ie,
    o: Ie,
    d(m) {
      m && h(l), i && i.d(), v.d();
    }
  };
}
function bl(e, l, n) {
  let t, s, i, a, f, v, m, c, W, P;
  var D, j, b, w, X;
  let { gradio: N } = l, { elem_id: $ = "" } = l, { elem_classes: de = [] } = l, { visible: M = !0 } = l, { value: u = null } = l, { label: oe = "" } = l, { show_label: G = !0 } = l, { interactive: fe = !0 } = l, { loading_status: me = void 0 } = l, { scale: ve = null } = l, { min_width: ge = void 0 } = l, { root: be = "" } = l, { container: re = !0 } = l, O = 600, se, C = null, R = null;
  fl(() => {
    const _ = (p) => {
      var q;
      const le = (q = p.detail) !== null && q !== void 0 ? q : {};
      le.elem_id === $ && n(15, R = typeof le.t == "number" ? le.t : null);
    };
    return window.addEventListener("fps-timeline-playhead", _), () => window.removeEventListener("fps-timeline-playhead", _);
  });
  const H = (_) => `${Math.min(Math.max(_, 0), t) / t * 100}%`, ue = (_, p) => `left:${H(_)};width:${(Math.min(p, t) - Math.max(_, 0)) / t * 100}%`, z = (_) => `${(Math.round(_ * 10) / 10).toFixed(1)}`, T = (_) => Math.round(_ * 10) / 10;
  function J(_, p, q) {
    if (!p) return [];
    const le = /* @__PURE__ */ new Set([0, p]);
    for (const te of _)
      le.add(T(te.start)), le.add(T(te.end));
    const De = [...le].filter((te) => te >= 0 && te <= p).sort((te, Ee) => te - Ee), Ve = 34, pe = [];
    let Me = -1 / 0;
    for (const te of De) {
      const Ee = te / p * q, Ce = te === p;
      if (Ce)
        for (; pe.length > 1 && Ee - pe[pe.length - 1].t / p * q < Ve; ) pe.pop();
      else if (Ee - Me < Ve) continue;
      pe.push({
        t: te,
        anchor: te === 0 ? "left" : Ce ? "right" : "mid"
      }), Me = Ee;
    }
    return pe;
  }
  function Q(_) {
    const p = _ / t;
    return p < 0.03 ? "left" : p > 0.97 ? "right" : "mid";
  }
  function he(_, p) {
    var q;
    return (u == null ? void 0 : u.selected_section) === p ? "selected" : (q = _.state) !== null && q !== void 0 ? q : "normal";
  }
  function L(_, p) {
    if (!u) return;
    const q = a.map((le, De) => De === _ ? Object.assign(Object.assign({}, le), { t: T(p) }) : le);
    n(0, u = Object.assign(Object.assign({}, u), { frames: q })), N.dispatch("change"), N.dispatch("input");
  }
  function Y(_) {
    const p = se.getBoundingClientRect(), q = (_ - p.left) / p.width * t;
    return Math.min(Math.max(q, 0.1), t - 0.1);
  }
  function _e(_, p) {
    !c || a[p].kind !== "key" || (_.currentTarget.setPointerCapture(_.pointerId), n(14, C = { i: p, t: a[p].t, moved: !1 }), _.preventDefault());
  }
  function U(_) {
    C && n(14, C = Object.assign(Object.assign({}, C), { t: Y(_.clientX), moved: !0 }));
  }
  function r() {
    if (!C) return;
    const { i: _, t: p, moved: q } = C;
    n(14, C = null), q && T(p) !== a[_].t && L(_, p);
  }
  function g(_, p) {
    if (!c || a[p].kind !== "key") return;
    const q = _.key === "ArrowRight" ? 0.1 : _.key === "ArrowLeft" ? -0.1 : 0;
    if (!q) return;
    _.preventDefault();
    const le = Math.min(Math.max(a[p].t + q, 0.1), t - 0.1);
    L(p, le);
  }
  function o(_) {
    const p = s[_];
    if (!(u != null && u.selectable)) {
      window.dispatchEvent(new CustomEvent(
        "fps-timeline-seek",
        {
          detail: { elem_id: $, t: p.start, index: _ }
        }
      ));
      return;
    }
    n(0, u = Object.assign(Object.assign({}, u), { selected_section: _ })), N.dispatch("select", {
      index: _,
      value: {
        start: p.start,
        end: p.end,
        order: p.order
      }
    });
  }
  function B(_) {
    var p;
    return `${(p = _.label) !== null && p !== void 0 ? p : _.kind} keyframe at ${z(_.t)} seconds${_.set === !1 ? ", not set" : ""}`;
  }
  function ae() {
    O = this.clientWidth, n(9, O);
  }
  const ce = (_) => o(_), F = (_, p) => _e(p, _), xe = (_, p) => g(p, _);
  function el(_) {
    sl[_ ? "unshift" : "push"](() => {
      se = _, n(13, se);
    });
  }
  return e.$$set = (_) => {
    "gradio" in _ && n(34, N = _.gradio), "elem_id" in _ && n(1, $ = _.elem_id), "elem_classes" in _ && n(2, de = _.elem_classes), "visible" in _ && n(3, M = _.visible), "value" in _ && n(0, u = _.value), "label" in _ && n(4, oe = _.label), "show_label" in _ && n(5, G = _.show_label), "interactive" in _ && n(35, fe = _.interactive), "loading_status" in _ && n(36, me = _.loading_status), "scale" in _ && n(6, ve = _.scale), "min_width" in _ && n(7, ge = _.min_width), "root" in _ && n(37, be = _.root), "container" in _ && n(8, re = _.container);
  }, e.$$.update = () => {
    e.$$.dirty[0] & /*value*/
    1 && n(11, t = u && u.duration > 0 ? u.duration : 0), e.$$.dirty[0] & /*value*/
    1 | e.$$.dirty[1] & /*_a*/
    128 && n(10, s = n(38, D = u == null ? void 0 : u.sections) !== null && D !== void 0 ? D : []), e.$$.dirty[0] & /*value*/
    1 | e.$$.dirty[1] & /*_b*/
    256 && n(22, i = n(39, j = u == null ? void 0 : u.prompts) !== null && j !== void 0 ? j : []), e.$$.dirty[0] & /*value*/
    1 | e.$$.dirty[1] & /*_c*/
    512 && n(16, a = n(40, b = u == null ? void 0 : u.frames) !== null && b !== void 0 ? b : []), e.$$.dirty[0] & /*value*/
    1 | e.$$.dirty[1] & /*_d*/
    1024 && n(21, f = n(41, w = u == null ? void 0 : u.lanes) !== null && w !== void 0 ? w : []), e.$$.dirty[0] & /*value*/
    1 | e.$$.dirty[1] & /*_e*/
    2048 && n(20, v = Math.max(0, n(42, X = u == null ? void 0 : u.blend) !== null && X !== void 0 ? X : 0)), e.$$.dirty[0] & /*value*/
    1 && n(12, m = (u == null ? void 0 : u.keyframes_enabled) !== !1), e.$$.dirty[0] & /*keys_enabled*/
    4096 | e.$$.dirty[1] & /*interactive*/
    16 && n(17, c = fe !== !1 && m), e.$$.dirty[0] & /*value*/
    1 && n(19, W = (u == null ? void 0 : u.direction) === "backward" ? "generated end → start" : (u == null ? void 0 : u.direction) === "forward" ? "generated start → end" : ""), e.$$.dirty[0] & /*sections, duration, track_width*/
    3584 && n(18, P = J(s, t, O));
  }, [
    u,
    $,
    de,
    M,
    oe,
    G,
    ve,
    ge,
    re,
    O,
    s,
    t,
    m,
    se,
    C,
    R,
    a,
    c,
    P,
    W,
    v,
    f,
    i,
    H,
    ue,
    z,
    Q,
    he,
    _e,
    U,
    r,
    g,
    o,
    B,
    N,
    fe,
    me,
    be,
    D,
    j,
    b,
    w,
    X,
    ae,
    ce,
    F,
    xe,
    el
  ];
}
class ml extends ll {
  constructor(l) {
    super(), il(
      this,
      l,
      bl,
      vl,
      ol,
      {
        gradio: 34,
        elem_id: 1,
        elem_classes: 2,
        visible: 3,
        value: 0,
        label: 4,
        show_label: 5,
        interactive: 35,
        loading_status: 36,
        scale: 6,
        min_width: 7,
        root: 37,
        container: 8
      },
      null,
      [-1, -1, -1]
    );
  }
}
export {
  ml as default
};
