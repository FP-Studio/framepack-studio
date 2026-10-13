const {
  SvelteComponent: c,
  append_hydration: v,
  attr: h,
  children: g,
  claim_element: m,
  claim_text: y,
  detach: u,
  element: w,
  init: b,
  insert_hydration: q,
  noop: f,
  safe_not_equal: E,
  set_data: k,
  text: C,
  toggle_class: s
} = window.__gradio__svelte__internal;
function D(n) {
  let e, a = (
    /*n*/
    n[2] ? `${/*n*/
    n[2]} ${/*n*/
    n[2] === 1 ? "arrow" : "arrows"}` : ""
  ), r;
  return {
    c() {
      e = w("div"), r = C(a), this.h();
    },
    l(l) {
      e = m(l, "DIV", { class: !0 });
      var t = g(e);
      r = y(t, a), t.forEach(u), this.h();
    },
    h() {
      h(e, "class", "svelte-1r0kqnm"), s(
        e,
        "table",
        /*type*/
        n[0] === "table"
      ), s(
        e,
        "gallery",
        /*type*/
        n[0] === "gallery"
      ), s(
        e,
        "selected",
        /*selected*/
        n[1]
      );
    },
    m(l, t) {
      q(l, e, t), v(e, r);
    },
    p(l, [t]) {
      t & /*n*/
      4 && a !== (a = /*n*/
      l[2] ? `${/*n*/
      l[2]} ${/*n*/
      l[2] === 1 ? "arrow" : "arrows"}` : "") && k(r, a), t & /*type*/
      1 && s(
        e,
        "table",
        /*type*/
        l[0] === "table"
      ), t & /*type*/
      1 && s(
        e,
        "gallery",
        /*type*/
        l[0] === "gallery"
      ), t & /*selected*/
      2 && s(
        e,
        "selected",
        /*selected*/
        l[1]
      );
    },
    i: f,
    o: f,
    d(l) {
      l && u(e);
    }
  };
}
function I(n, e, a) {
  let r;
  var l, t;
  let { value: o } = e, { type: d } = e, { selected: _ = !1 } = e;
  return n.$$set = (i) => {
    "value" in i && a(3, o = i.value), "type" in i && a(0, d = i.type), "selected" in i && a(1, _ = i.selected);
  }, n.$$.update = () => {
    n.$$.dirty & /*value, _a, _b*/
    56 && a(2, r = a(5, t = a(4, l = o == null ? void 0 : o.arrows) === null || l === void 0 ? void 0 : l.length) !== null && t !== void 0 ? t : 0);
  }, [d, _, r, o, l, t];
}
class S extends c {
  constructor(e) {
    super(), b(this, e, I, D, E, { value: 3, type: 0, selected: 1 });
  }
}
export {
  S as default
};
