# -*- coding: utf-8 -*-
"""
World Cup 2026 Simulator
"""

import os
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import poisson
from scipy.special import expit
from scipy.optimize import minimize
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import log_loss
import json
import requests
from bs4 import BeautifulSoup
from itertools import combinations
from multiprocessing import Pool, cpu_count
import os

# ─────────────────────────────────────────────
# 0. PATHS
# ─────────────────────────────────────────────
DRIVE_PATH = "./data"

RESULTS_PATH   = os.path.join(DRIVE_PATH, "results.csv")
SHOOTOUTS_PATH = os.path.join(DRIVE_PATH, "shootouts.csv")
ELO_PATH       = os.path.join(DRIVE_PATH, "eloratings.csv")

MAX_GOALS_PER_TEAM = 7  # hard cap on simulated goals per team per 90 min
MAX_GOALS_ET       = 3  # hard cap per team in extra time

# ─────────────────────────────────────────────
# 1. LOAD DATA
# ─────────────────────────────────────────────
results   = pd.read_csv(RESULTS_PATH,   parse_dates=["date"])
shootouts = pd.read_csv(SHOOTOUTS_PATH, parse_dates=["date"])


# Canonical name map — everything normalizes to results.csv naming
NAME_MAP = {
    "Czechia":                      "Czech Republic",
    "Democratic Republic of Congo": "DR Congo",
    "Curacao":                      "Curaçao",
}

def normalize(name: str) -> str:
    return NAME_MAP.get(name, name)

results["home_team"]   = results["home_team"].apply(normalize)
results["away_team"]   = results["away_team"].apply(normalize)
shootouts["home_team"] = shootouts["home_team"].apply(normalize)
shootouts["away_team"] = shootouts["away_team"].apply(normalize)
shootouts["winner"]    = shootouts["winner"].apply(normalize)

# ─────────────────────────────────────────────
# 2. WC 2026 GROUPS
# ─────────────────────────────────────────────
WC2026_GROUPS = {
    "A": ["Mexico",        "South Korea",   "South Africa",  "Czech Republic"],
    "B": ["Canada",        "Switzerland",   "Qatar",         "Bosnia and Herzegovina"],
    "C": ["Brazil",        "Morocco",       "Scotland",      "Haiti"],
    "D": ["United States", "Paraguay",      "Australia",     "Turkey"],
    "E": ["Germany",       "Curaçao",       "Ivory Coast",   "Ecuador"],
    "F": ["Netherlands",   "Japan",         "Sweden",        "Tunisia"],
    "G": ["Belgium",       "Egypt",         "Iran",          "New Zealand"],
    "H": ["Spain",         "Cape Verde",    "Saudi Arabia",  "Uruguay"],
    "I": ["France",        "Senegal",       "Norway",        "Iraq"],
    "J": ["Argentina",     "Algeria",       "Austria",       "Jordan"],
    "K": ["Portugal",      "Colombia",      "Uzbekistan",    "DR Congo"],
    "L": ["England",       "Croatia",       "Ghana",         "Panama"],
}
wc_teams = [t for group in WC2026_GROUPS.values() for t in group]

# ─────────────────────────────────────────────
# 3. COMPUTE ELO FROM SCRATCH
# ─────────────────────────────────────────────
K_BASE         = 20
K_TOURNAMENT   = {
    "FIFA World Cup":          3.0,
    "Confederations Cup":      2.5,
    "Copa América":            2.0,
    "UEFA Euro":               2.0,
    "AFC Asian Cup":           2.0,
    "Africa Cup of Nations":   2.0,
    "CONCACAF Gold Cup":       2.0,
    "UEFA Nations League":     1.5,
    "Friendly":                1.0,
}
K_DEFAULT      = 1.5
HOME_ADVANTAGE = 100
INITIAL_ELO    = 1500

def get_k(tournament: str) -> float:
    for key, mult in K_TOURNAMENT.items():
        if key in tournament:
            return K_BASE * mult
    return K_BASE * K_DEFAULT

def expected_score(elo_a: float, elo_b: float) -> float:
    return 1 / (1 + 10 ** ((elo_b - elo_a) / 400))

def goal_index(gf: int, ga: int) -> float:
    diff = abs(gf - ga)
    if diff <= 1: return 1.0
    if diff == 2: return 1.5
    return (11 + diff) / 8

def match_result(gf: int, ga: int) -> float:
    if gf > ga:   return 1.0
    if gf == ga:  return 0.5
    return 0.0

def compute_elo(results: pd.DataFrame) -> tuple:
    elo     = {}
    records = []
    df = results.dropna(subset=["home_score", "away_score"]).copy()
    df = df.sort_values("date").reset_index(drop=True)

    for idx, row in df.iterrows():
        home, away = row["home_team"], row["away_team"]
        gh, ga     = int(row["home_score"]), int(row["away_score"])
        neutral    = row["neutral"]
        tournament = row["tournament"]

        elo.setdefault(home, INITIAL_ELO)
        elo.setdefault(away, INITIAL_ELO)

        elo_h = elo[home] + (0 if neutral else HOME_ADVANTAGE)
        elo_a = elo[away]

        exp_h = expected_score(elo_h, elo_a)
        exp_a = 1 - exp_h
        res_h = match_result(gh, ga)
        res_a = 1 - res_h

        K  = get_k(tournament)
        GI = goal_index(gh, ga)

        delta_h = K * GI * (res_h - exp_h)
        delta_a = K * GI * (res_a - exp_a)

        records.append((row["date"], idx, home, elo[home], elo[home] + delta_h))
        records.append((row["date"], idx, away, elo[away], elo[away] + delta_a))

        elo[home] += delta_h
        elo[away] += delta_a

    history = pd.DataFrame(records, columns=["date", "match_id", "team", "elo_before", "elo_after"])
    return elo, history

raw_computed_elo, elo_history = compute_elo(results)
elo_history["date"] = pd.to_datetime(elo_history["date"])

with open(os.path.join(DRIVE_PATH, "elo_current.json")) as f:
    scraped_raw = json.load(f)

scraped_elo = {entry["team"]: float(entry["rating"]) for entry in scraped_raw}

# ── Name mapping: eloratings.net → our canonical names ───────────────────────
ELORATINGS_NAME_MAP = {
    "Czechia":   "Czech Republic",
}

# Rebuild with the fix
scraped_elo_mapped = {
    ELORATINGS_NAME_MAP.get(team, team): rating
    for team, rating in scraped_elo.items()
}

eloratings_net_elo = raw_computed_elo.copy()
for team in wc_teams:
    if team in scraped_elo_mapped:
        eloratings_net_elo[team] = scraped_elo_mapped[team]

# ─────────────────────────────────────────────
# 4. BUILD TRAINING DATASET
# ─────────────────────────────────────────────
elo_pivot = elo_history[["match_id", "team", "elo_before"]].copy()

home_elo = (
    results.reset_index()
    .rename(columns={"index": "match_id"})
    .merge(
        elo_pivot.rename(columns={"team": "home_team", "elo_before": "home_elo"}),
        on=["match_id", "home_team"], how="left"
    )
    .merge(
        elo_pivot.rename(columns={"team": "away_team", "elo_before": "away_elo"}),
        on=["match_id", "away_team"], how="left"
    )
    [["match_id", "date", "home_team", "away_team",
      "home_score", "away_score", "tournament", "neutral",
      "home_elo", "away_elo"]]
    .dropna(subset=["home_elo", "away_elo", "home_score", "away_score"])
)

ELO_DIFF_CAP = 400

def add_features(df):
    out = df.copy()
    out["elo_diff_raw"] = out["home_elo"] - out["away_elo"]
    out["elo_diff"]     = out["elo_diff_raw"].clip(-ELO_DIFF_CAP, ELO_DIFF_CAP)
    out["elo_sum"]      = (out["home_elo"] + out["away_elo"]) / 2
    out["is_neutral"]   = out["neutral"].astype(int)
    return out

TRAIN_FROM = "1990-01-01"
EXCLUDE    = ["Friendly"]

train_df = home_elo[
    (home_elo["date"] >= TRAIN_FROM) &
    (~home_elo["tournament"].isin(EXCLUDE))
].copy()
train_df = add_features(train_df)

fit_df  = train_df[train_df["date"] < "2018-06-01"].copy()
test_df = train_df[train_df["date"] >= "2018-06-01"].copy()

# ─────────────────────────────────────────────
# 5. FIT SINGLE NEUTRAL POISSON MODEL
# ─────────────────────────────────────────────
HOST_NATIONS  = {"Mexico", "United States", "Canada"}
HOST_ELO_BOOST = 50

# Stack all competitive matches as symmetric pairs
# Each match becomes two rows — one per team, elo_diff from scorer's perspective
fit_df = add_features(train_df[train_df["date"] < "2018-06-01"].copy())

rows_a = fit_df.assign(
    goals    = fit_df["home_score"].astype(int),
    elo_diff = fit_df["elo_diff"].clip(-ELO_DIFF_CAP, ELO_DIFF_CAP),
    elo_sum  = fit_df["elo_sum"],
)
rows_b = fit_df.assign(
    goals    = fit_df["away_score"].astype(int),
    elo_diff = (-fit_df["elo_diff"]).clip(-ELO_DIFF_CAP, ELO_DIFF_CAP),
    elo_sum  = fit_df["elo_sum"],
)

stacked = pd.concat([
    rows_a[["goals", "elo_diff", "elo_sum"]],
    rows_b[["goals", "elo_diff", "elo_sum"]],
]).reset_index(drop=True)

feature_cols_neutral = ["elo_diff", "elo_sum"]
scaler_neutral = StandardScaler()
scaler_neutral.fit(stacked[feature_cols_neutral])

X_fit = pd.DataFrame(
    scaler_neutral.transform(stacked[feature_cols_neutral]),
    columns=feature_cols_neutral
)
X_fit = sm.add_constant(X_fit)
y_fit = stacked["goals"]

model_goals = sm.GLM(y_fit, X_fit, family=sm.families.Poisson()).fit()

# ─────────────────────────────────────────────
# 6. PREDICT LAMBDA
# ─────────────────────────────────────────────
def predict_lambda(team_a, team_b, elo_dict, neutral=True):
    boost_a = HOST_ELO_BOOST if (team_a in HOST_NATIONS and not neutral) else 0
    boost_b = HOST_ELO_BOOST if (team_b in HOST_NATIONS and not neutral) else 0

    elo_a    = elo_dict[team_a] + boost_a
    elo_b    = elo_dict[team_b] + boost_b
    elo_diff = np.clip(elo_a - elo_b, -ELO_DIFF_CAP, ELO_DIFF_CAP)
    elo_sum  = (elo_a + elo_b) / 2

    raw_a = pd.DataFrame([{"elo_diff":  elo_diff, "elo_sum": elo_sum}])
    raw_b = pd.DataFrame([{"elo_diff": -elo_diff, "elo_sum": elo_sum}])

    scl_a = pd.DataFrame(scaler_neutral.transform(raw_a), columns=feature_cols_neutral)
    scl_b = pd.DataFrame(scaler_neutral.transform(raw_b), columns=feature_cols_neutral)

    lam_a = model_goals.predict(sm.add_constant(scl_a, has_constant="add"))[0]
    lam_b = model_goals.predict(sm.add_constant(scl_b, has_constant="add"))[0]

    return lam_a, lam_b

# Extract coefficients once at fit time
_coef  = model_goals.params.values          # [const, elo_diff, elo_sum]
_smean = scaler_neutral.mean_               # [elo_diff_mean, elo_sum_mean]
_sstd  = scaler_neutral.scale_              # [elo_diff_std,  elo_sum_std]

def predict_lambda_fast(team_a, team_b, elo_dict, neutral=True):
    boost_a = HOST_ELO_BOOST if (team_a in HOST_NATIONS and not neutral) else 0
    boost_b = HOST_ELO_BOOST if (team_b in HOST_NATIONS and not neutral) else 0

    elo_a    = elo_dict[team_a] + boost_a
    elo_b    = elo_dict[team_b] + boost_b
    elo_diff = np.clip(elo_a - elo_b, -ELO_DIFF_CAP, ELO_DIFF_CAP)
    elo_sum  = (elo_a + elo_b) / 2

    # Standardize manually — same as scaler_neutral.transform but no pandas overhead
    diff_scaled = (elo_diff - _smean[0]) / _sstd[0]
    sum_scaled  = (elo_sum  - _smean[1]) / _sstd[1]

    # log(λ) = const + coef_diff * diff_scaled + coef_sum * sum_scaled
    log_lam_a = _coef[0] + _coef[1] *  diff_scaled + _coef[2] * sum_scaled
    log_lam_b = _coef[0] + _coef[1] * -diff_scaled + _coef[2] * sum_scaled

    return np.exp(log_lam_a), np.exp(log_lam_b)


# ─────────────────────────────────────────────
# 7. MATCH PROBABILITY + VALIDATION
# ─────────────────────────────────────────────
def match_probabilities(la, lb, max_goals=MAX_GOALS_PER_TEAM + 1):
    scores = np.array([
        [poisson.pmf(i, la) * poisson.pmf(j, lb) for j in range(max_goals)]
        for i in range(max_goals)
    ])
    p_home = np.tril(scores, -1).sum()
    p_away = np.triu(scores, +1).sum()
    p_draw = np.trace(scores)
    total  = p_home + p_away + p_draw
    return p_home / total, p_draw / total, p_away / total

def validate(df, label=""):
    records = []
    for _, row in df.iterrows():
        la, lb = predict_lambda(row["home_team"], row["away_team"], raw_computed_elo, neutral=row["neutral"])
        ph, pd_, pa = match_probabilities(la, lb)
        records.append({
            "p_home": ph, "p_draw": pd_, "p_away": pa,
            "actual_h": int(row["home_score"] > row["away_score"]),
            "actual_d": int(row["home_score"] == row["away_score"]),
            "actual_a": int(row["home_score"] < row["away_score"]),
            "predicted": np.argmax([ph, pd_, pa]),
            "actual":    np.argmax([
                int(row["home_score"] > row["away_score"]),
                int(row["home_score"] == row["away_score"]),
                int(row["home_score"] < row["away_score"]),
            ]),
        })
    val = pd.DataFrame(records)
    acc = (val["predicted"] == val["actual"]).mean()
    ll  = log_loss(
        val[["actual_h", "actual_d", "actual_a"]].values,
        val[["p_home",   "p_draw",   "p_away"]].values
    )
    print(f"\n=== Validation: {label} ({len(val)} matches) ===")
    print(f"  Accuracy:         {acc:.3f}")
    print(f"  Log loss:         {ll:.3f}")
    print(f"  Avg P(draw):      {val['p_draw'].mean():.3f}  (historical WC: ~0.22)")
    print(f"  Actual draw rate: {val['actual_d'].mean():.3f}")
    return val

wc_test2 = add_features(test_df[test_df["tournament"] == "FIFA World Cup"].copy())
# validate(wc_test2, "WC 2018 + 2022")

# ─────────────────────────────────────────────
# 8. MATCH SIMULATOR
# ─────────────────────────────────────────────
def simulate_penalties(team_a, team_b, elo_a, elo_b):
    elo_diff = np.clip(elo_a - elo_b, -ELO_DIFF_CAP, ELO_DIFF_CAP)
    p_a_wins = 0.50 + 0.0001 * elo_diff
    return team_a if np.random.random() < p_a_wins else team_b

def simulate_match(team_a, team_b, elo_a, elo_b, elo_dict,
                   neutral=True, knockout=False):
    lam_a, lam_b = predict_lambda_fast(team_a, team_b, elo_dict, neutral=neutral)

    goals_a = min(np.random.poisson(lam_a), MAX_GOALS_PER_TEAM)
    goals_b = min(np.random.poisson(lam_b), MAX_GOALS_PER_TEAM)

    result = {
        "team_a": team_a, "team_b": team_b,
        "goals_a": goals_a, "goals_b": goals_b,
        "goals_a_et": None, "goals_b_et": None,
        "winner": None,
        "went_to_et": False, "went_to_pens": False,
    }

    if goals_a > goals_b:
        result["winner"] = team_a
    elif goals_b > goals_a:
        result["winner"] = team_b
    else:
        if not knockout:
            return result

        et_a = min(np.random.poisson(lam_a * 0.33), MAX_GOALS_ET)
        et_b = min(np.random.poisson(lam_b * 0.33), MAX_GOALS_ET)
        result.update({"went_to_et": True, "goals_a_et": et_a, "goals_b_et": et_b})

        total_a = goals_a + et_a
        total_b = goals_b + et_b

        if total_a > total_b:
            result["winner"] = team_a
        elif total_b > total_a:
            result["winner"] = team_b
        else:
            result["went_to_pens"] = True
            result["winner"] = simulate_penalties(team_a, team_b, elo_a, elo_b)

    return result

# 9. GROUP STAGE SIMULATOR
# ─────────────────────────────────────────────

# Which matches are NOT neutral (host nation playing at home)
def is_neutral(team_a, team_b):
    return not (team_a in HOST_NATIONS or team_b in HOST_NATIONS)

def sort_standings(table, match_results):
    """
    Sort group standings by FIFA tiebreaker rules:
    1. Points
    2. Goal difference
    3. Goals scored
    4. Head-to-head points
    5. Head-to-head goal difference
    6. Head-to-head goals scored
    7. ELO (proxy for drawing of lots)
    """
    teams = list(table.keys())

    # Build head-to-head record for every pair
    h2h = {t: {"pts": 0, "gd": 0, "gf": 0} for t in teams}
    for r in match_results:
        a, b   = r["team_a"], r["team_b"]
        ga, gb = r["goals_a"], r["goals_b"]
        if ga > gb:
            h2h[a]["pts"] += 3
        elif gb > ga:
            h2h[b]["pts"] += 3
        else:
            h2h[a]["pts"] += 1
            h2h[b]["pts"] += 1
        h2h[a]["gd"] += ga - gb
        h2h[b]["gd"] += gb - ga
        h2h[a]["gf"] += ga
        h2h[b]["gf"] += gb

    rows = []
    for team, stats in table.items():
        rows.append({
            "team":     team,
            "pts":      stats["pts"],
            "gd":       stats["gd"],
            "gf":       stats["gf"],
            "ga":       stats["ga"],
            "w":        stats["w"],
            "d":        stats["d"],
            "l":        stats["l"],
            "h2h_pts":  h2h[team]["pts"],
            "h2h_gd":   h2h[team]["gd"],
            "h2h_gf":   h2h[team]["gf"],
            "elo":      raw_computed_elo[team],
        })

    standings = pd.DataFrame(rows).sort_values(
        ["pts", "gd", "gf", "h2h_pts", "h2h_gd", "h2h_gf", "elo"],
        ascending=False
    ).reset_index(drop=True)
    standings["pos"] = standings.index + 1
    return standings

def simulate_group(group_teams, current_elo):
    table = {team: {
        "pts": 0, "gf": 0, "ga": 0, "gd": 0, "w": 0, "d": 0, "l": 0
    } for team in group_teams}
    match_results = []

    for team_a, team_b in combinations(group_teams, 2):
        neutral = is_neutral(team_a, team_b)
        r = simulate_match(
            team_a, team_b,
            current_elo[team_a], current_elo[team_b],
            current_elo,
            neutral=neutral, knockout=False
        )
        match_results.append(r)

        ga, gb = r["goals_a"], r["goals_b"]
        table[team_a]["gf"] += ga;  table[team_a]["ga"] += gb
        table[team_a]["gd"] += ga - gb
        table[team_b]["gf"] += gb;  table[team_b]["ga"] += ga
        table[team_b]["gd"] += gb - ga

        if ga > gb:
            table[team_a]["pts"] += 3; table[team_a]["w"] += 1
            table[team_b]["l"]   += 1
        elif gb > ga:
            table[team_b]["pts"] += 3; table[team_b]["w"] += 1
            table[team_a]["l"]   += 1
        else:
            table[team_a]["pts"] += 1; table[team_a]["d"] += 1
            table[team_b]["pts"] += 1; table[team_b]["d"] += 1

        update_elo(team_a, team_b, ga, gb, neutral, current_elo)

    # Use proper tiebreaker sort
    standings = sort_standings(table, match_results)
    return standings, match_results

def update_elo(team_a, team_b, goals_a, goals_b, neutral, elo_dict):
    """Update elo_dict in place after a simulated match."""
    elo_a = elo_dict[team_a] + (0 if neutral else HOME_ADVANTAGE)
    elo_b = elo_dict[team_b]

    exp_a = expected_score(elo_a, elo_b)
    exp_b = 1 - exp_a
    res_a = match_result(goals_a, goals_b)
    res_b = 1 - res_a

    K  = K_BASE * K_TOURNAMENT["FIFA World Cup"]
    GI = goal_index(goals_a, goals_b)

    elo_dict[team_a] += K * GI * (res_a - exp_a)
    elo_dict[team_b] += K * GI * (res_b - exp_b)

def simulate_all_groups(groups, base_elo):
    """
    Simulate all 12 groups.
    Returns:
      - all_standings: dict of {group_label: standings_df}
      - qualified:     dict with 1st, 2nd place per group + all 3rd place teams
      - all_matches:   flat list of all group stage results
      - run_elo:       elo dict after all group matches
    """
    run_elo     = base_elo.copy()
    all_standings = {}
    third_place   = []
    all_matches   = []
    qualified     = {"first": {}, "second": {}}

    for label, teams in groups.items():
        standings, matches = simulate_group(teams, run_elo)
        all_standings[label] = standings
        all_matches.extend(matches)

        qualified["first"][label]  = standings.iloc[0]["team"]
        qualified["second"][label] = standings.iloc[1]["team"]
        third_place.append({
            "group": label,
            "team":  standings.iloc[2]["team"],
            "pts":   standings.iloc[2]["pts"],
            "gd":    standings.iloc[2]["gd"],
            "gf":    standings.iloc[2]["gf"],
            "elo":   run_elo[standings.iloc[2]["team"]],
        })

    # Pick best 8 third-place teams
    third_df = pd.DataFrame(third_place).sort_values(
        ["pts", "gd", "gf", "elo"], ascending=False
    ).reset_index(drop=True)
    qualified["third"] = third_df.head(8)["team"].tolist()
    qualified["third_full"] = third_df  # keep full table for bracket assignment

    return all_standings, qualified, all_matches, run_elo

REBUILD_THIRD_PLACE_TABLE = False

def build_third_place_table():
    url = "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_knockout_stage"
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(resp.text, "lxml")

    target_table = None
    for table in soup.find_all("table", class_="wikitable"):
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        if any("1A" in h for h in headers):
            target_table = table
            break

    if target_table is None:
        raise ValueError("Could not find the combination table")

    valid_groups  = set("ABCDEFGHIJKL")
    # The 8 group winner slots whose opponents we need, in table column order
    gw_order = ["1A", "1B", "1D", "1E", "1G", "1I", "1K", "1L"]

    rows = target_table.find_all("tr")[1:]
    table_dict = {}

    for row in rows:
        cells = [td.get_text(strip=True) for td in row.find_all(["td", "th"])]
        if len(cells) < 18:
            continue

        # Collect all single-letter group names → the 8 qualifying groups
        groups = frozenset(c for c in cells if c in valid_groups)
        if len(groups) != 8:
            continue

        # Collect all "3X" values in order → they map to gw_order
        assignments_ordered = [c for c in cells if len(c) == 2
                                and c[0] == "3" and c[1] in valid_groups]
        if len(assignments_ordered) != 8:
            continue

        assignment = dict(zip(gw_order, assignments_ordered))
        table_dict[groups] = assignment

    print(f"Parsed {len(table_dict)} combinations (expected 495)")
    test_key = frozenset("EFGHIJKL")
    if test_key in table_dict:
        print(f"Verification row 1: {table_dict[test_key]}")
    else:
        print("WARNING: verification row 1 not found")

    return table_dict


# ── Save to JSON for reuse (frozensets → sorted strings as keys) ──────────────
def save_table(table, path):
    serializable = {
        ",".join(sorted(k)): v
        for k, v in table.items()
    }
    with open(path, "w") as f:
        json.dump(serializable, f)
    print(f"Saved {len(serializable)} rows to {path}")

def load_table(path):
    with open(path) as f:
        raw = json.load(f)
    return {frozenset(k.split(",")): v for k, v in raw.items()}

save_path = os.path.join(DRIVE_PATH, "third_place_table.json")


if REBUILD_THIRD_PLACE_TABLE:
    THIRD_PLACE_TABLE = build_third_place_table()
    save_table(THIRD_PLACE_TABLE, save_path)
else:
    THIRD_PLACE_TABLE = load_table(save_path)

# ─────────────────────────────────────────────
# 10. ROUND OF 32 BRACKET + FULL KNOCKOUT
# ─────────────────────────────────────────────

# Fixed R32 matchups (group winners vs runners-up — these never change)
# Format: (team_a_slot, team_b_slot)
# Slots: "1X" = winner group X, "2X" = runner-up group X, "3?" = third place
R32_FIXED = [
    ("2A", "2B"),   # Match 73
    ("1E", "3?"),   # Match 74 — third from A/B/C/D/F
    ("1F", "2C"),   # Match 75
    ("1C", "2F"),   # Match 76
    ("1I", "3?"),   # Match 77 — third from C/D/F/G/H
    ("2E", "2I"),   # Match 78
    ("1A", "3?"),   # Match 79 — third from C/E/F/H/I
    ("1L", "3?"),   # Match 80 — third from E/H/I/J/K
    ("1D", "3?"),   # Match 81 — third from B/E/F/I/J
    ("1G", "3?"),   # Match 82 — third from A/E/H/I/J
    ("2K", "2L"),   # Match 83
    ("1H", "2J"),   # Match 84
    ("1B", "3?"),   # Match 85 — third from E/F/G/I/J
    ("1J", "2H"),   # Match 86
    ("1K", "3?"),   # Match 87 — third from D/E/I/J/L
    ("2D", "2G"),   # Match 88
]

def resolve_r32_bracket(qualified):
    """
    Resolve all 16 R32 matchups using the FIFA combination table.
    Returns list of (team_a, team_b) tuples in match order.
    """
    # ── Build slot → team mapping ─────────────────────────────────────────────
    slots = {}
    for g, team in qualified["first"].items():
        slots[f"1{g}"] = team
    for g, team in qualified["second"].items():
        slots[f"2{g}"] = team

    # ── Resolve third-place slots from the combination table ──────────────────
    third_groups  = frozenset(qualified["third_full"].head(8)["group"].tolist())
    third_by_group = {
        row["group"]: row["team"]
        for _, row in qualified["third_full"].head(8).iterrows()
    }

    third_assignment = THIRD_PLACE_TABLE.get(third_groups)
    if third_assignment is None:
        print(f"WARNING: combination {sorted(third_groups)} not in table")
        # Fallback: assign best third-place teams in order to slots that need them
        third_teams = qualified["third_full"].head(8)["team"].tolist()
        slots_needing_third = [s for s, _ in R32_FIXED if _ == "3?"]
        # Won't happen if table is complete — but just in case
        third_assignment = {}

    # Map "3X" codes → actual team names and store in slots
    # Key: which group winner slot (e.g. "1E") gets which third-place team (e.g. "3F")
    for gw_slot, third_code in third_assignment.items():
        group_letter = third_code[1]   # "3F" → "F"
        team = third_by_group.get(group_letter)
        if team:
            slots[f"third_for_{gw_slot}"] = team

    # ── Build the 16 matchups ─────────────────────────────────────────────────
    matchups = []
    for slot_a, slot_b in R32_FIXED:
        team_a = slots.get(slot_a, "TBD")

        if slot_b == "3?":
            # Look up which third-place team this group winner faces
            team_b = slots.get(f"third_for_{slot_a}", "TBD")
        else:
            team_b = slots.get(slot_b, "TBD")

        matchups.append((team_a, team_b))

    return matchups

def simulate_knockout_stage(qualified, run_elo):
    """
    Simulate from R32 through the Final.
    Returns dict with results per round and the champion.
    """
    rounds = {}

    # ── Round of 32 ──────────────────────────────────────────────────────────
    r32_matchups = resolve_r32_bracket(qualified)
    r32_results  = []
    r16_teams    = []

    for team_a, team_b in r32_matchups:
        r = simulate_match(team_a, team_b,
                           run_elo[team_a], run_elo[team_b],
                           run_elo, neutral=True, knockout=True)
        r32_results.append(r)
        r16_teams.append(r["winner"])
        update_elo(team_a, team_b, r["goals_a"], r["goals_b"], True, run_elo)
    rounds["R32"] = r32_results

    # ── Round of 16 (winners paired sequentially: 0v1, 2v3, ...) ────────────
    def simulate_round(teams, round_name):
        results  = []
        winners  = []
        for i in range(0, len(teams), 2):
            a, b = teams[i], teams[i+1]
            r = simulate_match(a, b, run_elo[a], run_elo[b],
                               run_elo, neutral=True, knockout=True)
            results.append(r)
            winners.append(r["winner"])
            update_elo(a, b, r["goals_a"], r["goals_b"], True, run_elo)
        rounds[round_name] = results
        return winners

    r16_winners = simulate_round(r16_teams,      "R16")
    qf_winners  = simulate_round(r16_winners,    "QF")
    sf_winners  = simulate_round(qf_winners,     "SF")
    sf_losers   = [r["team_a"] if r["winner"] == r["team_b"] else r["team_b"]
                   for r in rounds["SF"]]

    # Third place
    tp = simulate_match(sf_losers[0], sf_losers[1],
                        run_elo[sf_losers[0]], run_elo[sf_losers[1]],
                        run_elo, neutral=True, knockout=True)
    rounds["TP"] = [tp]

    # Final
    final = simulate_match(sf_winners[0], sf_winners[1],
                           run_elo[sf_winners[0]], run_elo[sf_winners[1]],
                           run_elo, neutral=True, knockout=True)
    rounds["Final"] = [final]

    return rounds, final["winner"]

# ─────────────────────────────────────────────
# 11. FULL TOURNAMENT RUNNER + RUN STORAGE
# ─────────────────────────────────────────────
import json, time

def run_tournament(run_id, base_elo, groups):
    """Simulate one full tournament. Returns a compact result dict."""
    run_elo = base_elo.copy()

    # Group stage
    all_standings, qualified, group_matches, run_elo = simulate_all_groups(groups, run_elo)

    # Knockout stage
    ko_rounds, champion = simulate_knockout_stage(qualified, run_elo)

    # ── Compact storage format ────────────────────────────────────────────────
    def match_to_dict(r):
        return {
            "a": r["team_a"], "b": r["team_b"],
            "ga": r["goals_a"], "gb": r["goals_b"],
            "w": r["winner"],
            "et": r["went_to_et"], "pen": r["went_to_pens"],
            "goals_a_et": r["goals_a_et"],
            "goals_b_et": r["goals_b_et"], 
        }

    result = {
        "run_id":   run_id,
        "champion": champion,
        "finalist": [m["team_a"] if m["winner"] != m["team_a"]
                     else m["team_b"] for m in ko_rounds["Final"]] + [champion],
        "sf":  [r["winner"] for r in ko_rounds["SF"]] +
               [r["team_a"] if r["winner"] == r["team_b"] else r["team_b"]
                for r in ko_rounds["SF"]],
        "groups": {
            g: {
                "standings": df[["team","pts","gd","gf","ga"]].to_dict("records"),
                "qualified": {
                    "first":  qualified["first"][g],
                    "second": qualified["second"][g],
                }
            }
            for g, df in all_standings.items()
        },
        "third_qualified": qualified["third"],
        "matches": {
            "group":  [match_to_dict(m) for m in group_matches],
            "R32":    [match_to_dict(m) for m in ko_rounds["R32"]],
            "R16":    [match_to_dict(m) for m in ko_rounds["R16"]],
            "QF":     [match_to_dict(m) for m in ko_rounds["QF"]],
            "SF":     [match_to_dict(m) for m in ko_rounds["SF"]],
            "TP":     [match_to_dict(m) for m in ko_rounds["TP"]],
            "Final":  [match_to_dict(m) for m in ko_rounds["Final"]],
        },
        "raw_computed_elo": {t: round(run_elo[t], 1) for t in wc_teams},
    }
    return result

def run_simulations(n, base_elo, groups, save_path=None, print_every=100):
    """
    Run n full tournament simulations.
    Returns list of result dicts. Optionally saves to a .jsonl file
    (one JSON object per line — easy to stream/append later).
    """
    results = []
    t0 = time.time()

    if save_path:
        f = open(save_path, "w")

    for i in range(n):
        r = run_tournament(i, base_elo, groups)
        results.append(r)

        if save_path:
            f.write(json.dumps(r) + "\n")

        if (i + 1) % print_every == 0:
            elapsed = time.time() - t0
            rate    = (i + 1) / elapsed
            print(f"  Run {i+1:>6}/{n}  |  {rate:.1f} runs/sec  |  "
                  f"ETA {(n - i - 1) / rate:.0f}s  |  "
                  f"Last champion: {r['champion']}")

    if save_path:
        f.close()

    elapsed = time.time() - t0
    print(f"\nDone. {n} runs in {elapsed:.1f}s ({n/elapsed:.1f} runs/sec)")
    return results

def run_batch(args):
    """Worker function — runs a chunk of simulations in one process."""
    run_ids, base_elo, groups, seed = args
    np.random.seed(seed)  # different seed per process for independent randomness
    results = []
    for run_id in run_ids:
        r = run_tournament(run_id, base_elo, groups)
        results.append(r)
    return results

def run_simulations_parallel(n, base_elo, groups, save_path=None,
                             n_workers=None, chunk_size=500):
    if n_workers is None:
        n_workers = cpu_count()

    print(f"Running {n} simulations across {n_workers} workers")

    run_ids = list(range(n))
    chunks  = [run_ids[i:i+chunk_size] for i in range(0, n, chunk_size)]
    args    = [(chunk, base_elo, groups, i * 12345) for i, chunk in enumerate(chunks)]

    t0          = time.time()
    all_results = []
    f           = open(save_path, "w") if save_path else None

    with Pool(n_workers) as pool:
        for batch in pool.imap(run_batch, args):
            all_results.extend(batch)

            if f:
                for r in batch:
                    f.write(json.dumps(r) + "\n")

            # Report based on wall time since last chunk arrival
            completed = len(all_results)
            elapsed   = time.time() - t0
            # Use only the last portion of elapsed time for a stable rate
            # by measuring from when we had (completed - chunk_size) runs
            rate      = completed / elapsed  # overall average — most stable metric
            eta       = (n - completed) / rate if rate > 0 else 0

            print(f"  Completed {completed:>6}/{n}  |  "
                  f"{rate:.1f} runs/sec (avg)  |  ETA {eta:.0f}s")

    if f:
        f.close()

    elapsed = time.time() - t0
    print(f"\nDone. {n} runs in {elapsed:.1f}s ({n/elapsed:.1f} runs/sec)")
    return all_results

if __name__ == "__main__":
    print(f"CPU cores available: {cpu_count()}")

    batch_parallel = run_simulations_parallel(
        100000, eloratings_net_elo, WC2026_GROUPS,
        save_path="data/simulation_runs_100k_parallel.jsonl",
        n_workers=cpu_count(),
        chunk_size=500
    )

    from collections import Counter
    champs    = Counter(r["champion"] for r in batch_parallel)
    finalists = Counter(t for r in batch_parallel for t in r["finalist"])
    semis     = Counter(t for r in batch_parallel for t in r["sf"])

    print(f"\n=== Champion probability (top 20) ===")
    for team, count in champs.most_common(20):
        bar = "█" * int(count / 100)
        print(f"  {team:<28} {count/100:5.1f}%  {bar}")

    print(f"\n=== Finalist probability (top 20) ===")
    for team, count in finalists.most_common(20):
        print(f"  {team:<28} {count/100:5.1f}%")

    print(f"\n=== Semi-final probability (top 20) ===")
    for team, count in semis.most_common(20):
        print(f"  {team:<28} {count/100:5.1f}%")
    
    print("\n=== Sanity check: ET without PEN integrity ===")
    violations = []
    for run in batch_parallel:
        for stage, matches in run["matches"].items():
            for m in matches:
                if m["et"] and not m["pen"]:
                    # ET happened but no penalties — scores must differ
                    total_a = m["ga"] + (m.get("goals_a_et") or 0)
                    total_b = m["gb"] + (m.get("goals_b_et") or 0)
                    if total_a == total_b:
                        violations.append({
                            "run_id": run["run_id"],
                            "stage":  stage,
                            "match":  f"{m['a']} {m['ga']}+{m.get('goals_a_et',0)} vs "
                                    f"{m['b']} {m['gb']}+{m.get('goals_b_et',0)}",
                            "winner": m["w"],
                        })

    if violations:
        print(f"  ❌ Found {len(violations)} violations:")
        for v in violations[:10]:  # show first 10
            print(f"     Run {v['run_id']} {v['stage']}: {v['match']} → {v['winner']}")
    else:
        print(f"  ✅ No violations found across {len(batch_parallel)} runs")