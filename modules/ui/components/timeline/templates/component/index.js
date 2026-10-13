const {
  SvelteComponent: Ze,
  add_iframe_resize_listener: $e,
  add_render_callback: xe,
  append_hydration: g,
  attr: u,
  binding_callbacks: el,
  children: I,
  claim_element: y,
  claim_space: j,
  claim_text: J,
  destroy_each: he,
  detach: h,
  element: E,
  empty: De,
  ensure_array_like: Z,
  get_svelte_dataset: me,
  init: ll,
  insert_hydration: V,
  listen: ve,
  noop: pe,
  run_all: tl,
  safe_not_equal: nl,
  set_data: ee,
  set_style: le,
  space: O,
  text: Q,
  toggle_class: U
} = window.__gradio__svelte__internal;
function Ie(e, l, n) {
  const t = e.slice();
  return t[51] = l[n], t;
}
function Ve(e, l, n) {
  const t = e.slice();
  t[54] = l[n], t[58] = n;
  const s = (
    /*drag*/
    t[14] && /*drag*/
    t[14].i === /*i*/
    t[58] ? (
      /*drag*/
      t[14].t
    ) : (
      /*f*/
      t[54].t
    )
  );
  t[55] = s;
  const i = (
    /*editable*/
    t[16] && /*f*/
    t[54].kind === "key"
  );
  return t[56] = i, t;
}
function Me(e, l, n) {
  const t = e.slice();
  return t[59] = l[n], t[58] = n, t;
}
function Ce(e, l, n) {
  const t = e.slice();
  return t[59] = l[n], t[58] = n, t;
}
function Ne(e, l, n) {
  const t = e.slice();
  t[62] = l[n], t[58] = n;
  const s = (
    /*cell_state*/
    t[26](
      /*s*/
      t[62],
      /*i*/
      t[58]
    )
  );
  t[63] = s;
  const i = (
    /*s*/
    (t[62].end - /*s*/
    t[62].start) / /*duration*/
    t[11] * /*track_width*/
    t[9]
  );
  return t[64] = i, t;
}
function Se(e, l, n) {
  const t = e.slice();
  return t[66] = l[n], t;
}
function Ae(e) {
  let l, n, t = (
    /*show_label*/
    e[5] && /*label*/
    e[4] && Pe(e)
  ), s = (
    /*duration*/
    e[11] && /*caption*/
    e[18] && je(e)
  );
  return {
    c() {
      l = E("div"), t && t.c(), n = O(), s && s.c(), this.h();
    },
    l(i) {
      l = y(i, "DIV", { class: !0 });
      var a = I(l);
      t && t.l(a), n = j(a), s && s.l(a), a.forEach(h), this.h();
    },
    h() {
      u(l, "class", "head svelte-ccfote");
    },
    m(i, a) {
      V(i, l, a), t && t.m(l, null), g(l, n), s && s.m(l, null);
    },
    p(i, a) {
      /*show_label*/
      i[5] && /*label*/
      i[4] ? t ? t.p(i, a) : (t = Pe(i), t.c(), t.m(l, n)) : t && (t.d(1), t = null), /*duration*/
      i[11] && /*caption*/
      i[18] ? s ? s.p(i, a) : (s = je(i), s.c(), s.m(l, null)) : s && (s.d(1), s = null);
    },
    d(i) {
      i && h(l), t && t.d(), s && s.d();
    }
  };
}
function Pe(e) {
  let l, n;
  return {
    c() {
      l = E("span"), n = Q(
        /*label*/
        e[4]
      ), this.h();
    },
    l(t) {
      l = y(t, "SPAN", { class: !0 });
      var s = I(l);
      n = J(
        s,
        /*label*/
        e[4]
      ), s.forEach(h), this.h();
    },
    h() {
      u(l, "class", "block-label svelte-ccfote");
    },
    m(t, s) {
      V(t, l, s), g(l, n);
    },
    p(t, s) {
      s[0] & /*label*/
      16 && ee(
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
function je(e) {
  let l, n;
  return {
    c() {
      l = E("span"), n = Q(
        /*caption*/
        e[18]
      ), this.h();
    },
    l(t) {
      l = y(t, "SPAN", { class: !0 });
      var s = I(l);
      n = J(
        s,
        /*caption*/
        e[18]
      ), s.forEach(h), this.h();
    },
    h() {
      u(l, "class", "caption svelte-ccfote");
    },
    m(t, s) {
      V(t, l, s), g(l, n);
    },
    p(t, s) {
      s[0] & /*caption*/
      262144 && ee(
        n,
        /*caption*/
        t[18]
      );
    },
    d(t) {
      t && h(l);
    }
  };
}
function sl(e) {
  let l, n, t, s, i, a, f, v = "Sections", b, m, D, B, S = "Prompt", w, c, M, X, A, H, fe = "Frames", C, r, $, ue, re, _e, te = Z(
    /*ticks*/
    e[17]
  ), F = [];
  for (let _ = 0; _ < te.length; _ += 1)
    F[_] = Oe(Se(e, te, _));
  let ne = Z(
    /*sections*/
    e[10]
  ), z = [];
  for (let _ = 0; _ < ne.length; _ += 1)
    z[_] = Be(Ne(e, ne, _));
  let q = (
    /*prompts*/
    e[21].length === 0 && Fe()
  ), x = Z(
    /*prompts*/
    e[21]
  ), N = [];
  for (let _ = 0; _ < x.length; _ += 1)
    N[_] = ze(Ce(e, x, _));
  let L = (
    /*blend*/
    e[19] > 0 && qe(e)
  ), se = Z(
    /*frames*/
    e[15]
  ), K = [];
  for (let _ = 0; _ < se.length; _ += 1)
    K[_] = Ue(Ve(e, se, _));
  let T = !/*keys_enabled*/
  e[12] && /*value*/
  e[0].keyframes_reason && Le(e), ie = Z(
    /*lanes*/
    e[20]
  ), W = [];
  for (let _ = 0; _ < ie.length; _ += 1)
    W[_] = We(Ie(e, ie, _));
  return {
    c() {
      l = E("div"), n = E("div"), t = O(), s = E("div");
      for (let _ = 0; _ < F.length; _ += 1)
        F[_].c();
      a = O(), f = E("div"), f.textContent = v, b = O(), m = E("div");
      for (let _ = 0; _ < z.length; _ += 1)
        z[_].c();
      D = O(), B = E("div"), B.textContent = S, w = O(), c = E("div"), q && q.c(), M = O();
      for (let _ = 0; _ < N.length; _ += 1)
        N[_].c();
      X = O(), L && L.c(), A = O(), H = E("div"), H.textContent = fe, C = O(), r = E("div"), $ = E("div"), ue = O();
      for (let _ = 0; _ < K.length; _ += 1)
        K[_].c();
      re = O(), T && T.c(), _e = O();
      for (let _ = 0; _ < W.length; _ += 1)
        W[_].c();
      this.h();
    },
    l(_) {
      l = y(_, "DIV", { class: !0 });
      var k = I(l);
      n = y(k, "DIV", { class: !0 }), I(n).forEach(h), t = j(k), s = y(k, "DIV", { class: !0 });
      var o = I(s);
      for (let P = 0; P < F.length; P += 1)
        F[P].l(o);
      o.forEach(h), a = j(k), f = y(k, "DIV", { class: !0, "data-svelte-h": !0 }), me(f) !== "svelte-1e5iyc6" && (f.textContent = v), b = j(k), m = y(k, "DIV", { class: !0 });
      var R = I(m);
      for (let P = 0; P < z.length; P += 1)
        z[P].l(R);
      R.forEach(h), D = j(k), B = y(k, "DIV", { class: !0, "data-svelte-h": !0 }), me(B) !== "svelte-lym768" && (B.textContent = S), w = j(k), c = y(k, "DIV", { class: !0 });
      var ae = I(c);
      q && q.l(ae), M = j(ae);
      for (let P = 0; P < N.length; P += 1)
        N[P].l(ae);
      X = j(ae), L && L.l(ae), ae.forEach(h), A = j(k), H = y(k, "DIV", { class: !0, "data-svelte-h": !0 }), me(H) !== "svelte-144t6rb" && (H.textContent = fe), C = j(k), r = y(k, "DIV", { class: !0 });
      var de = I(r);
      $ = y(de, "DIV", { class: !0 }), I($).forEach(h), ue = j(de);
      for (let P = 0; P < K.length; P += 1)
        K[P].l(de);
      de.forEach(h), re = j(k), T && T.l(k), _e = j(k);
      for (let P = 0; P < W.length; P += 1)
        W[P].l(k);
      k.forEach(h), this.h();
    },
    h() {
      u(n, "class", "lane-label svelte-ccfote"), u(s, "class", "track ruler svelte-ccfote"), xe(() => (
        /*div1_elementresize_handler*/
        e[42].call(s)
      )), u(f, "class", "lane-label svelte-ccfote"), u(m, "class", "track sections svelte-ccfote"), u(B, "class", "lane-label svelte-ccfote"), u(c, "class", "track prompts svelte-ccfote"), u(H, "class", "lane-label top svelte-ccfote"), u($, "class", "axis svelte-ccfote"), u(r, "class", "track frames svelte-ccfote"), U(r, "disabled", !/*keys_enabled*/
      e[12]), u(l, "class", "grid svelte-ccfote");
    },
    m(_, k) {
      V(_, l, k), g(l, n), g(l, t), g(l, s);
      for (let o = 0; o < F.length; o += 1)
        F[o] && F[o].m(s, null);
      i = $e(
        s,
        /*div1_elementresize_handler*/
        e[42].bind(s)
      ), g(l, a), g(l, f), g(l, b), g(l, m);
      for (let o = 0; o < z.length; o += 1)
        z[o] && z[o].m(m, null);
      g(l, D), g(l, B), g(l, w), g(l, c), q && q.m(c, null), g(c, M);
      for (let o = 0; o < N.length; o += 1)
        N[o] && N[o].m(c, null);
      g(c, X), L && L.m(c, null), g(l, A), g(l, H), g(l, C), g(l, r), g(r, $), g(r, ue);
      for (let o = 0; o < K.length; o += 1)
        K[o] && K[o].m(r, null);
      e[46](r), g(l, re), T && T.m(l, null), g(l, _e);
      for (let o = 0; o < W.length; o += 1)
        W[o] && W[o].m(l, null);
    },
    p(_, k) {
      if (k[0] & /*ticks, pct, fmt*/
      21102592) {
        te = Z(
          /*ticks*/
          _[17]
        );
        let o;
        for (o = 0; o < te.length; o += 1) {
          const R = Se(_, te, o);
          F[o] ? F[o].p(R, k) : (F[o] = Oe(R), F[o].c(), F[o].m(s, null));
        }
        for (; o < F.length; o += 1)
          F[o].d(1);
        F.length = te.length;
      }
      if (k[0] & /*cell_state, sections, span, value, fmt, duration, track_width*/
      92278273 | k[1] & /*select_section*/
      1) {
        ne = Z(
          /*sections*/
          _[10]
        );
        let o;
        for (o = 0; o < ne.length; o += 1) {
          const R = Ne(_, ne, o);
          z[o] ? z[o].p(R, k) : (z[o] = Be(R), z[o].c(), z[o].m(m, null));
        }
        for (; o < z.length; o += 1)
          z[o].d(1);
        z.length = ne.length;
      }
      if (/*prompts*/
      _[21].length === 0 ? q || (q = Fe(), q.c(), q.m(c, M)) : q && (q.d(1), q = null), k[0] & /*span, prompts*/
      10485760) {
        x = Z(
          /*prompts*/
          _[21]
        );
        let o;
        for (o = 0; o < x.length; o += 1) {
          const R = Ce(_, x, o);
          N[o] ? N[o].p(R, k) : (N[o] = ze(R), N[o].c(), N[o].m(c, X));
        }
        for (; o < N.length; o += 1)
          N[o].d(1);
        N.length = x.length;
      }
      if (/*blend*/
      _[19] > 0 ? L ? L.p(_, k) : (L = qe(_), L.c(), L.m(c, null)) : L && (L.d(1), L = null), k[0] & /*frames, fmt, editable, drag, pct, on_down, on_move, on_up, on_key, anchor, span*/
      2076295168 | k[1] & /*frame_label*/
      2) {
        se = Z(
          /*frames*/
          _[15]
        );
        let o;
        for (o = 0; o < se.length; o += 1) {
          const R = Ve(_, se, o);
          K[o] ? K[o].p(R, k) : (K[o] = Ue(R), K[o].c(), K[o].m(r, null));
        }
        for (; o < K.length; o += 1)
          K[o].d(1);
        K.length = se.length;
      }
      if (k[0] & /*keys_enabled*/
      4096 && U(r, "disabled", !/*keys_enabled*/
      _[12]), !/*keys_enabled*/
      _[12] && /*value*/
      _[0].keyframes_reason ? T ? T.p(_, k) : (T = Le(_), T.c(), T.m(l, _e)) : T && (T.d(1), T = null), k[0] & /*span, lanes*/
      9437184) {
        ie = Z(
          /*lanes*/
          _[20]
        );
        let o;
        for (o = 0; o < ie.length; o += 1) {
          const R = Ie(_, ie, o);
          W[o] ? W[o].p(R, k) : (W[o] = We(R), W[o].c(), W[o].m(l, null));
        }
        for (; o < W.length; o += 1)
          W[o].d(1);
        W.length = ie.length;
      }
    },
    d(_) {
      _ && h(l), he(F, _), i(), he(z, _), q && q.d(), he(N, _), L && L.d(), he(K, _), e[46](null), T && T.d(), he(W, _);
    }
  };
}
function il(e) {
  let l, n = "Timeline appears once a length is set";
  return {
    c() {
      l = E("div"), l.textContent = n, this.h();
    },
    l(t) {
      l = y(t, "DIV", { class: !0, "data-svelte-h": !0 }), me(l) !== "svelte-16hw8yd" && (l.textContent = n), this.h();
    },
    h() {
      u(l, "class", "placeholder svelte-ccfote");
    },
    m(t, s) {
      V(t, l, s);
    },
    p: pe,
    d(t) {
      t && h(l);
    }
  };
}
function Oe(e) {
  let l, n = (
    /*fmt*/
    e[24](
      /*tk*/
      e[66].t
    ) + ""
  ), t, s, i;
  return {
    c() {
      l = E("span"), t = Q(n), s = Q("s"), this.h();
    },
    l(a) {
      l = y(a, "SPAN", { class: !0 });
      var f = I(l);
      t = J(f, n), s = J(f, "s"), f.forEach(h), this.h();
    },
    h() {
      u(l, "class", i = "tick " + /*tk*/
      e[66].anchor + " svelte-ccfote"), le(
        l,
        "left",
        /*pct*/
        e[22](
          /*tk*/
          e[66].t
        )
      );
    },
    m(a, f) {
      V(a, l, f), g(l, t), g(l, s);
    },
    p(a, f) {
      f[0] & /*ticks*/
      131072 && n !== (n = /*fmt*/
      a[24](
        /*tk*/
        a[66].t
      ) + "") && ee(t, n), f[0] & /*ticks*/
      131072 && i !== (i = "tick " + /*tk*/
      a[66].anchor + " svelte-ccfote") && u(l, "class", i), f[0] & /*ticks*/
      131072 && le(
        l,
        "left",
        /*pct*/
        a[22](
          /*tk*/
          a[66].t
        )
      );
    },
    d(a) {
      a && h(l);
    }
  };
}
function Te(e) {
  let l, n = (
    /*s*/
    e[62].order + ""
  ), t;
  return {
    c() {
      l = E("span"), t = Q(n), this.h();
    },
    l(s) {
      l = y(s, "SPAN", { class: !0 });
      var i = I(l);
      t = J(i, n), i.forEach(h), this.h();
    },
    h() {
      u(l, "class", "order svelte-ccfote");
    },
    m(s, i) {
      V(s, l, i), g(l, t);
    },
    p(s, i) {
      i[0] & /*sections*/
      1024 && n !== (n = /*s*/
      s[62].order + "") && ee(t, n);
    },
    d(s) {
      s && h(l);
    }
  };
}
function Be(e) {
  let l, n, t, s, i, a, f, v, b, m, D = (
    /*s*/
    e[62].order != null && /*w*/
    e[64] >= 16 && Te(e)
  );
  function B() {
    return (
      /*click_handler*/
      e[43](
        /*i*/
        e[58]
      )
    );
  }
  return {
    c() {
      l = E("button"), D && D.c(), n = O(), this.h();
    },
    l(S) {
      l = y(S, "BUTTON", {
        type: !0,
        class: !0,
        style: !0,
        tabindex: !0,
        "aria-disabled": !0,
        title: !0,
        "aria-label": !0
      });
      var w = I(l);
      D && D.l(w), n = j(w), w.forEach(h), this.h();
    },
    h() {
      u(l, "type", "button"), u(l, "class", t = "cell " + /*st*/
      e[63] + " svelte-ccfote"), u(l, "style", s = /*span*/
      e[23](
        /*s*/
        e[62].start,
        /*s*/
        e[62].end
      )), u(l, "tabindex", i = /*value*/
      e[0].selectable ? 0 : -1), u(l, "aria-disabled", a = !/*value*/
      e[0].selectable), u(l, "title", f = `${/*fmt*/
      e[24](
        /*s*/
        e[62].start
      )}–${/*fmt*/
      e[24](
        /*s*/
        e[62].end
      )} s${/*s*/
      e[62].order != null ? `, generated #${/*s*/
      e[62].order}` : ""}${/*st*/
      e[63] !== "normal" ? ` (${/*st*/
      e[63]})` : ""}`), u(l, "aria-label", v = `Section ${/*i*/
      e[58] + 1}, ${/*fmt*/
      e[24](
        /*s*/
        e[62].start
      )} to ${/*fmt*/
      e[24](
        /*s*/
        e[62].end
      )} seconds`), U(
        l,
        "alt",
        /*i*/
        e[58] % 2 === 1
      ), U(
        l,
        "clickable",
        /*value*/
        e[0].selectable
      );
    },
    m(S, w) {
      V(S, l, w), D && D.m(l, null), g(l, n), b || (m = ve(l, "click", B), b = !0);
    },
    p(S, w) {
      e = S, /*s*/
      e[62].order != null && /*w*/
      e[64] >= 16 ? D ? D.p(e, w) : (D = Te(e), D.c(), D.m(l, n)) : D && (D.d(1), D = null), w[0] & /*sections*/
      1024 && t !== (t = "cell " + /*st*/
      e[63] + " svelte-ccfote") && u(l, "class", t), w[0] & /*sections*/
      1024 && s !== (s = /*span*/
      e[23](
        /*s*/
        e[62].start,
        /*s*/
        e[62].end
      )) && u(l, "style", s), w[0] & /*value*/
      1 && i !== (i = /*value*/
      e[0].selectable ? 0 : -1) && u(l, "tabindex", i), w[0] & /*value*/
      1 && a !== (a = !/*value*/
      e[0].selectable) && u(l, "aria-disabled", a), w[0] & /*sections*/
      1024 && f !== (f = `${/*fmt*/
      e[24](
        /*s*/
        e[62].start
      )}–${/*fmt*/
      e[24](
        /*s*/
        e[62].end
      )} s${/*s*/
      e[62].order != null ? `, generated #${/*s*/
      e[62].order}` : ""}${/*st*/
      e[63] !== "normal" ? ` (${/*st*/
      e[63]})` : ""}`) && u(l, "title", f), w[0] & /*sections*/
      1024 && v !== (v = `Section ${/*i*/
      e[58] + 1}, ${/*fmt*/
      e[24](
        /*s*/
        e[62].start
      )} to ${/*fmt*/
      e[24](
        /*s*/
        e[62].end
      )} seconds`) && u(l, "aria-label", v), w[0] & /*sections*/
      1024 && U(
        l,
        "alt",
        /*i*/
        e[58] % 2 === 1
      ), w[0] & /*sections, value*/
      1025 && U(
        l,
        "clickable",
        /*value*/
        e[0].selectable
      );
    },
    d(S) {
      S && h(l), D && D.d(), b = !1, m();
    }
  };
}
function Fe(e) {
  let l, n = "No prompt";
  return {
    c() {
      l = E("span"), l.textContent = n, this.h();
    },
    l(t) {
      l = y(t, "SPAN", { class: !0, "data-svelte-h": !0 }), me(l) !== "svelte-e7elkq" && (l.textContent = n), this.h();
    },
    h() {
      u(l, "class", "empty-note svelte-ccfote");
    },
    m(t, s) {
      V(t, l, s);
    },
    d(t) {
      t && h(l);
    }
  };
}
function ze(e) {
  let l, n, t = (
    /*p*/
    e[59].text + ""
  ), s, i, a;
  return {
    c() {
      l = E("div"), n = E("span"), s = Q(t), this.h();
    },
    l(f) {
      l = y(f, "DIV", { class: !0, style: !0, title: !0 });
      var v = I(l);
      n = y(v, "SPAN", { class: !0 });
      var b = I(n);
      s = J(b, t), b.forEach(h), v.forEach(h), this.h();
    },
    h() {
      u(n, "class", "txt svelte-ccfote"), u(l, "class", "bar prompt svelte-ccfote"), u(l, "style", i = /*span*/
      e[23](
        /*p*/
        e[59].start,
        /*p*/
        e[59].end
      )), u(l, "title", a = /*p*/
      e[59].text), U(
        l,
        "alt",
        /*i*/
        e[58] % 2 === 1
      );
    },
    m(f, v) {
      V(f, l, v), g(l, n), g(n, s);
    },
    p(f, v) {
      v[0] & /*prompts*/
      2097152 && t !== (t = /*p*/
      f[59].text + "") && ee(s, t), v[0] & /*prompts*/
      2097152 && i !== (i = /*span*/
      f[23](
        /*p*/
        f[59].start,
        /*p*/
        f[59].end
      )) && u(l, "style", i), v[0] & /*prompts*/
      2097152 && a !== (a = /*p*/
      f[59].text) && u(l, "title", a);
    },
    d(f) {
      f && h(l);
    }
  };
}
function qe(e) {
  let l, n = Z(
    /*prompts*/
    e[21].slice(1)
  ), t = [];
  for (let s = 0; s < n.length; s += 1)
    t[s] = Ke(Me(e, n, s));
  return {
    c() {
      for (let s = 0; s < t.length; s += 1)
        t[s].c();
      l = De();
    },
    l(s) {
      for (let i = 0; i < t.length; i += 1)
        t[i].l(s);
      l = De();
    },
    m(s, i) {
      for (let a = 0; a < t.length; a += 1)
        t[a] && t[a].m(s, i);
      V(s, l, i);
    },
    p(s, i) {
      if (i[0] & /*span, prompts, blend, fmt*/
      27787264) {
        n = Z(
          /*prompts*/
          s[21].slice(1)
        );
        let a;
        for (a = 0; a < n.length; a += 1) {
          const f = Me(s, n, a);
          t[a] ? t[a].p(f, i) : (t[a] = Ke(f), t[a].c(), t[a].m(l.parentNode, l));
        }
        for (; a < t.length; a += 1)
          t[a].d(1);
        t.length = n.length;
      }
    },
    d(s) {
      s && h(l), he(t, s);
    }
  };
}
function Ke(e) {
  let l, n, t;
  return {
    c() {
      l = E("div"), this.h();
    },
    l(s) {
      l = y(s, "DIV", { class: !0, style: !0, title: !0 }), I(l).forEach(h), this.h();
    },
    h() {
      u(l, "class", "blend svelte-ccfote"), u(l, "style", n = /*span*/
      e[23](
        /*p*/
        e[59].start - /*blend*/
        e[19] / 2,
        /*p*/
        e[59].start + /*blend*/
        e[19] / 2
      )), u(l, "title", t = `Blend ${/*fmt*/
      e[24](
        /*blend*/
        e[19]
      )} s`), U(
        l,
        "rev",
        /*i*/
        e[58] % 2 === 1
      );
    },
    m(s, i) {
      V(s, l, i);
    },
    p(s, i) {
      i[0] & /*prompts, blend*/
      2621440 && n !== (n = /*span*/
      s[23](
        /*p*/
        s[59].start - /*blend*/
        s[19] / 2,
        /*p*/
        s[59].start + /*blend*/
        s[19] / 2
      )) && u(l, "style", n), i[0] & /*blend*/
      524288 && t !== (t = `Blend ${/*fmt*/
      s[24](
        /*blend*/
        s[19]
      )} s`) && u(l, "title", t);
    },
    d(s) {
      s && h(l);
    }
  };
}
function Re(e) {
  let l, n, t, s, i, a;
  return {
    c() {
      l = E("div"), t = O(), s = E("div"), i = E("span"), this.h();
    },
    l(f) {
      l = y(f, "DIV", { class: !0, style: !0 }), I(l).forEach(h), t = j(f), s = y(f, "DIV", { class: !0, title: !0 });
      var v = I(s);
      i = y(v, "SPAN", { class: !0 }), I(i).forEach(h), v.forEach(h), this.h();
    },
    h() {
      u(l, "class", "snap-line svelte-ccfote"), u(l, "style", n = /*span*/
      e[23](Math.min(
        /*f*/
        e[54].t,
        /*f*/
        e[54].snapped
      ), Math.max(
        /*f*/
        e[54].t,
        /*f*/
        e[54].snapped
      ))), u(i, "class", "diamond svelte-ccfote"), u(s, "class", "marker ghost svelte-ccfote"), u(s, "title", a = `snaps to ${/*fmt*/
      e[24](
        /*f*/
        e[54].snapped
      )} s`), le(
        s,
        "left",
        /*pct*/
        e[22](
          /*f*/
          e[54].snapped
        )
      );
    },
    m(f, v) {
      V(f, l, v), V(f, t, v), V(f, s, v), g(s, i);
    },
    p(f, v) {
      v[0] & /*frames*/
      32768 && n !== (n = /*span*/
      f[23](Math.min(
        /*f*/
        f[54].t,
        /*f*/
        f[54].snapped
      ), Math.max(
        /*f*/
        f[54].t,
        /*f*/
        f[54].snapped
      ))) && u(l, "style", n), v[0] & /*frames*/
      32768 && a !== (a = `snaps to ${/*fmt*/
      f[24](
        /*f*/
        f[54].snapped
      )} s`) && u(s, "title", a), v[0] & /*frames*/
      32768 && le(
        s,
        "left",
        /*pct*/
        f[22](
          /*f*/
          f[54].snapped
        )
      );
    },
    d(f) {
      f && (h(l), h(t), h(s));
    }
  };
}
function al(e) {
  let l = (
    /*f*/
    (e[54].label ?? "") + ""
  ), n;
  return {
    c() {
      n = Q(l);
    },
    l(t) {
      n = J(t, l);
    },
    m(t, s) {
      V(t, n, s);
    },
    p(t, s) {
      s[0] & /*frames*/
      32768 && l !== (l = /*f*/
      (t[54].label ?? "") + "") && ee(n, l);
    },
    d(t) {
      t && h(n);
    }
  };
}
function ol(e) {
  let l = (
    /*t*/
    e[55].toFixed(2) + ""
  ), n, t;
  return {
    c() {
      n = Q(l), t = Q(" s");
    },
    l(s) {
      n = J(s, l), t = J(s, " s");
    },
    m(s, i) {
      V(s, n, i), V(s, t, i);
    },
    p(s, i) {
      i[0] & /*drag, frames*/
      49152 && l !== (l = /*t*/
      s[55].toFixed(2) + "") && ee(n, l);
    },
    d(s) {
      s && (h(n), h(t));
    }
  };
}
function Ue(e) {
  let l = (
    /*f*/
    e[54].kind === "key" && /*f*/
    e[54].snapped != null && Math.abs(
      /*f*/
      e[54].snapped - /*f*/
      e[54].t
    ) > 0.05 && !/*drag*/
    (e[14] && /*drag*/
    e[14].i === /*i*/
    e[58])
  ), n, t, s, i, a, f, v, b, m, D, B, S, w, c = l && Re(e);
  function M(C, r) {
    return (
      /*drag*/
      C[14] && /*drag*/
      C[14].i === /*i*/
      C[58] ? ol : al
    );
  }
  let X = M(e), A = X(e);
  function H(...C) {
    return (
      /*pointerdown_handler*/
      e[44](
        /*i*/
        e[58],
        ...C
      )
    );
  }
  function fe(...C) {
    return (
      /*keydown_handler*/
      e[45](
        /*i*/
        e[58],
        ...C
      )
    );
  }
  return {
    c() {
      c && c.c(), n = O(), t = E("button"), s = E("span"), i = O(), a = E("span"), A.c(), v = O(), this.h();
    },
    l(C) {
      c && c.l(C), n = j(C), t = y(C, "BUTTON", {
        type: !0,
        class: !0,
        "aria-label": !0,
        title: !0,
        tabindex: !0
      });
      var r = I(t);
      s = y(r, "SPAN", { class: !0 }), I(s).forEach(h), i = j(r), a = y(r, "SPAN", { class: !0 });
      var $ = I(a);
      A.l($), $.forEach(h), v = j(r), r.forEach(h), this.h();
    },
    h() {
      u(s, "class", "diamond svelte-ccfote"), u(a, "class", f = "mlabel " + /*anchor*/
      e[25](
        /*t*/
        e[55]
      ) + " svelte-ccfote"), u(t, "type", "button"), u(t, "class", b = "marker " + /*f*/
      e[54].kind + " svelte-ccfote"), u(t, "aria-label", m = /*frame_label*/
      e[32](
        /*f*/
        e[54]
      )), u(t, "title", D = /*f*/
      e[54].kind === "key" && /*f*/
      e[54].snapped != null && Math.abs(
        /*f*/
        e[54].snapped - /*f*/
        e[54].t
      ) > 0.05 ? `${/*f*/
      e[54].label ?? "Key"} at ${/*fmt*/
      e[24](
        /*f*/
        e[54].t
      )} s, snaps to ${/*fmt*/
      e[24](
        /*f*/
        e[54].snapped
      )} s` : `${/*f*/
      e[54].label ?? /*f*/
      e[54].kind} at ${/*fmt*/
      e[24](
        /*f*/
        e[54].t
      )} s`), u(t, "tabindex", B = /*draggable*/
      e[56] || /*f*/
      e[54].kind !== "key" ? 0 : -1), U(
        t,
        "unset",
        /*f*/
        e[54].set === !1
      ), U(
        t,
        "draggable",
        /*draggable*/
        e[56]
      ), U(
        t,
        "dragging",
        /*drag*/
        e[14] && /*drag*/
        e[14].i === /*i*/
        e[58]
      ), le(
        t,
        "left",
        /*pct*/
        e[22](
          /*t*/
          e[55]
        )
      );
    },
    m(C, r) {
      c && c.m(C, r), V(C, n, r), V(C, t, r), g(t, s), g(t, i), g(t, a), A.m(a, null), g(t, v), S || (w = [
        ve(t, "pointerdown", H),
        ve(
          t,
          "pointermove",
          /*on_move*/
          e[28]
        ),
        ve(
          t,
          "pointerup",
          /*on_up*/
          e[29]
        ),
        ve(
          t,
          "pointercancel",
          /*on_up*/
          e[29]
        ),
        ve(t, "keydown", fe)
      ], S = !0);
    },
    p(C, r) {
      e = C, r[0] & /*frames, drag*/
      49152 && (l = /*f*/
      e[54].kind === "key" && /*f*/
      e[54].snapped != null && Math.abs(
        /*f*/
        e[54].snapped - /*f*/
        e[54].t
      ) > 0.05 && !/*drag*/
      (e[14] && /*drag*/
      e[14].i === /*i*/
      e[58])), l ? c ? c.p(e, r) : (c = Re(e), c.c(), c.m(n.parentNode, n)) : c && (c.d(1), c = null), X === (X = M(e)) && A ? A.p(e, r) : (A.d(1), A = X(e), A && (A.c(), A.m(a, null))), r[0] & /*drag, frames*/
      49152 && f !== (f = "mlabel " + /*anchor*/
      e[25](
        /*t*/
        e[55]
      ) + " svelte-ccfote") && u(a, "class", f), r[0] & /*frames*/
      32768 && b !== (b = "marker " + /*f*/
      e[54].kind + " svelte-ccfote") && u(t, "class", b), r[0] & /*frames*/
      32768 && m !== (m = /*frame_label*/
      e[32](
        /*f*/
        e[54]
      )) && u(t, "aria-label", m), r[0] & /*frames*/
      32768 && D !== (D = /*f*/
      e[54].kind === "key" && /*f*/
      e[54].snapped != null && Math.abs(
        /*f*/
        e[54].snapped - /*f*/
        e[54].t
      ) > 0.05 ? `${/*f*/
      e[54].label ?? "Key"} at ${/*fmt*/
      e[24](
        /*f*/
        e[54].t
      )} s, snaps to ${/*fmt*/
      e[24](
        /*f*/
        e[54].snapped
      )} s` : `${/*f*/
      e[54].label ?? /*f*/
      e[54].kind} at ${/*fmt*/
      e[24](
        /*f*/
        e[54].t
      )} s`) && u(t, "title", D), r[0] & /*editable, frames*/
      98304 && B !== (B = /*draggable*/
      e[56] || /*f*/
      e[54].kind !== "key" ? 0 : -1) && u(t, "tabindex", B), r[0] & /*frames, frames*/
      32768 && U(
        t,
        "unset",
        /*f*/
        e[54].set === !1
      ), r[0] & /*frames, editable, frames*/
      98304 && U(
        t,
        "draggable",
        /*draggable*/
        e[56]
      ), r[0] & /*frames, drag*/
      49152 && U(
        t,
        "dragging",
        /*drag*/
        e[14] && /*drag*/
        e[14].i === /*i*/
        e[58]
      ), r[0] & /*drag, frames*/
      49152 && le(
        t,
        "left",
        /*pct*/
        e[22](
          /*t*/
          e[55]
        )
      );
    },
    d(C) {
      C && (h(n), h(t)), c && c.d(C), A.d(), S = !1, tl(w);
    }
  };
}
function Le(e) {
  let l, n, t, s = (
    /*value*/
    e[0].keyframes_reason + ""
  ), i;
  return {
    c() {
      l = E("div"), n = O(), t = E("div"), i = Q(s), this.h();
    },
    l(a) {
      l = y(a, "DIV", { class: !0 }), I(l).forEach(h), n = j(a), t = y(a, "DIV", { class: !0 });
      var f = I(t);
      i = J(f, s), f.forEach(h), this.h();
    },
    h() {
      u(l, "class", "lane-label svelte-ccfote"), u(t, "class", "note svelte-ccfote");
    },
    m(a, f) {
      V(a, l, f), V(a, n, f), V(a, t, f), g(t, i);
    },
    p(a, f) {
      f[0] & /*value*/
      1 && s !== (s = /*value*/
      a[0].keyframes_reason + "") && ee(i, s);
    },
    d(a) {
      a && (h(l), h(n), h(t));
    }
  };
}
function fl(e) {
  let l = (
    /*ln*/
    (e[51].text ?? "") + ""
  ), n;
  return {
    c() {
      n = Q(l);
    },
    l(t) {
      n = J(t, l);
    },
    m(t, s) {
      V(t, n, s);
    },
    p(t, s) {
      s[0] & /*lanes*/
      1048576 && l !== (l = /*ln*/
      (t[51].text ?? "") + "") && ee(n, l);
    },
    d(t) {
      t && h(n);
    }
  };
}
function rl(e) {
  let l = (
    /*ln*/
    (e[51].reason || "Disabled") + ""
  ), n;
  return {
    c() {
      n = Q(l);
    },
    l(t) {
      n = J(t, l);
    },
    m(t, s) {
      V(t, n, s);
    },
    p(t, s) {
      s[0] & /*lanes*/
      1048576 && l !== (l = /*ln*/
      (t[51].reason || "Disabled") + "") && ee(n, l);
    },
    d(t) {
      t && h(n);
    }
  };
}
function We(e) {
  let l, n = (
    /*ln*/
    e[51].label + ""
  ), t, s, i, a, f, v, b, m, D;
  function B(c, M) {
    return (
      /*ln*/
      c[51].enabled === !1 ? rl : fl
    );
  }
  let S = B(e), w = S(e);
  return {
    c() {
      l = E("div"), t = Q(n), i = O(), a = E("div"), f = E("div"), v = E("span"), w.c(), D = O(), this.h();
    },
    l(c) {
      l = y(c, "DIV", { class: !0, title: !0 });
      var M = I(l);
      t = J(M, n), M.forEach(h), i = j(c), a = y(c, "DIV", { class: !0 });
      var X = I(a);
      f = y(X, "DIV", { class: !0, style: !0, title: !0 });
      var A = I(f);
      v = y(A, "SPAN", { class: !0 });
      var H = I(v);
      w.l(H), H.forEach(h), A.forEach(h), D = j(X), X.forEach(h), this.h();
    },
    h() {
      u(l, "class", "lane-label svelte-ccfote"), u(l, "title", s = /*ln*/
      e[51].label), u(v, "class", "txt svelte-ccfote"), u(f, "class", "bar extra svelte-ccfote"), u(f, "style", b = /*span*/
      e[23](
        /*ln*/
        e[51].start,
        /*ln*/
        e[51].end
      )), u(f, "title", m = /*ln*/
      e[51].enabled === !1 ? `${/*ln*/
      e[51].text ?? ""} (${/*ln*/
      e[51].reason ?? "disabled"})` : (
        /*ln*/
        e[51].text
      )), U(
        f,
        "off",
        /*ln*/
        e[51].enabled === !1
      ), u(a, "class", "track lane svelte-ccfote");
    },
    m(c, M) {
      V(c, l, M), g(l, t), V(c, i, M), V(c, a, M), g(a, f), g(f, v), w.m(v, null), g(a, D);
    },
    p(c, M) {
      M[0] & /*lanes*/
      1048576 && n !== (n = /*ln*/
      c[51].label + "") && ee(t, n), M[0] & /*lanes*/
      1048576 && s !== (s = /*ln*/
      c[51].label) && u(l, "title", s), S === (S = B(c)) && w ? w.p(c, M) : (w.d(1), w = S(c), w && (w.c(), w.m(v, null))), M[0] & /*lanes*/
      1048576 && b !== (b = /*span*/
      c[23](
        /*ln*/
        c[51].start,
        /*ln*/
        c[51].end
      )) && u(f, "style", b), M[0] & /*lanes*/
      1048576 && m !== (m = /*ln*/
      c[51].enabled === !1 ? `${/*ln*/
      c[51].text ?? ""} (${/*ln*/
      c[51].reason ?? "disabled"})` : (
        /*ln*/
        c[51].text
      )) && u(f, "title", m), M[0] & /*lanes*/
      1048576 && U(
        f,
        "off",
        /*ln*/
        c[51].enabled === !1
      );
    },
    d(c) {
      c && (h(l), h(i), h(a)), w.d();
    }
  };
}
function _l(e) {
  let l, n, t, s, i = (
    /*show_label*/
    (e[5] && /*label*/
    e[4] || /*duration*/
    e[11] && /*caption*/
    e[18]) && Ae(e)
  );
  function a(b, m) {
    return (
      /*duration*/
      b[11] ? sl : il
    );
  }
  let f = a(e), v = f(e);
  return {
    c() {
      l = E("div"), i && i.c(), n = O(), v.c(), this.h();
    },
    l(b) {
      l = y(b, "DIV", { id: !0, class: !0 });
      var m = I(l);
      i && i.l(m), n = j(m), v.l(m), m.forEach(h), this.h();
    },
    h() {
      u(l, "id", t = /*elem_id*/
      e[1] || null), u(l, "class", s = "fps-timeline " + /*elem_classes*/
      e[2].join(" ") + " svelte-ccfote"), U(l, "hidden", !/*visible*/
      e[3]), U(
        l,
        "boxed",
        /*container*/
        e[8]
      ), le(
        l,
        "flex-grow",
        /*scale*/
        e[6]
      ), le(
        l,
        "min-width",
        /*min_width*/
        e[7] ? `${/*min_width*/
        e[7]}px` : null
      );
    },
    m(b, m) {
      V(b, l, m), i && i.m(l, null), g(l, n), v.m(l, null);
    },
    p(b, m) {
      /*show_label*/
      b[5] && /*label*/
      b[4] || /*duration*/
      b[11] && /*caption*/
      b[18] ? i ? i.p(b, m) : (i = Ae(b), i.c(), i.m(l, n)) : i && (i.d(1), i = null), f === (f = a(b)) && v ? v.p(b, m) : (v.d(1), v = f(b), v && (v.c(), v.m(l, null))), m[0] & /*elem_id*/
      2 && t !== (t = /*elem_id*/
      b[1] || null) && u(l, "id", t), m[0] & /*elem_classes*/
      4 && s !== (s = "fps-timeline " + /*elem_classes*/
      b[2].join(" ") + " svelte-ccfote") && u(l, "class", s), m[0] & /*elem_classes, visible*/
      12 && U(l, "hidden", !/*visible*/
      b[3]), m[0] & /*elem_classes, container*/
      260 && U(
        l,
        "boxed",
        /*container*/
        b[8]
      ), m[0] & /*scale*/
      64 && le(
        l,
        "flex-grow",
        /*scale*/
        b[6]
      ), m[0] & /*min_width*/
      128 && le(
        l,
        "min-width",
        /*min_width*/
        b[7] ? `${/*min_width*/
        b[7]}px` : null
      );
    },
    i: pe,
    o: pe,
    d(b) {
      b && h(l), i && i.d(), v.d();
    }
  };
}
function ul(e, l, n) {
  let t, s, i, a, f, v, b, m, D, B;
  var S, w, c, M, X;
  let { gradio: A } = l, { elem_id: H = "" } = l, { elem_classes: fe = [] } = l, { visible: C = !0 } = l, { value: r = null } = l, { label: $ = "" } = l, { show_label: ue = !0 } = l, { interactive: re = !0 } = l, { loading_status: _e = void 0 } = l, { scale: te = null } = l, { min_width: F = void 0 } = l, { root: ne = "" } = l, { container: z = !0 } = l, q = 600, x, N = null;
  const L = (d) => `${Math.min(Math.max(d, 0), t) / t * 100}%`, se = (d, p) => `left:${L(d)};width:${(Math.min(p, t) - Math.max(d, 0)) / t * 100}%`, K = (d) => `${(Math.round(d * 10) / 10).toFixed(1)}`, T = (d) => Math.round(d * 10) / 10;
  function ie(d, p, G) {
    if (!p) return [];
    const oe = /* @__PURE__ */ new Set([0, p]);
    for (const Y of d)
      oe.add(T(Y.start)), oe.add(T(Y.end));
    const ke = [...oe].filter((Y) => Y >= 0 && Y <= p).sort((Y, be) => Y - be), we = 34, ce = [];
    let ye = -1 / 0;
    for (const Y of ke) {
      const be = Y / p * G, Ee = Y === p;
      if (Ee)
        for (; ce.length > 1 && be - ce[ce.length - 1].t / p * G < we; ) ce.pop();
      else if (be - ye < we) continue;
      ce.push({
        t: Y,
        anchor: Y === 0 ? "left" : Ee ? "right" : "mid"
      }), ye = be;
    }
    return ce;
  }
  function W(d) {
    const p = d / t;
    return p < 0.03 ? "left" : p > 0.97 ? "right" : "mid";
  }
  function _(d, p) {
    var G;
    return (r == null ? void 0 : r.selected_section) === p ? "selected" : (G = d.state) !== null && G !== void 0 ? G : "normal";
  }
  function k(d, p) {
    if (!r) return;
    const G = a.map((oe, ke) => ke === d ? Object.assign(Object.assign({}, oe), { t: T(p) }) : oe);
    n(0, r = Object.assign(Object.assign({}, r), { frames: G })), A.dispatch("change"), A.dispatch("input");
  }
  function o(d) {
    const p = x.getBoundingClientRect(), G = (d - p.left) / p.width * t;
    return Math.min(Math.max(G, 0.1), t - 0.1);
  }
  function R(d, p) {
    !m || a[p].kind !== "key" || (d.currentTarget.setPointerCapture(d.pointerId), n(14, N = { i: p, t: a[p].t, moved: !1 }), d.preventDefault());
  }
  function ae(d) {
    N && n(14, N = Object.assign(Object.assign({}, N), { t: o(d.clientX), moved: !0 }));
  }
  function de() {
    if (!N) return;
    const { i: d, t: p, moved: G } = N;
    n(14, N = null), G && T(p) !== a[d].t && k(d, p);
  }
  function P(d, p) {
    if (!m || a[p].kind !== "key") return;
    const G = d.key === "ArrowRight" ? 0.1 : d.key === "ArrowLeft" ? -0.1 : 0;
    if (!G) return;
    d.preventDefault();
    const oe = Math.min(Math.max(a[p].t + G, 0.1), t - 0.1);
    k(p, oe);
  }
  function ge(d) {
    if (!(r != null && r.selectable)) return;
    const p = s[d];
    n(0, r = Object.assign(Object.assign({}, r), { selected_section: d })), A.dispatch("select", {
      index: d,
      value: {
        start: p.start,
        end: p.end,
        order: p.order
      }
    });
  }
  function Xe(d) {
    var p;
    return `${(p = d.label) !== null && p !== void 0 ? p : d.kind} keyframe at ${K(d.t)} seconds${d.set === !1 ? ", not set" : ""}`;
  }
  function Ge() {
    q = this.clientWidth, n(9, q);
  }
  const He = (d) => ge(d), Je = (d, p) => R(p, d), Qe = (d, p) => P(p, d);
  function Ye(d) {
    el[d ? "unshift" : "push"](() => {
      x = d, n(13, x);
    });
  }
  return e.$$set = (d) => {
    "gradio" in d && n(33, A = d.gradio), "elem_id" in d && n(1, H = d.elem_id), "elem_classes" in d && n(2, fe = d.elem_classes), "visible" in d && n(3, C = d.visible), "value" in d && n(0, r = d.value), "label" in d && n(4, $ = d.label), "show_label" in d && n(5, ue = d.show_label), "interactive" in d && n(34, re = d.interactive), "loading_status" in d && n(35, _e = d.loading_status), "scale" in d && n(6, te = d.scale), "min_width" in d && n(7, F = d.min_width), "root" in d && n(36, ne = d.root), "container" in d && n(8, z = d.container);
  }, e.$$.update = () => {
    e.$$.dirty[0] & /*value*/
    1 && n(11, t = r && r.duration > 0 ? r.duration : 0), e.$$.dirty[0] & /*value*/
    1 | e.$$.dirty[1] & /*_a*/
    64 && n(10, s = n(37, S = r == null ? void 0 : r.sections) !== null && S !== void 0 ? S : []), e.$$.dirty[0] & /*value*/
    1 | e.$$.dirty[1] & /*_b*/
    128 && n(21, i = n(38, w = r == null ? void 0 : r.prompts) !== null && w !== void 0 ? w : []), e.$$.dirty[0] & /*value*/
    1 | e.$$.dirty[1] & /*_c*/
    256 && n(15, a = n(39, c = r == null ? void 0 : r.frames) !== null && c !== void 0 ? c : []), e.$$.dirty[0] & /*value*/
    1 | e.$$.dirty[1] & /*_d*/
    512 && n(20, f = n(40, M = r == null ? void 0 : r.lanes) !== null && M !== void 0 ? M : []), e.$$.dirty[0] & /*value*/
    1 | e.$$.dirty[1] & /*_e*/
    1024 && n(19, v = Math.max(0, n(41, X = r == null ? void 0 : r.blend) !== null && X !== void 0 ? X : 0)), e.$$.dirty[0] & /*value*/
    1 && n(12, b = (r == null ? void 0 : r.keyframes_enabled) !== !1), e.$$.dirty[0] & /*keys_enabled*/
    4096 | e.$$.dirty[1] & /*interactive*/
    8 && n(16, m = re !== !1 && b), e.$$.dirty[0] & /*value*/
    1 && n(18, D = (r == null ? void 0 : r.direction) === "backward" ? "generated end → start" : (r == null ? void 0 : r.direction) === "forward" ? "generated start → end" : ""), e.$$.dirty[0] & /*sections, duration, track_width*/
    3584 && n(17, B = ie(s, t, q));
  }, [
    r,
    H,
    fe,
    C,
    $,
    ue,
    te,
    F,
    z,
    q,
    s,
    t,
    b,
    x,
    N,
    a,
    m,
    B,
    D,
    v,
    f,
    i,
    L,
    se,
    K,
    W,
    _,
    R,
    ae,
    de,
    P,
    ge,
    Xe,
    A,
    re,
    _e,
    ne,
    S,
    w,
    c,
    M,
    X,
    Ge,
    He,
    Je,
    Qe,
    Ye
  ];
}
class dl extends Ze {
  constructor(l) {
    super(), ll(
      this,
      l,
      ul,
      _l,
      nl,
      {
        gradio: 33,
        elem_id: 1,
        elem_classes: 2,
        visible: 3,
        value: 0,
        label: 4,
        show_label: 5,
        interactive: 34,
        loading_status: 35,
        scale: 6,
        min_width: 7,
        root: 36,
        container: 8
      },
      null,
      [-1, -1, -1]
    );
  }
}
export {
  dl as default
};
