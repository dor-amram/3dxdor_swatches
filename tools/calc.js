// 3DxDor calc core — shared by the page and the node diff test. Weights in grams.
var Calc = (function () {
  function n(x) { return typeof x === 'number' && isFinite(x) ? x : null; }
  function z(x) { return n(x) === null ? 0 : x; }
  function tare(r) {
    if (n(r.tare) !== null) return r.tare;
    if (n(r.new_g) !== null && n(r.new_n) !== null) return r.new_g - r.new_n;
    return null;
  }
  // Remaining net filament [g]
  function remN(r) {
    if (r.status === 'finished') return 0;
    if (n(r.rem_n) !== null) return r.rem_n; // manual override
    if (r.status === 'sealed' || r.status === 'awaiting') return n(r.new_n);
    var t = tare(r);
    if (n(r.rem_g) !== null && t !== null) return r.rem_g - t;
    return null; // unmeasured
  }
  // Price per kg in paid currency, incl. shipping
  function perKgPaid(r) {
    if (n(r.cost) === null || !n(r.new_n)) return null;
    return (r.cost + z(r.ship)) / (r.new_n / 1000);
  }
  // Net cost per kg in NIS (after VAT reclaim)
  function perKgNIS(r) {
    var p = perKgPaid(r);
    if (p === null) return null;
    var fx = r.cur === 'ILS' ? 1 : n(r.fx);
    if (fx === null) return null;
    return p * fx / (1 + z(r.vat) / 100);
  }
  function activeRoll(f) {
    var rs = f.rolls || [];
    for (var i = 0; i < rs.length; i++) if (rs[i].id === f.active) return rs[i];
    return rs[0] || null;
  }
  function spares(f) {
    return (f.rolls || []).filter(function (r) { return r.id !== f.active && (r.status === 'sealed' || r.status === 'awaiting'); });
  }
  // Pricing (sheet formula, Sept 2026 validated). p = frozen params snapshot.
  function job(j, p) {
    var m = p.machine, qty = z(j.qty), succ = z(j.succ), L = z(j.hours);
    var matcost = z(j.mat_nis_kg) * z(j.mat_g) / 1000;
    var mall = (m.cost - m.sale) / m.hours * L;
    var call = m.cons / m.life * L;
    var elec = p.elec * L * z(j.ef) * m.kw;
    var labor = L * p.print * qty + (z(j.setup) * p.setup + z(j.slice) * p.slice + z(j.model) * p.model + z(j.post) * p.post * qty) / 60;
    var total = ((z(j.cons) * qty) + ((matcost + mall + call + elec) * qty + labor) * (succ ? 100 / succ : NaN)) * (1 + p.markup / 100) * z(j.adj) * (1 + p.vat / 100);
    var quote = n(j.quote) !== null ? j.quote : total;
    var cost = matcost + z(j.cons) + mall + call + elec;
    var profit = quote / (1 + p.vat / 100) - z(j.cons) - call - mall - elec - matcost;
    return { matcost: matcost, mall: mall, call: call, elec: elec, labor: labor, total: total, quote: quote, cost: cost, profit: profit };
  }
  function snapshot(params, printer) {
    var c = params.current || params;
    return { print: c.print, setup: c.setup, slice: c.slice, model: c.model, post: c.post, elec: c.elec, vat: c.vat, markup: c.markup, machine: c.machines[printer] };
  }
  return { tare: tare, remN: remN, perKgPaid: perKgPaid, perKgNIS: perKgNIS, activeRoll: activeRoll, spares: spares, job: job, snapshot: snapshot };
})();
if (typeof module !== 'undefined') module.exports = Calc;
