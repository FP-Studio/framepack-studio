const {
  SvelteComponent: _,
  append_hydration: c,
  attr: f,
  children: h,
  claim_element: m,
  claim_text: v,
  detach: o,
  element: g,
  init: y,
  insert_hydration: b,
  noop: u,
  safe_not_equal: q,
  set_data: w,
  text: E,
  toggle_class: s
} = window.__gradio__svelte__internal;
function F(n) {
  var d;
  let e, a = (
    /*value*/
    (d = n[0]) != null && d.duration ? `${/*value*/
    n[0].duration.toFixed(1)} s timeline` : ""
  ), i;
  return {
    c() {
      e = g("div"), i = E(a), this.h();
    },
    l(l) {
      e = m(l, "DIV", { class: !0 });
      var t = h(e);
      i = v(t, a), t.forEach(o), this.h();
    },
    h() {
      f(e, "class", "svelte-1r0kqnm"), s(
        e,
        "table",
        /*type*/
        n[1] === "table"
      ), s(
        e,
        "gallery",
        /*type*/
        n[1] === "gallery"
      ), s(
        e,
        "selected",
        /*selected*/
        n[2]
      );
    },
    m(l, t) {
      b(l, e, t), c(e, i);
    },
    p(l, [t]) {
      var r;
      t & /*value*/
      1 && a !== (a = /*value*/
      (r = l[0]) != null && r.duration ? `${/*value*/
      l[0].duration.toFixed(1)} s timeline` : "") && w(i, a), t & /*type*/
      2 && s(
        e,
        "table",
        /*type*/
        l[1] === "table"
      ), t & /*type*/
      2 && s(
        e,
        "gallery",
        /*type*/
        l[1] === "gallery"
      ), t & /*selected*/
      4 && s(
        e,
        "selected",
        /*selected*/
        l[2]
      );
    },
    i: u,
    o: u,
    d(l) {
      l && o(e);
    }
  };
}
function k(n, e, a) {
  let { value: i } = e, { type: d } = e, { selected: l = !1 } = e;
  return n.$$set = (t) => {
    "value" in t && a(0, i = t.value), "type" in t && a(1, d = t.type), "selected" in t && a(2, l = t.selected);
  }, [i, d, l];
}
class C extends _ {
  constructor(e) {
    super(), y(this, e, k, F, q, { value: 0, type: 1, selected: 2 });
  }
}
export {
  C as default
};
