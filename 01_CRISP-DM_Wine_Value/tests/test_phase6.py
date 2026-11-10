import numpy as np
import pytest
import pandas as pd

from winevalue import config, pilot


def _pilot(n=400, shift=None, seed=0, n_sources=4, good=True):
    """Synthetic pilot: a good model (estimate close to the score, ranker ordered by score) unless ``good`` is False."""
    rng = np.random.default_rng(seed)
    y = rng.integers(84, 95, n).astype(float)
    src = np.array([f"s{i % n_sources}" for i in range(n)])
    sel = y + rng.normal(0, 0.8, n)
    if shift:
        for s, v in shift.items():
            sel[src == s] += v
    rank = y + rng.normal(0, 0.5, n) if good else rng.random(n)
    return pd.DataFrame({"points": y, "sel": sel, "base": np.full(n, y.mean()), "rank": rank,
                         "rule: price (pricier first)": rng.random(n), "winery_key": [f"w{i % 300}" for i in range(n)],
                         "source": src, "country": np.where(np.arange(n) % 2, "A", "B"), "order": np.arange(1, n + 1)})


def test_gate_and_decision_follow_option_f():
    g = pilot.gate(_pilot(), n_boot=100)
    assert g["BO1 passes"] and g["BO2 passes"]
    assert pilot.decision(g) == "deploy shortlist and show score band internally"
    bad_band = pilot.gate(_pilot().assign(sel=lambda d: d["sel"] + 4), n_boot=100)
    assert bad_band["BO1 passes"] and not bad_band["BO2 passes"]
    assert pilot.decision(bad_band) == "deploy shortlist only (band not shown)"
    bad_short = pilot.gate(_pilot(good=False), n_boot=100)
    assert bad_short["BO2 passes"] and not bad_short["BO1 passes"]
    assert pilot.decision(bad_short).startswith("deploy nothing")


def test_check_units_pools_small_sources_and_adds_countries():
    d = _pilot(n=200, n_sources=8)            # 25 wines per source: all pooled
    u = pilot.check_units(d)
    assert ("source", pilot.POOLED) in u and len(u[("source", pilot.POOLED)]) == 200
    assert {("country", "A"), ("country", "B"), ("pilot", "all wines")} <= set(u)
    assert not any(k[0] == "source" and k[1] != pilot.POOLED for k in u)


def test_band_withdrawn_only_for_the_shifted_source_and_gate_keeps_all_wines():
    d = _pilot(shift={"s0": 2.5})
    r = pilot.run_protocol(d, n_boot=100)
    assert ("source", "s0") in r["band withdrawn"]
    assert not any(k == ("source", s) for k in r["band withdrawn"] for s in ("s1", "s2", "s3"))
    assert r["gate"]["wines"] == len(d)        # the gate is computed on every pilot wine
    assert r["meets source minimum"] and r["sources with enough wines"] == 4


def test_shortlist_pause_needs_enough_wines():
    d = _pilot(good=False)
    assert not pilot.shortlist_check(d.iloc[: config.PILOT_PAUSE_MIN_WINES - 1])["checked"]
    assert pilot.shortlist_check(d.iloc[: config.PILOT_PAUSE_MIN_WINES], n_boot=50)["checked"]


def test_source_intercept_removes_a_constant_offset():
    d = _pilot(shift={"s0": 2.0}, n_sources=2)
    t = pilot.source_intercept(d).set_index("source")
    assert abs(t.loc["s0", "intercept (first wines)"] - 2.0) < 0.4
    assert t.loc["s0", "gain adjusted (pp)"] > t.loc["s0", "gain unadjusted (pp)"]


def test_choose_pause_min_wines_takes_the_smallest_safe_size():
    rates = {"a": pd.DataFrame({"wines": [100, 200, 300], "pause if lift < 1.0": [0.10, 0.04, 0.0]}),
             "b": pd.DataFrame({"wines": [100, 200, 300], "pause if lift < 1.0": [0.02, 0.06, 0.01]})}
    assert pilot.choose_pause_min_wines(rates, max_rate=0.05) == 300
    assert pilot.choose_pause_min_wines(rates, max_rate=0.0) is None


def test_prepare_new_derives_model_inputs_like_prepare():
    from winevalue.production import prepare_new
    d = prepare_new(pd.DataFrame([{"note": "Crisp apple and lemon. 92 points.", "country": "US", "province": "California Other",
                                   "variety": "Pinot Grigio", "title": "Acme 2015 Reserve Pinot Grigio (Napa)", "winery": "Acme",
                                   "price": 18, "designation": "Reserve"}]))
    r = d.iloc[0]
    assert r["province_model"] == "Unknown province" and r["grape"] == "Pinot Gris" and r["label_differs"]
    assert r["colour"] == "white" and r["vintage"] == 2015 and not r["is_nonvintage"]
    assert r["has_designation"] and not r["has_region_1"] and r["in_value_pool"]
    assert "92" not in r["note"]                       # scores stripped from the model text (R-2)


def test_verdict_uses_the_price_free_estimate_and_the_price_bar():
    from winevalue.production import ValueFinder
    vf = ValueFinder(*([None] * 3), 2.67, *([None] * 6))
    assert vf.verdict(93.0, 20.0).startswith("Likely")
    assert vf.verdict(90.5, 20.0).startswith("Probable")
    assert vf.verdict(88.0, 20.0).startswith("Long shot")
    assert vf.verdict(86.0, 20.0).startswith("Unlikely")
    assert vf.verdict(93.0, 40.0).startswith("Above")
    assert vf.verdict(93.0, float("nan")).startswith("No price")
    assert ValueFinder.tier(0.05, True).startswith("Above the development 90th") and ValueFinder.tier(0.15, True).startswith("Above the development 80th")
    assert ValueFinder.tier(0.5, True).startswith("Below") and ValueFinder.tier(0.05, False).startswith("Not")


def _artifact_paths(tmp_path, monkeypatch):
    from winevalue import artifacts
    m, man = tmp_path / "vf.joblib", tmp_path / "manifest.json"
    monkeypatch.setattr(artifacts, "MODEL_PATH", m)
    monkeypatch.setattr(artifacts, "MANIFEST_PATH", man)
    return artifacts, m, man


def test_artifact_integrity_check_refuses_a_changed_file(tmp_path, monkeypatch):
    import joblib
    artifacts, m, man = _artifact_paths(tmp_path, monkeypatch)
    joblib.dump({"x": 1}, m)
    good = {"sha1": artifacts.sha1(m), "lockbox reproduction (max abs difference)": {k: 0.0 for k in artifacts.REPRO_KEYS}}
    import json
    man.write_text(json.dumps(good))
    assert artifacts.load_value_finder() == {"x": 1}
    joblib.dump({"x": 2}, m)
    with pytest.raises(RuntimeError, match="SHA-1"):
        artifacts.load_value_finder()


def test_serving_refuses_a_missing_manifest_or_an_unchecked_rebuild(tmp_path, monkeypatch):
    import json
    import joblib
    artifacts, m, man = _artifact_paths(tmp_path, monkeypatch)
    joblib.dump({"x": 1}, m)
    with pytest.raises(RuntimeError, match="missing"):            # no manifest: refuse, never rebuild silently
        artifacts.load_value_finder()
    man.write_text(json.dumps({"sha1": artifacts.sha1(m), "lockbox reproduction (max abs difference)": None}))
    with pytest.raises(RuntimeError, match="reproduction"):
        artifacts.load_value_finder()
    man.write_text(json.dumps({"sha1": artifacts.sha1(m), "lockbox reproduction (max abs difference)": {"ridge": 0.3}}))
    with pytest.raises(RuntimeError, match="reproduction"):
        artifacts.load_value_finder()
    full = {k: 0.0 for k in artifacts.REPRO_KEYS}
    for bad in ({"ridge": 0.0}, {**full, "P(90+)": float("nan")}, {**full, "ridge": float("inf")}, {**full, "ridge": -1.0}):
        man.write_text(json.dumps({"sha1": artifacts.sha1(m), "lockbox reproduction (max abs difference)": bad}))
        with pytest.raises(RuntimeError, match="reproduction"):   # partial, NaN, infinite or negative records fail
            artifacts.load_value_finder()
    man.write_text(json.dumps({"sha1": artifacts.sha1(m), "lockbox reproduction (max abs difference)": full}))
    assert artifacts.load_value_finder() == {"x": 1}
    for bad in (pd.Series({"ridge": 0.3}), None, pd.Series({**full, "ridge": float("nan")}), pd.Series({"ridge": 0.0})):
        with pytest.raises(ValueError):                          # and an unreproduced model is never saved
            artifacts.save_value_finder(object(), bad)
    from winevalue.production import _maxdiff
    assert _maxdiff([1.0, 2.0], [1.0, 2.0]) == 0.0
    assert _maxdiff([1.0, np.nan], [1.0, 2.0]) == float("inf")    # a NaN prediction never "reproduces"
    assert _maxdiff([1.0], [1.0, 2.0]) == float("inf") and _maxdiff([np.nan], [np.nan]) == float("inf")


def test_a_futility_pause_ends_the_pilot_with_no_deployment():
    g = pilot.gate(_pilot(), n_boot=100)
    assert pilot.decision(g, paused=True) == pilot.PAUSED
    d = _pilot().assign(rank=lambda t: -t["points"])            # a shortlist that puts the best wines last
    r = pilot.run_protocol(d, n_boot=50)
    assert r["shortlist paused at"] == config.PILOT_PAUSE_MIN_WINES and r["decision"] == pilot.PAUSED


def test_evaluate_raw_waits_for_the_source_minimum(monkeypatch):
    d = _pilot(n_sources=2)                       # 400 wines but only 2 sources
    monkeypatch.setattr(pilot, "from_raw", lambda df, vf: df)
    r = pilot.evaluate_raw(d, vf=None, n_boot=50)
    assert not r["gate"]["final"] and r["gate"]["decision"].startswith("interim") and "note sources" in r["gate"]["decision"]
    r4 = pilot.evaluate_raw(_pilot(n_sources=4), vf=None, n_boot=50)
    assert r4["gate"]["final"] and r4["gate"]["decision"].startswith("deploy shortlist")



def test_band_hidden_matches_names_robustly():
    status = {"withdrawn everywhere": False, "sources": ["Kerin O’Keefe"], "pooled sources": ["Small Importer"], "countries": ["Italy"]}
    d = pd.DataFrame({"source": ["Kerin O'Keefe", " kerin  o’keefe", "small importer", "Big Importer", None, "Big Importer"],
                      "country": ["France", "France", "France", "France", "France", " italy"]})
    assert pilot.band_hidden(d, status).tolist() == [True, True, True, False, False, True]
    assert pilot.band_hidden(d, {**status, "pooled sources": ["unknown"]}).tolist() == [True, True, False, False, True, True]
    assert pilot.band_hidden(d, {"withdrawn everywhere": True}).all() and not pilot.band_hidden(d, None).any()


def test_pooled_withdrawal_names_its_members_and_the_tool_rule_reproduces_the_protocol():
    d = _pilot(n=400, n_sources=12)                     # ~33 wines per source at 400: all pooled
    d["source"] = np.where(np.arange(400) < 100, "big", d["source"])       # one large source
    small = [f"s{i}" for i in range(12)]
    d.loc[d["source"].isin(small[:6]), "sel"] += 2.5    # half the small sources are badly off
    r = pilot.run_protocol(d, n_boot=100)
    assert ("source", pilot.POOLED) in r["band withdrawn"]
    assert set(r["status"]["pooled sources"]) == set(small)          # members at the check where it fired
    used = d.sort_values("order").iloc[: r["wines used"]]
    assert pilot.band_hidden(used, r["status"]).equals(r["band withdrawn rows"])


def test_checks_continue_past_400_until_the_source_minimum_and_stop_at_the_cap():
    d = _pilot(n=config.PILOT_MAX_WINES, n_sources=2)          # never 3 sources
    r = pilot.run_protocol(d, n_boot=50)
    assert r["decision"].startswith("stopped") and r["final"] and r["decision at"] is None
    assert r["checks"]["check at"].max() == config.PILOT_MAX_WINES
    d3 = _pilot(n=600, n_sources=4)
    r3 = pilot.run_protocol(d3, n_boot=50)
    assert r3["decision at"] == config.PILOT_MIN_WINES and r3["wines used"] == config.PILOT_MIN_WINES   # later wines unused


def test_score_round_hides_the_same_wines_as_the_pilot_rule():
    import importlib.util
    from pathlib import Path
    from winevalue.artifacts import load_value_finder
    from winevalue.production import prepare_new
    spec = importlib.util.spec_from_file_location("score", Path(__file__).resolve().parents[1] / "deployment" / "score.py")
    score = importlib.util.module_from_spec(spec); spec.loader.exec_module(score)
    vf = load_value_finder()
    notes = ["Ripe black cherry and plum with smooth tannins and a long, spicy finish.",
             "Crisp lemon, green apple and wet stone; bright acidity.", "Short note.",
             "Ripe black cherry and plum with smooth tannins and a long, spicy finish."]
    cand = pd.DataFrame({"note": notes * 2, "country": ["Italy", "France", "Spain", "France"] * 2,
                         "variety": ["Sangiovese", "Chardonnay", "Tempranillo", "Merlot"] * 2, "price": [18, 22, np.nan, 15] * 2,
                         "source": ["Kerin O'Keefe", "Small Importer", "Big Importer", "big importer"] * 2})
    status = {"withdrawn everywhere": False, "sources": ["Kerin O’Keefe"], "pooled sources": ["small importer"], "countries": []}
    out, report = score.score_round(cand, k=2, status=status, vf=vf)
    want = pilot.band_hidden(prepare_new(cand), status)
    assert out["estimate"].isna().sort_index().equals(want.sort_index())
    assert report["bands hidden"] == int(want.sum()) == 4
    assert out.loc[2, "flag: short note"] and out.loc[2, "flag: no price"] and out.loc[3, "flag: duplicate in round"]
    assert set(report["indicators"]) >= set(config.MONITOR_ALERTS)
    with pytest.raises(ValueError, match="price"):
        score.score_round(cand.drop(columns="price"), vf=vf)


def test_alerts_follow_the_configured_rules():
    from winevalue import monitoring
    ok = {"share of note words outside the model vocabulary": 0.01, "median note length (words)": 40, "share unmapped colour": 0.02,
          "share of grapes rare or unseen in training": 0.03, "≤ $25 share": 0.45, "mean P(90+) (≤ $25)": 0.2,
          "share above the development 90th percentile (≤ $25)": 0.1}
    assert monitoring.alerts(ok) == []
    bad = monitoring.alerts({**ok, "median note length (words)": 12, "≤ $25 share": 0.1})
    assert len(bad) == 2 and bad[0].startswith("median note length") and bad[1].startswith("≤ $25 share")
    low = monitoring.alerts({**ok, "mean P(90+) (≤ $25)": 0.05, "share above the development 90th percentile (≤ $25)": 0.02})
    assert len(low) == 2                                       # the ranker-level alerts are two-sided


def test_detection_rates_run_on_broken_files():
    from winevalue import monitoring
    from winevalue.artifacts import load_value_finder
    vf = load_value_finder()
    rng = np.random.default_rng(1)
    words = ["cherry", "plum", "oak", "vanilla", "lemon", "apple", "spice", "tannins", "acidity", "finish", "ripe", "bright"]
    raw = pd.DataFrame({"description": [" ".join(rng.choice(words, 40)) for _ in range(300)], "country": "US",
                        "variety": "Merlot", "price": rng.integers(8, 40, 300).astype(float)})
    pert = {k: monitoring.PERTURBATIONS[k] for k in ("none (lockbox as is)", "notes truncated to 15 words", "20% of note words unknown (another language, in part)")}
    t = monitoring.detection_rates(vf, raw, pert, size=200, n_rounds=5)
    assert t.loc["notes truncated to 15 words", "median note length (words)"] == 1.0
    assert t.loc["20% of note words unknown (another language, in part)", "share of note words outside the model vocabulary"] == 1.0
    assert t.loc["none (lockbox as is)", "share of note words outside the model vocabulary"] == 0.0


def test_round_tiers_rank_within_the_round():
    from winevalue.artifacts import load_value_finder
    vf = load_value_finder()
    rng = np.random.default_rng(0)
    words = ["cherry", "plum", "oak", "vanilla", "lemon", "apple", "spice", "tannins", "acidity", "finish", "ripe", "bright"]
    cand = pd.DataFrame({"note": [" ".join(rng.choice(words, 15)) for _ in range(50)], "country": "US", "variety": "Merlot",
                         "price": rng.integers(8, 25, 50).astype(float)})
    sl = vf.shortlist(cand, k=5)
    assert (sl["round tier"].str.startswith("Sample first")).sum() == 5 and (sl["round tier"].str.startswith("Worth")).sum() == 5
    assert sl.loc[sl["rank"] <= 5, "round tier"].str.startswith("Sample first").all()


def test_masked_ranker_refits_the_ranker_on_masked_notes():
    from winevalue import evaluate as ev
    from winevalue.phase5 import masked_ranker
    from winevalue.production import prepare_new
    from winevalue.scoring import ridge_fit_predict
    rng = np.random.default_rng(1)
    words = ["cherry", "plum", "oak", "lemon", "apple", "spice", "tannins", "acidity", "finish", "ripe"]
    n = 80
    notes = [" ".join(rng.choice(words, 12)) + (" outstanding superb" if i % 2 else "") for i in range(n)]
    raw = pd.DataFrame({"note": notes, "country": "US", "province": "California", "variety": "Merlot", "price": rng.integers(8, 25, n),
                        "title": [f"W{i} 2014 Merlot" for i in range(n)], "winery": [f"W{i}" for i in range(n)]})
    d = prepare_new(raw).assign(points=lambda t: 86 + 4 * (np.arange(n) % 2) + rng.normal(0, 1, n))
    tr, te = d.iloc[:60], d.iloc[60:]
    run = {"train": tr, "test": te, "info": {"ranker ridge alpha": 4.0}}
    got = masked_ranker(run)
    m = ev.MASKS["frozen list"]
    want = ridge_fit_predict(4.0, with_price=True)(tr.assign(note=m(tr["note"], ())), te.assign(note=m(te["note"], ())))
    assert np.allclose(got.to_numpy(), want) and got.index.equals(te.index)
    plain = ridge_fit_predict(4.0, with_price=True)(tr, te)
    assert not np.allclose(got.to_numpy(), plain)          # the verdict words carried signal, and the mask removed it


def test_one_writer_spelled_two_ways_is_one_source_everywhere():
    """Phase 6 critic round 2 issue 1, against ground truth (not against band_hidden itself)."""
    d = _pilot(n=400, n_sources=3, shift={"s0": 2.5})        # 3 sources of ~133 wines; s0 badly off
    truth = pilot.run_protocol(d, n_boot=100)
    assert truth["sources with enough wines"] == 3 and ("source", "s0") in truth["band withdrawn"]
    v = d.copy()
    s0 = v.index[v["source"].eq("s0")]
    v.loc[s0[::3], "source"] = " S0 "                       # a third of s0's wines typed another way
    v.loc[v.index[v["country"].eq("A")][::2], "country"] = "a"
    r = pilot.run_protocol(v, n_boot=100)
    assert r["sources with enough wines"] == 3               # not 4
    assert set(r["band withdrawn"]) == set(truth["band withdrawn"]) and r["decision"] == truth["decision"]
    assert r["band withdrawn rows"].sort_index().equals(truth["band withdrawn rows"].sort_index())
    assert r["checks"].equals(truth["checks"])
    two = _pilot(n=400, n_sources=2)                          # 2 real sources, one typed two ways: still no decision
    two.loc[two.index[two["source"].eq("s0")][::2], "source"] = "S0"
    r2 = pilot.run_protocol(two, n_boot=50)
    assert r2["sources with enough wines"] == 2 and r2["decision"].startswith("interim")
    t = pilot.source_list(pilot.canonical_names(v)).set_index("source")
    assert t.loc["s0", "wines"] == len(s0) and t.loc["s0", "spellings"] == " S0  | s0"


def _vf_with_spellings():
    """The deployed artifact, with its training spellings (built from the development rows if the saved artifact
    predates revision 4)."""
    from winevalue import production
    from winevalue.artifacts import load_value_finder
    vf = load_value_finder()
    if not getattr(vf, "categories", None):
        from pathlib import Path
        from winevalue.cv import development
        prep = pd.read_parquet(Path(__file__).resolve().parents[1] / "data" / "processed" / "wine_prepared.parquet")
        vf.categories = production.training_spellings(development(prep))
    return vf


def test_country_variants_score_like_the_training_spelling():
    """Phase 6 critic round 3 issue 1a: case and alias variants of origin and grape reach the models as the training
    spelling, and a country the models never saw is flagged and counted."""
    from winevalue import monitoring
    vf = _vf_with_spellings()
    base = pd.DataFrame({"note": ["Ripe black cherry and plum with smooth tannins and a long, spicy finish."] * 4,
                         "country": ["Italy", "US", "Spain", "France"], "province": ["Tuscany", "California", "Northern Spain", "Bordeaux"],
                         "variety": ["Sangiovese", "Merlot", "Tempranillo", "Merlot"], "price": [18.0, 22.0, 15.0, 24.0]})
    variant = base.assign(country=["italy", "USA", " SPAIN ", "france"], province=["tuscany", "CALIFORNIA", "northern spain", "Bordeaux"],
                          variety=["sangiovese", "MERLOT", "tempranillo", "merlot"])
    a, b = vf.score(base), vf.score(variant)
    assert np.allclose(a["estimate"], b["estimate"]) and np.allclose(a["rank score"], b["rank score"])
    assert np.allclose(vf.baseline(vf.prepare(base)), vf.baseline(vf.prepare(variant)))
    d = vf.prepare(variant)
    assert list(d["country"]) == ["Italy", "US", "Spain", "France"] and d["country (as given)"].iloc[1] == "USA"
    odd = vf.prepare(base.assign(country=["Atlantis", "US", "Spain", "France"]))
    assert list(monitoring.country_unseen(vf, odd)) == [True, False, False, False]
    flags, rep = monitoring.round_report(vf, base.assign(country=["Atlantis", "US", "Spain", "France"]))
    assert rep["flag counts"]["flag: country unseen in training"] == 1
    assert rep["indicators"]["share of countries unseen in training"] == 0.25
    assert any(x.startswith("share of countries unseen in training") for x in rep["alerts"])
    assert monitoring.round_report(vf, variant)[1]["names mapped to training spellings"]["country"] == 4


def test_unseen_country_in_another_case_still_matches_its_province():
    """Re-execution 7 check: an unseen country is not mapped, so the province = country rule must ignore case (England,
    province England -> 'Unknown province', however either is written)."""
    vf = _vf_with_spellings()
    row = pd.DataFrame({"note": ["Crisp green apple and lemon with fine bubbles."] * 3, "variety": "Sparkling Blend",
                        "country": ["England", "ENGLAND", "england"], "province": ["England", "England", "ENGLAND"],
                        "price": 24.0})
    d = vf.prepare(row)
    assert d["province_model"].eq("Unknown province").all()
    s = vf.score(row)
    assert np.allclose(s["estimate"], s["estimate"].iloc[0])


def test_unsourced_rows_never_count_as_a_source():
    """Phase 6 critic round 3 issue 1b: two named writers plus rows without a source must not reach the decision."""
    d = _pilot(n=400, n_sources=3)
    d.loc[d["source"].eq("s2"), "source"] = np.nan             # a third of the wines have no note source
    r = pilot.run_protocol(d, n_boot=50)
    assert r["sources with enough wines"] == 2 and r["decision"].startswith("interim") and not r["meets source minimum"]
    assert ("source", "unknown") in pilot.check_units(pilot.canonical_names(d))   # still a stop-rule unit


def test_only_the_primary_scorer_enters_the_gate(monkeypatch):
    other = np.arange(500) % 5 == 4                              # every fifth score arrives from another critic
    d = _pilot(n=500, n_sources=4).assign(scorer=np.where(other, "Other Critic", "Wine Enthusiast"),
                                          sampled=lambda t: np.arange(len(t)) % 4 == 0)
    d.loc[other, "sel"] += 5                                    # the other critic's scores sit far from the estimates
    monkeypatch.setattr(pilot, "from_raw", lambda df, vf: df)
    r = pilot.evaluate_raw(d, vf=None, n_boot=50)
    assert r["gate"]["wines"] == 400 and r["gate"]["wines from other scorers (sensitivity only)"] == 100
    assert r["gate"]["decision"].startswith("deploy shortlist and show")
    ps = r["sensitivity"]["per scorer"].set_index("scorer")
    assert ps.loc["Other Critic", "mean residual"] > 4 and ps.loc["Wine Enthusiast", "wines"] == 400
    assert r["sensitivity"]["unsampled wines used"] == 300 and r["sensitivity"]["unsampled wines"]["wines"] == 300
    assert r["sensitivity"]["all scorers"]["wines"] == 499     # every scorer up to the decision (order 499; the 500th is later)
    late = pd.concat([d, d.iloc[:50].assign(order=lambda t: t["order"] + 1000, scorer="Other Critic")], ignore_index=True)
    assert pilot.evaluate_raw(late, vf=None, n_boot=50)["sensitivity"]["all scorers: wines"] == 499   # later arrivals excluded
    alias = d.assign(scorer=np.where(other, "Other Critic", "Wine Enthusiast Magazine"))
    assert pilot.evaluate_raw(alias, vf=None, n_boot=50)["gate"]["wines"] == 400
    none = d.assign(scorer="Other Critic")
    r0 = pilot.evaluate_raw(none, vf=None, n_boot=50)
    assert r0["gate"]["wines"] == 0 and r0["gate"]["decision"].startswith("no scores from") and not r0["gate"]["final"]


def test_price_deflator_converts_to_2017_dollars(monkeypatch):
    from winevalue import production
    raw = pd.DataFrame({"note": ["Crisp lemon and apple."], "country": ["US"], "variety": ["Chardonnay"], "price": [30.0]})
    assert not production.prepare_new(raw)["in_value_pool"].iloc[0]
    monkeypatch.setattr(config, "PRICE_DEFLATOR", 0.8)
    d = production.prepare_new(raw)
    assert d["price"].iloc[0] == 24.0 and d["price (as given)"].iloc[0] == 30.0 and d["in_value_pool"].iloc[0]


def test_lower_limit_rule_and_source_share_rule():
    from winevalue import monitoring, phase6
    rounds = pd.DataFrame({"pool": ["a"] * 100 + ["b"] * 100,
                           monitoring.RANKER_INDICATORS[0]: np.r_[np.linspace(0.10, 0.30, 100), np.linspace(0.20, 0.40, 100)],
                           monitoring.RANKER_INDICATORS[1]: np.r_[np.linspace(0.05, 0.25, 100), np.linspace(0.10, 0.30, 100)]})
    lim = monitoring.choose_lower_limits(rounds, q=0.01)
    assert lim == {monitoring.RANKER_INDICATORS[0]: 0.10, monitoring.RANKER_INDICATORS[1]: 0.05}
    p = phase6.source_minimum_probability(shares=(0.125, 0.2), sizes=(400,))
    assert abs(p["P(all sources ≥ 50)"].iloc[0] - 0.107) < 0.005 and p["P(all sources ≥ 50)"].iloc[1] > 0.999
    assert phase6.choose_source_share(p, target=0.8) == 0.2


def test_business_kpi():
    from winevalue import monitoring
    s = pd.DataFrame({"sampled": [True, True, True, True, False], "points": [91, 88, np.nan, 92, 95]})
    k = monitoring.business_kpi(s)
    assert k["sampled and reviewed"] == 3 and k["value wines"] == 2 and k["samples per value wine"] == 1.5
    k2 = monitoring.business_kpi(s.assign(**{"shortlist used": [True, False, True, True, True]}))
    assert k2["rounds with the shortlist"]["value wines"] == 2 and k2["rounds without it"]["sampled and reviewed"] == 1


def test_placeholder_sources_are_one_unsourced_unit():
    """Phase 6 critic round 4 issue 6: placeholders ("N/A", "none", "-", "") are not sources and form one unit."""
    d = _pilot(n=400, n_sources=3)
    s2 = d.index[d["source"].eq("s2")]
    d.loc[s2, "source"] = np.array(["N/A", "none", "-", "", None], dtype=object)[np.arange(len(s2)) % 5]
    t = d.copy()
    t["source (as given)"] = t["source"]
    t.loc[pilot.name_key(t["source"]).set_axis(t.index).isin(pilot.UNSOURCED), "source"] = "unknown"
    assert set(t.loc[s2, "source"]) == {"unknown"}
    r = pilot.run_protocol(t, n_boot=50)
    assert r["sources with enough wines"] == 2 and r["decision"].startswith("interim")


def test_winery_variants_give_the_same_gate_and_coverage_rule():
    """Phase 6 critic round 4 issue 1: winery names reach the "winery track record" rule as the training spelling, and the
    comparator-coverage rule is applied at the decision point."""
    from pathlib import Path
    vf = _vf_with_spellings()
    prep = pd.read_parquet(Path(__file__).resolve().parents[1] / "data" / "processed" / "wine_prepared.parquet")
    lb = prep[prep["is_lockbox"] & prep["in_value_pool"]].sample(400, random_state=1)
    raw = lb[["description", "country", "province", "variety", "region_1", "designation", "winery", "title", "price",
              "vintage", "points"]].assign(source=lb["critic"], order=np.arange(1, 401))
    a = vf.rule_scores(vf.prepare(raw))["winery track record"]
    b = vf.rule_scores(vf.prepare(raw.assign(winery=raw["winery"].str.upper())))["winery track record"]
    assert np.allclose(a, b)
    ta, tb = pilot.from_raw(raw, vf), pilot.from_raw(raw.assign(winery=raw["winery"].str.upper()), vf)
    assert ta["winery seen"].equals(tb["winery seen"]) and 0.4 < ta["winery seen"].mean() < 0.95
    # the coverage rule: below the minimum, BO1 must also pass on the matched wines
    t = _pilot(n=400, n_sources=3).assign(**{"winery seen": np.arange(400) % 10 < 3})
    c = pilot.comparator_check(t, n_boot=50)
    assert c["comparator degraded"] and abs(c["winery coverage"] - 0.3) < 1e-9 and c["matched-winery gate"]["wines"] == 120
    t_ok = t.assign(**{"winery seen": True})
    assert not pilot.comparator_check(t_ok, n_boot=50)["comparator degraded"]
    few = t.assign(**{"winery seen": np.arange(400) < 60})
    assert pilot.comparator_check(few, n_boot=50)["BO1 holds"] is False       # too few matched wines to show it


def test_lexicon_grapes_in_any_case_keep_grape_and_colour():
    """Phase 6 critic round 4 issue 2: a grape known only to the grape lexicon (Turbiana) or a blend of lexicon grapes keeps
    its canonical grape and colour whatever its case."""
    vf = _vf_with_spellings()
    base = pd.DataFrame({"note": ["Crisp lemon, almond and green apple with a saline finish."] * 2, "country": "Italy",
                         "variety": ["Turbiana", "Pinot Gris-Gewürztraminer"], "price": 18.0})
    a = vf.prepare(base)
    for f in (str.lower, str.upper):
        b = vf.prepare(base.assign(variety=base["variety"].map(f)))
        assert list(b["grape"]) == list(a["grape"]) and list(b["colour"]) == list(a["colour"])
        assert np.allclose(vf.estimate(a), vf.estimate(b))


def test_serving_path_is_part_of_the_reproduction_record():
    """Phase 6 critic round 4 issue 3: the manifest must record the lockbox reproduced through raw inputs too."""
    from winevalue import artifacts, production
    assert production.SERVING_PATH in artifacts.REPRO_KEYS
    rec = {k: 0.0 for k in artifacts.REPRO_KEYS}
    assert artifacts.reproduction_passed(rec)
    assert not artifacts.reproduction_passed({k: v for k, v in rec.items() if k != production.SERVING_PATH})


def test_prepare_is_idempotent_and_shows_the_2017_price(monkeypatch):
    """Phase 6 critic round 4 issue 4: preparing twice never deflates twice; the 2017-dollar price is an output."""
    from winevalue import production
    monkeypatch.setattr(config, "PRICE_DEFLATOR", 0.8)
    raw = pd.DataFrame({"note": ["Crisp lemon and apple."], "country": ["US"], "variety": ["Chardonnay"], "price": [30.0]})
    once = production.prepare_new(raw)
    assert production.prepare_new(once)["price"].iloc[0] == 24.0
    vf = _vf_with_spellings()
    assert vf.score(raw)["price (2017 $)"].iloc[0] == 24.0


def _script(name):
    import importlib.util
    from pathlib import Path
    spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parents[1] / "deployment" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_ranker_lower_rows_and_small_rounds():
    """Critic round 5 issue 8: the lower limit follows the round's ≤ $25 count; below 200 only the upper limit is read."""
    from winevalue import monitoring
    k0, k1 = monitoring.RANKER_INDICATORS
    assert monitoring.ranker_lower(k0, 199) is None
    for n, row in [(200, 200), (299, 200), (300, 300), (599, 300), (600, 600), (999, 600), (1000, 1000), (2500, 1000)]:
        assert monitoring.ranker_lower(k0, n) == config.MONITOR_RANKER_LOWER[row][0]
        assert monitoring.ranker_lower(k1, n) == config.MONITOR_RANKER_LOWER[row][1]
    small_promo = {"≤ $25 candidates": 120, k0: 0.76, k1: 0.89}
    assert any(a.startswith(k0) for a in monitoring.alerts(small_promo))           # upper limit read below 200
    small_low = {"≤ $25 candidates": 120, k0: 0.01, k1: 0.0}
    assert not monitoring.alerts(small_low)                                        # lower limits not read below 200
    assert any(a.startswith(k1) for a in monitoring.alerts({"≤ $25 candidates": 400, k0: 0.2, k1: 0.01}))


def test_prefiltered_file_and_relative_drop():
    """Critic round 5 issues 1 and 8: a file with only ≤ $25 wines alerts; a fall to under half the trailing median alerts."""
    from winevalue import monitoring
    assert any(a.startswith("≤ $25 share") for a in monitoring.alerts({"≤ $25 share": 1.0}))
    assert not monitoring.alerts({"≤ $25 share": 0.45})
    k = monitoring.RELATIVE_INDICATOR
    hist = [{"≤ $25 candidates": 900, k: v} for v in (0.30, 0.28, 0.32)]
    assert monitoring.relative_alerts({"≤ $25 candidates": 900, k: 0.11}, hist)
    assert not monitoring.relative_alerts({"≤ $25 candidates": 900, k: 0.20}, hist)
    assert not monitoring.relative_alerts({"≤ $25 candidates": 900, k: 0.11}, hist[:2])       # needs 3 earlier rounds
    assert not monitoring.relative_alerts({"≤ $25 candidates": 150, k: 0.01}, hist)            # too small a round


def test_winery_is_matched_within_its_country_only():
    """Critic round 5 issue 2: "Patria" from Italy is not the Portuguese "Pátria"; an accent variant in the same country is."""
    vf = _vf_with_spellings()
    by = vf.categories["winery"]["by key"]
    pt = [k for k, v in by.items() if v == "Pátria"]
    assert pt and all(k.endswith("|portugal") for k in pt)
    row = pd.DataFrame({"note": ["Crisp lemon and green apple."] * 2, "country": ["Italy", "Portugal"],
                        "variety": "White Blend", "price": 12.0, "winery": ["Patria", "PATRIA"]})
    d = vf.prepare(row)
    assert d["winery"].tolist() == ["Patria", "Pátria"]


def test_a_winery_case_variant_scores_as_its_exact_spelling():
    """Re-execution 10: "NEUMEISTER" with country Unknown is "Neumeister" (an Austrian training winery), as the exact
    spelling is, so it is seen and gets the same track record; an accent variant from another country is still not
    matched ("Patria", Italy)."""
    vf = _vf_with_spellings()
    assert "Neumeister" in vf.categories["winery"]["spellings"]
    row = pd.DataFrame({"note": ["Crisp lemon and green apple."] * 4, "country": ["Unknown", "Unknown", np.nan, "Italy"],
                        "variety": "White Blend", "price": 12.0,
                        "winery": ["Neumeister", "NEUMEISTER", "neumeister", "PATRIA"]})
    d = vf.prepare(row)
    assert d["winery"].tolist() == ["Neumeister"] * 3 + ["PATRIA"]
    tr = np.asarray(vf.rule_scores(d)["winery track record"], float)
    assert tr[0] == tr[1] == tr[2]


def test_an_unknown_winery_keeps_a_query_fast():
    """Re-execution 11: the case lookup was rebuilt per query (about 4 s for a wine with an unseen winery, BSC4 < 3 s).
    It is built once per artifact now."""
    import time
    vf = _vf_with_spellings()
    row = pd.DataFrame({"note": ["Crisp lemon and green apple."], "country": ["Italy"], "variety": "White Blend",
                        "price": 12.0, "winery": ["A Winery Nobody Has Heard Of"]})
    vf.prepare(row)                                           # first call may build the lookup
    t = time.perf_counter()
    for _ in range(5):
        vf.prepare(row)
    assert (time.perf_counter() - t) / 5 < 0.5


def test_degraded_comparator_shows_in_the_gate_file(monkeypatch):
    """Critic round 5 issue 3: when the comparator rule blocks the shortlist, gate.json says so."""
    d = _pilot(n=400, n_sources=3).assign(**{"winery seen": np.arange(400) < 40})     # 10% coverage, 40 matched wines
    monkeypatch.setattr(pilot, "from_raw", lambda df, vf: df)
    r = pilot.evaluate_raw(d, vf=None, n_boot=50)
    g = r["gate"]
    assert g["BO1 passes"] and g["comparator degraded"] and not g["BO1 passes (after comparator rule)"]
    assert not g["joint gate passes"] and g["decision"].startswith("deploy nothing")
    assert r["sensitivity"]["matched-winery wines"] is None


def test_interim_gate_file_does_not_pass_a_shortlist_the_comparator_rule_could_block(monkeypatch):
    """Critic round 6 issue 4: before the decision point (300 wines, 0% coverage) the after-rule flag and the joint gate
    are None, not PASS."""
    d = _pilot(n=300, n_sources=3).assign(**{"winery seen": False})
    monkeypatch.setattr(pilot, "from_raw", lambda df, vf: df)
    g = pilot.evaluate_raw(d, vf=None, n_boot=50)["gate"]
    assert g["decision"].startswith("interim") and g["decision at"] is None
    assert g["BO1 passes (after comparator rule)"] is None and g["joint gate passes"] is None


def test_sampled_flag_is_read_strictly():
    """Critic round 6 issue 5: the gate's unsampled-wines sensitivity reads `sampled` with the KPI's strict parser."""
    from winevalue import monitoring
    assert monitoring._flag(pd.Series(["yes", "", "No", 1.0]), "sampled").tolist() == [True, False, False, True]
    for bad in ("N/A", "x", "Sampled"):
        with pytest.raises(ValueError):
            monitoring._flag(pd.Series([bad]), "sampled")


def test_business_kpi_reads_csv_flags():
    """Critic round 5 issue 5: "yes"/"no" strings and blanks are read as flags; anything else is refused."""
    from winevalue import monitoring
    s = pd.DataFrame({"sampled": ["yes", "no", "yes", "YES", ""], "points": [91, 95, 88, 92, 93],
                      "shortlist used": ["true", "false", "false", "1", "0"]})
    k = monitoring.business_kpi(s)
    assert k["sampled and reviewed"] == 3 and k["value wines"] == 2
    assert k["rounds with the shortlist"]["sampled and reviewed"] == 2 and k["rounds without it"]["sampled and reviewed"] == 1
    with pytest.raises(ValueError):
        monitoring.business_kpi(s.assign(sampled=["yes", "maybe", "no", "no", "no"]))


def test_pilot_eval_refuses_a_file_without_the_right_deflator(tmp_path, monkeypatch):
    """Critic round 5 issue 6 and round 6 issue 5: a missing, different, mixed or partly blank deflator is refused; a
    matching one gets past the check, and --deflator-confirmed covers only a missing column."""
    pe = _script("pilot_eval")
    base = pd.DataFrame({"note": ["a"], "country": ["US"], "variety": ["Merlot"], "price": [10.0], "points": [90],
                         "source": ["s"], "order": [1]})
    for name, df in {"absent": base, "different": base.assign(**{"price deflator": 0.8}),
                     "mixed": pd.concat([base.assign(**{"price deflator": 1.0}), base.assign(**{"price deflator": 0.8})]),
                     # critic round 6 issue 5: one row without a deflator (appended from an unscored source)
                     "partly blank": pd.concat([base.assign(**{"price deflator": config.PRICE_DEFLATOR}),
                                                base.assign(**{"price deflator": np.nan})])}.items():
        f = tmp_path / f"{name}.csv"; df.to_csv(f, index=False)
        with pytest.raises(SystemExit) as e:
            pe.main([str(f), "--out", str(tmp_path / "out")])
        assert "refused" in str(e.value)

    class Passed(Exception):
        pass

    def stop():
        raise Passed
    monkeypatch.setattr(pe, "load_value_finder", stop)
    for df, extra in [(base.assign(**{"price deflator": config.PRICE_DEFLATOR}), []), (base, ["--deflator-confirmed"])]:
        f = tmp_path / "ok.csv"; df.to_csv(f, index=False)
        with pytest.raises(Passed):
            pe.main([str(f), "--out", str(tmp_path / "out"), *extra])


def test_score_reads_the_earlier_rounds(tmp_path):
    """Critic round 5 issue 8 and round 6 issue 3: score.py's history is the folder's reports of EARLIER rounds, ordered
    by round number (not file time), one per round (the latest write of a re-scored round), never round 0 (test files),
    with each round's own alert and accepted flags."""
    import json
    import os
    sc = _script("score")
    k = "share above the development 90th percentile (≤ $25)"
    def write(name, rnd, v, t, **extra):
        f = tmp_path / f"{name}.monitoring.json"
        f.write_text(json.dumps({"round": rnd, "indicators": {"≤ $25 candidates": 900, k: v}, **extra}))
        os.utime(f, (t, t))
    write("r3", 3, 0.32, 1000)                     # written first, but round 3
    write("r1", 1, 0.30, 1001)
    write("r2_old", 2, 0.99, 1002)
    write("r2", 2, 0.28, 1003)                     # round 2 re-scored: this one counts
    write("test", 0, 0.01, 1004)                   # rollout step 1 test file
    write("r5", 5, 0.05, 1005, **{"self-referenced alert": True})
    (tmp_path / "broken.monitoring.json").write_text("not json")
    (tmp_path / "old.monitoring.json").write_text(json.dumps({"indicators": {k: 0.5}}))      # no round number
    h = sc.load_history(tmp_path, before=5)
    assert [x[k] for x in h] == [0.30, 0.28, 0.32]
    h = sc.load_history(tmp_path, before=9)
    assert [x[k] for x in h] == [0.30, 0.28, 0.32, 0.05] and h[-1]["self-referenced alert"] and not h[-1]["accepted"]


def test_relative_rule_holds_on_a_persistent_fault():
    """Critic round 6 issue 1: three clean rounds, then a fault that is never fixed. A round that raised the rule's own
    alert stays out of the reference, so every faulty round alerts; once the analyst accepts the new level, the
    reference moves to it."""
    from winevalue import monitoring
    k = monitoring.RELATIVE_INDICATOR
    hist, fired = [], []
    for v in (0.30, 0.29, 0.31, 0.04, 0.05, 0.04, 0.05):
        ind = {"≤ $25 candidates": 1000, k: v}
        a = monitoring.relative_alerts(ind, hist)
        fired.append(bool(a))
        hist.append({**ind, "self-referenced alert": bool(a), "accepted": False})
    assert fired == [False, False, False, True, True, True, True]
    for h in hist[3:]:
        h["accepted"] = True
    assert not monitoring.relative_alerts({"≤ $25 candidates": 1000, k: 0.04}, hist)
    # the simulation applies the same exclusion
    r = pd.DataFrame({"pool": "p", monitoring.RANKER_INDICATORS[1]: [0.30, 0.29, 0.31, 0.04, 0.05, 0.04, 0.05]})
    assert monitoring.relative_drop_rates(r).iloc[0] == 1.0


def test_relative_rule_minimum_round_size():
    """The self-referenced rule is read from the smallest size whose false-alert rate stays ≤ 2% from there on."""
    from winevalue import monitoring
    idx = pd.MultiIndex.from_product([[200, 300, 600, 1000], ["f0", "f1"]], names=["size", "pool"])
    r = pd.Series([0.0, 0.09, 0.0, 0.06, 0.0, 0.012, 0.0, 0.0], index=idx)
    assert monitoring.choose_relative_min_pool(r) == 600
    assert monitoring.choose_relative_min_pool(r.where(r.index.get_level_values("size") != 1000, 0.05)) is None
    k = monitoring.RELATIVE_INDICATOR
    hist = [{"≤ $25 candidates": 450, k: 0.3}] * 3
    assert not monitoring.relative_alerts({"≤ $25 candidates": 450, k: 0.05}, hist)        # under 600: not read


def test_share_band_is_kept_or_recentred_on_the_retailer():
    """Critic round 6 issue 9: the ≤ $25-share band is kept for a retailer like the data, re-centred otherwise, and a
    pre-filtered file (share 1.0) stays outside it either way."""
    from winevalue import monitoring
    assert monitoring.share_band(0.45) == (0.25, 0.95)
    lo, hi = monitoring.share_band(0.90)
    assert (lo, hi) == (0.70, 0.98) and not lo <= 1.0 <= hi and lo <= 0.90 <= hi
    lo, hi = monitoring.share_band(0.20)
    assert (lo, hi) == (0.05, 0.65) and lo <= 0.20 <= hi


def test_one_constant_for_a7():
    """Critic round 6 issue 7: A7 lives in one place."""
    assert config.PILOT_ROUND_CANDIDATES == config.CANDIDATES_PER_CYCLE
