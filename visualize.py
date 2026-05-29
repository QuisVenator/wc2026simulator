# visualize.py
import sys
import json
import argparse
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from collections import Counter
from pathlib import Path
from wc_strings import t, stage_label
from huggingface_hub import hf_hub_download
import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))
os.environ["HF_HOME"] = os.path.join(APP_DIR, ".hf_cache")

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
FLAGS = {
    "Algeria":                "🇩🇿",
    "Argentina":              "🇦🇷",
    "Australia":              "🇦🇺",
    "Austria":                "🇦🇹",
    "Belgium":                "🇧🇪",
    "Bosnia and Herzegovina": "🇧🇦",
    "Brazil":                 "🇧🇷",
    "Canada":                 "🇨🇦",
    "Cape Verde":             "🇨🇻",
    "Colombia":               "🇨🇴",
    "Croatia":                "🇭🇷",
    "Curaçao":                "🇨🇼",
    "Czech Republic":         "🇨🇿",
    "DR Congo":               "🇨🇩",
    "Ecuador":                "🇪🇨",
    "Egypt":                  "🇪🇬",
    "England":                "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
    "France":                 "🇫🇷",
    "Germany":                "🇩🇪",
    "Ghana":                  "🇬🇭",
    "Haiti":                  "🇭🇹",
    "Iran":                   "🇮🇷",
    "Iraq":                   "🇮🇶",
    "Ivory Coast":            "🇨🇮",
    "Japan":                  "🇯🇵",
    "Jordan":                 "🇯🇴",
    "Mexico":                 "🇲🇽",
    "Morocco":                "🇲🇦",
    "Netherlands":            "🇳🇱",
    "New Zealand":            "🇳🇿",
    "Norway":                 "🇳🇴",
    "Panama":                 "🇵🇦",
    "Paraguay":               "🇵🇾",
    "Portugal":               "🇵🇹",
    "Qatar":                  "🇶🇦",
    "Saudi Arabia":           "🇸🇦",
    "Scotland":               "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "Senegal":                "🇸🇳",
    "South Africa":           "🇿🇦",
    "South Korea":            "🇰🇷",
    "Spain":                  "🇪🇸",
    "Sweden":                 "🇸🇪",
    "Switzerland":            "🇨🇭",
    "Tunisia":                "🇹🇳",
    "Turkey":                 "🇹🇷",
    "United States":          "🇺🇸",
    "Uruguay":                "🇺🇾",
    "Uzbekistan":             "🇺🇿",
}

STAGES = ["group", "R32", "R16", "QF", "SF", "final", "champion"]

CONFEDERATION = {
    "Argentina": "CONMEBOL", "Brazil": "CONMEBOL", "Colombia": "CONMEBOL",
    "Ecuador": "CONMEBOL", "Paraguay": "CONMEBOL", "Uruguay": "CONMEBOL",
    "Spain": "UEFA", "France": "UEFA", "England": "UEFA", "Germany": "UEFA",
    "Netherlands": "UEFA", "Portugal": "UEFA", "Belgium": "UEFA",
    "Croatia": "UEFA", "Switzerland": "UEFA", "Austria": "UEFA",
    "Norway": "UEFA", "Sweden": "UEFA", "Scotland": "UEFA",
    "Bosnia and Herzegovina": "UEFA", "Czech Republic": "UEFA", "Turkey": "UEFA",
    "Japan": "AFC", "South Korea": "AFC", "Australia": "AFC", "Iran": "AFC",
    "Saudi Arabia": "AFC", "Iraq": "AFC", "Jordan": "AFC",
    "Qatar": "AFC", "Uzbekistan": "AFC",
    "Morocco": "CAF", "Senegal": "CAF", "Egypt": "CAF", "Ghana": "CAF",
    "Ivory Coast": "CAF", "Algeria": "CAF", "Tunisia": "CAF",
    "DR Congo": "CAF", "South Africa": "CAF", "Cape Verde": "CAF",
    "United States": "CONCACAF", "Mexico": "CONCACAF", "Canada": "CONCACAF",
    "Panama": "CONCACAF", "Haiti": "CONCACAF", "Curaçao": "CONCACAF",
    "New Zealand": "OFC",
}

CONF_COLORS = {
    "UEFA":     "#3B82F6",
    "CONMEBOL": "#10B981",
    "AFC":      "#F59E0B",
    "CAF":      "#EF4444",
    "CONCACAF": "#8B5CF6",
    "OFC":      "#6B7280",
}

WC2026_GROUPS = {
    "A": ["Mexico", "South Korea", "South Africa", "Czech Republic"],
    "B": ["Canada", "Switzerland", "Qatar", "Bosnia and Herzegovina"],
    "C": ["Brazil", "Morocco", "Scotland", "Haiti"],
    "D": ["United States", "Paraguay", "Australia", "Turkey"],
    "E": ["Germany", "Curaçao", "Ivory Coast", "Ecuador"],
    "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
    "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
    "H": ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
    "I": ["France", "Senegal", "Norway", "Iraq"],
    "J": ["Argentina", "Algeria", "Austria", "Jordan"],
    "K": ["Portugal", "Colombia", "Uzbekistan", "DR Congo"],
    "L": ["England", "Croatia", "Ghana", "Panama"],
}

def flag(team):
    return FLAGS.get(team, "🏳")

# ─────────────────────────────────────────────
# 0. ARGUMENT PARSING
# ─────────────────────────────────────────────
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo",     type=str,
                        default="QuisVenator/wc2026_simulation",
                        help="Hugging Face dataset repo ID")
    parser.add_argument("--filename", type=str,
                        default="simulation_runs_10k_parallel.jsonl",
                        help="Filename within the dataset repo")
    parser.add_argument("--file",     type=str, default=None,
                        help="Local file path (overrides --repo if provided)")
    try:
        args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    except ValueError:
        args = parser.parse_args()
    return args

# ─────────────────────────────────────────────
# 1. DATA LOADING + AGGREGATION
# ─────────────────────────────────────────────
def get_exit_round(run, team):
    if run["champion"] == team:
        return "champion"
    if team in run["finalist"]:
        return "final"
    if team in run["sf"]:
        return "SF"
    for stage in ["QF", "R16", "R32"]:
        for m in run["matches"][stage]:
            if (m["a"] == team or m["b"] == team) and m["w"] != team:
                return stage
    return "group"

def get_eliminated_by(run, team):
    if run["champion"] == team:
        return None
    for stage in ["final", "SF", "QF", "R16", "R32"]:
        for m in run["matches"].get(stage, []):
            if (m["a"] == team or m["b"] == team) and m["w"] != team:
                return m["w"]
    return None

@st.cache_data
def load_data(filepath=None, repo=None, filename=None):
    runs = []

    if filepath:
        with open(filepath) as f:
            for line in f:
                if line.strip():
                    runs.append(json.loads(line))
    else:
        cache_path = f"/tmp/{filename}"
        if not os.path.exists(cache_path):
            with st.spinner("Downloading simulation data from Hugging Face..."):
                cache_path = hf_hub_download(
                    repo_id=repo,
                    filename=filename,
                    repo_type="dataset",
                    local_dir="/tmp",
                )

        with open(cache_path) as f:
            for line in f:
                if line.strip():
                    runs.append(json.loads(line))

    n = len(runs)
    all_teams = sorted(CONFEDERATION.keys())

    team_stats = {}
    for team in all_teams:
        exits      = Counter(get_exit_round(run, team) for run in runs)
        elim_by    = Counter(
            get_eliminated_by(run, team) for run in runs
            if get_eliminated_by(run, team) is not None
        )
        winning_ids = [r["run_id"] for r in runs if r["champion"] == team]

        reached = {}
        for stage in STAGES:
            if stage == "group":
                reached[stage] = exits.get("group", 0) / n
            else:
                idx = STAGES.index(stage)
                reached[stage] = sum(exits.get(s, 0) for s in STAGES[idx:]) / n

        team_stats[team] = {
            "exits":         dict(exits),
            "eliminated_by": elim_by.most_common(10),
            "winning_ids":   winning_ids,
            "reached":       reached,
            "champion_pct":  exits.get("champion", 0) / n * 100,
            "conf":          CONFEDERATION.get(team, "Other"),
        }

    group_stats = {}
    for g, teams in WC2026_GROUPS.items():
        group_stats[g] = {team: {"pos_counts": Counter()} for team in teams}
        for run in runs:
            standings = run["groups"][g]["standings"]
            for i, row in enumerate(standings):
                group_stats[g][row["team"]]["pos_counts"][i + 1] += 1

    return runs, team_stats, group_stats, n

# ─────────────────────────────────────────────
# 2. GLOBAL / RUN STATS
# ─────────────────────────────────────────────
def show_tournament_stats(runs, lang):
    st.markdown(f"#### {t('global_stats_title', lang)}")

    total_matches = total_goals = total_draws = total_et = total_pen = 0
    max_goals_ever  = 0
    max_goals_match = None

    for run in runs:
        all_matches = (
            run["matches"]["group"] +
            run["matches"]["R32"]   +
            run["matches"]["R16"]   +
            run["matches"]["QF"]    +
            run["matches"]["SF"]    +
            run["matches"]["TP"]    +
            run["matches"]["Final"]
        )
        for m in all_matches:
            ga, gb = m["ga"], m["gb"]
            et_a   = m.get("goals_a_et") or 0
            et_b   = m.get("goals_b_et") or 0
            tg     = ga + gb + et_a + et_b

            total_matches += 1
            total_goals   += ga + gb
            if ga == gb and not m.get("et"):
                total_draws += 1
            if m.get("et"):
                total_et  += 1
            if m.get("pen"):
                total_pen += 1
            if tg > max_goals_ever:
                max_goals_ever  = tg
                max_goals_match = m

    n = len(runs)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric(t("stat_avg_goals", lang), f"{total_goals/total_matches:.2f}")
    c2.metric(t("stat_avg_draws", lang), f"{total_draws/n:.1f}")
    c3.metric(t("stat_avg_aet",   lang), f"{total_et/n:.1f}")
    c4.metric(t("stat_avg_pen",   lang), f"{total_pen/n:.1f}")
    if max_goals_match:
        c5.metric(
            t("stat_highest_scoring", lang),
            t("stat_goals_suffix", lang, n=max_goals_ever),
            f"{flag(max_goals_match['a'])} {max_goals_match['a']} "
            f"{max_goals_match['ga']}–{max_goals_match['gb']} "
            f"{max_goals_match['b']} {flag(max_goals_match['b'])}"
        )
    st.divider()


def show_run_stats(run, lang):
    all_matches = (
        run["matches"]["R32"]   +
        run["matches"]["R16"]   +
        run["matches"]["QF"]    +
        run["matches"]["SF"]    +
        run["matches"]["TP"]    +
        run["matches"]["Final"]
    )
    group_matches = run["matches"]["group"]
    all_inc_group = group_matches + all_matches

    total       = len(all_inc_group)
    draws_group = sum(1 for m in group_matches if m["ga"] == m["gb"])
    went_et     = sum(1 for m in all_matches if m.get("et", False))
    went_pen    = sum(1 for m in all_matches if m.get("pen", False))
    total_goals = sum(m["ga"] + m["gb"] for m in all_inc_group)
    avg_goals   = total_goals / total if total else 0

    def total_g(m):
        return m["ga"] + m["gb"] + (m.get("goals_a_et") or 0) + (m.get("goals_b_et") or 0)

    def margin(m):
        return abs(m["ga"] - m["gb"])

    most_goals_match = max(all_inc_group, key=total_g)
    most_goals       = total_g(most_goals_match)
    biggest_win      = max(all_inc_group, key=margin)

    goals_by_team = Counter()
    for m in all_inc_group:
        goals_by_team[m["a"]] += m["ga"]
        goals_by_team[m["b"]] += m["gb"]
    top_team, top_goals = goals_by_team.most_common(1)[0]

    st.markdown(f"#### {t('run_stats_title', lang)}")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric(t("stat_total_matches",  lang), total)
    c2.metric(t("stat_group_draws",    lang),
              f"{draws_group} ({draws_group/len(group_matches)*100:.0f}%)")
    c3.metric(t("stat_went_aet",       lang), went_et)
    c4.metric(t("stat_decided_pen",    lang), went_pen)
    c5.metric(t("stat_avg_goals_game", lang), f"{avg_goals:.2f}")
    c6.metric(t("stat_most_goals_game",lang),
              f"{most_goals} ({flag(most_goals_match['a'])} {most_goals_match['a']} "
              f"{most_goals_match['ga']}–{most_goals_match['gb']} "
              f"{most_goals_match['b']} {flag(most_goals_match['b'])})")

    c1, c2 = st.columns(2)
    c1.metric(
        t("stat_biggest_margin", lang),
        t("stat_biggest_margin_val", lang, n=margin(biggest_win)),
        f"{flag(biggest_win['a'])} {biggest_win['a']} "
        f"{biggest_win['ga']}–{biggest_win['gb']} "
        f"{biggest_win['b']} {flag(biggest_win['b'])}"
    )
    c2.metric(
        t("stat_most_goals_scored", lang),
        f"{flag(top_team)} {top_team}",
        t("stat_goals_all_matches", lang, n=top_goals)
    )
    st.divider()

# ─────────────────────────────────────────────
# 3. OVERVIEW VIEW
# ─────────────────────────────────────────────
def show_overview(team_stats, group_stats, n_runs, runs, lang):
    st.title(t("overview_title", lang))
    st.markdown(t("overview_subtitle", lang, n=n_runs))
    show_tournament_stats(runs, lang)

    # ── Champion probability bar chart ────────────────────────────────────────
    st.subheader(t("champion_prob", lang))

    rows = []
    for team, stats in team_stats.items():
        rows.append({
            t("col_team", lang): f"{flag(team)} {team}",
            "Champion %":        stats["champion_pct"],
            "Conf":              stats["conf"],
            "Color":             CONF_COLORS.get(stats["conf"], "#6B7280"),
        })
    df = pd.DataFrame(rows).sort_values("Champion %", ascending=True)

    fig = go.Figure(go.Bar(
        x=df["Champion %"],
        y=df[t("col_team", lang)],
        orientation="h",
        marker_color=df["Color"],
        text=df["Champion %"].map("{:.1f}%".format),
        textposition="outside",
        hovertemplate=f"<b>%{{y}}</b><br>{t('champion_prob', lang)}: %{{x:.1f}}%<extra></extra>",
    ))
    fig.update_layout(
        height=1200,
        margin=dict(l=10, r=60, t=10, b=10),
        xaxis_title=t("champion_prob_axis", lang),
        yaxis_title=None,
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="rgba(128,128,128,0.2)"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Confederation legend ──────────────────────────────────────────────────
    cols = st.columns(len(CONF_COLORS))
    for i, (conf, color) in enumerate(CONF_COLORS.items()):
        cols[i].markdown(
            f"<span style='color:{color}'>█</span> {conf}",
            unsafe_allow_html=True
        )

    st.divider()

    # ── Stage probability table ───────────────────────────────────────────────
    st.subheader(t("stage_reach", lang))

    stage_keys   = ["R32", "R16", "QF", "SF", "final", "champion"]
    stage_rows   = []
    for team, stats in team_stats.items():
        row = {
            t("col_team", lang): f"{flag(team)} {team}",
            t("col_conf", lang): stats["conf"],
        }
        for s in stage_keys:
            row[stage_label(s, lang)] = stats["reached"][s] * 100
        stage_rows.append(row)

    stage_df = pd.DataFrame(stage_rows).sort_values(
        stage_label("champion", lang), ascending=False
    )
    for s in stage_keys:
        lbl = stage_label(s, lang)
        stage_df[lbl] = stage_df[lbl].map("{:.1f}%".format)

    st.dataframe(stage_df, use_container_width=True, hide_index=True)
    st.divider()

    # ── Group stage summary ───────────────────────────────────────────────────
    st.subheader(t("group_summary", lang))

    gcols = st.columns(3)
    for i, (g, teams) in enumerate(WC2026_GROUPS.items()):
        with gcols[i % 3]:
            st.markdown(f"**{t('group_label', lang, g=g)}**")
            group_rows = []
            for team in teams:
                pos_counts = group_stats[g][team]["pos_counts"]
                total      = sum(pos_counts.values())
                group_rows.append({
                    t("col_team", lang): f"{flag(team)} {team}",
                    t("pos_1st",  lang): pos_counts.get(1, 0) / total * 100,
                    t("pos_2nd",  lang): pos_counts.get(2, 0) / total * 100,
                    t("pos_3rd",  lang): pos_counts.get(3, 0) / total * 100,
                    t("pos_4th",  lang): pos_counts.get(4, 0) / total * 100,
                })
            gdf = pd.DataFrame(group_rows).sort_values(t("pos_1st", lang), ascending=False)
            for col in [t("pos_1st", lang), t("pos_2nd", lang),
                        t("pos_3rd", lang), t("pos_4th", lang)]:
                gdf[col] = gdf[col].map("{:.0f}%".format)
            st.dataframe(gdf, use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────
# 4. TEAM DEEP DIVE VIEW
# ─────────────────────────────────────────────
def show_team_deep_dive(runs, team_stats, n_runs, lang):
    st.title(t("team_title", lang))

    all_teams    = sorted(team_stats.keys())
    team_display = {f"{flag(tm)} {tm}": tm for tm in all_teams}
    selected_display = st.selectbox(t("select_team", lang), list(team_display.keys()))
    team  = team_display[selected_display]
    stats = team_stats[team]
    conf  = stats["conf"]

    st.markdown(
        f"**{team}** · {conf} · "
        f"<span style='color:{CONF_COLORS.get(conf, '#888')}'>█</span>",
        unsafe_allow_html=True
    )
    st.divider()

    # ── Top metrics ───────────────────────────────────────────────────────────
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric(t("metric_champion",    lang), f"{stats['reached']['champion']*100:.1f}%")
    m2.metric(t("metric_reach_final", lang), f"{stats['reached']['final']*100:.1f}%")
    m3.metric(t("metric_reach_sf",    lang), f"{stats['reached']['SF']*100:.1f}%")
    m4.metric(t("metric_reach_qf",    lang), f"{stats['reached']['QF']*100:.1f}%")
    m5.metric(t("metric_reach_r16",   lang), f"{stats['reached']['R16']*100:.1f}%")

    st.divider()
    col_left, col_right = st.columns(2)

    # ── Stage funnel ──────────────────────────────────────────────────────────
    with col_left:
        st.subheader(t("progression_title", lang))
        funnel_stages = ["R32", "R16", "QF", "SF", "final", "champion"]
        funnel_labels = [stage_label(s, lang) for s in funnel_stages]
        funnel_values = [stats["reached"][s] * 100 for s in funnel_stages]

        fig = go.Figure(go.Funnel(
            y=funnel_labels,
            x=funnel_values,
            textinfo="value+percent initial",
            texttemplate="%{value:.1f}%",
            marker_color=[CONF_COLORS.get(conf, "#6B7280")] * len(funnel_stages),
        ))
        fig.update_layout(
            height=350,
            margin=dict(l=10, r=10, t=10, b=10),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Eliminated by ─────────────────────────────────────────────────────────
    with col_right:
        st.subheader(t("eliminated_by_title", lang))
        elim_data = stats["eliminated_by"]
        if elim_data:
            elim_teams  = [e[0] for e in elim_data]
            elim_counts = [e[1] for e in elim_data]
            elim_pcts   = [c / n_runs * 100 for c in elim_counts]

            fig2 = go.Figure(go.Bar(
                x=elim_pcts[::-1],
                y=[f"{flag(tm)} {tm}" for tm in elim_teams[::-1]],
                orientation="h",
                marker_color=[
                    CONF_COLORS.get(CONFEDERATION.get(tm, ""), "#6B7280")
                    for tm in elim_teams[::-1]
                ],
                text=[f"{p:.1f}%" for p in elim_pcts[::-1]],
                textposition="outside",
                hovertemplate=f"<b>%{{y}}</b><br>{t('eliminated_pct_axis', lang)}: %{{x:.1f}}%<extra></extra>",
            ))
            fig2.update_layout(
                height=350,
                margin=dict(l=10, r=60, t=10, b=10),
                xaxis_title=t("eliminated_pct_axis", lang),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(gridcolor="rgba(128,128,128,0.2)"),
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info(t("no_elim_data", lang))

    st.divider()

    # ── Exit round breakdown ──────────────────────────────────────────────────
    st.subheader(t("exit_round_title", lang))
    exit_data = stats["exits"]
    exit_cols = st.columns(len(STAGES))
    for i, stage in enumerate(STAGES):
        count = exit_data.get(stage, 0)
        pct   = count / n_runs * 100
        exit_cols[i].metric(
            stage_label(stage, lang),
            f"{pct:.1f}%",
            t("runs_label", lang, n=count)
        )

    st.divider()

    # ── Group performance ─────────────────────────────────────────────────────
    st.subheader(t("group_finish_title", lang))
    team_group = next((g for g, teams in WC2026_GROUPS.items() if team in teams), None)
    if team_group:
        group_teams = WC2026_GROUPS[team_group]
        st.markdown(t("group_teams_label", lang,
                      g=team_group, teams=", ".join(group_teams)))

        pos_rows = []
        for tm in group_teams:
            pos_counts = Counter()
            for run in runs:
                standings = run["groups"][team_group]["standings"]
                for i, row in enumerate(standings):
                    if row["team"] == tm:
                        pos_counts[i + 1] += 1
                        break
            total = sum(pos_counts.values())
            pos_rows.append({
                t("col_team", lang): f"{flag(tm)} {tm}",
                t("pos_1st",  lang): pos_counts.get(1, 0) / total * 100,
                t("pos_2nd",  lang): pos_counts.get(2, 0) / total * 100,
                t("pos_3rd",  lang): pos_counts.get(3, 0) / total * 100,
                t("pos_4th",  lang): pos_counts.get(4, 0) / total * 100,
                t("avg_pts",  lang): sum(
                    run["groups"][team_group]["standings"][i]["pts"]
                    for run in runs
                    for i, row in enumerate(run["groups"][team_group]["standings"])
                    if row["team"] == tm
                ) / n_runs,
            })

        pos_df = pd.DataFrame(pos_rows).sort_values(t("pos_1st", lang), ascending=False)

        team_display_name = f"{flag(team)} {team}"
        def highlight_team(row):
            return ["background-color: rgba(59,130,246,0.2)"] * len(row) \
                if row[t("col_team", lang)] == team_display_name else [""] * len(row)

        for col in [t("pos_1st", lang), t("pos_2nd", lang),
                    t("pos_3rd", lang), t("pos_4th", lang)]:
            pos_df[col] = pos_df[col].map("{:.1f}%".format)
        pos_df[t("avg_pts", lang)] = pos_df[t("avg_pts", lang)].map("{:.2f}".format)

        st.dataframe(
            pos_df.style.apply(highlight_team, axis=1),
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    # ── Link to individual runs ───────────────────────────────────────────────
    winning_ids = stats["winning_ids"]
    if winning_ids:
        st.subheader(t("winning_runs_title", lang))
        st.markdown(t("winning_runs_desc", lang,
                      team=team, n=len(winning_ids),
                      pct=len(winning_ids)/n_runs*100))
        if st.button(t("browse_runs_btn", lang, n=len(winning_ids))):
            st.session_state["drill_team"]    = team
            st.session_state["drill_run_ids"] = winning_ids
            st.session_state["view"]          = t("nav_runs", lang)
            st.rerun()
    else:
        st.info(t("no_wins", lang, team=team))

# ─────────────────────────────────────────────
# 5. INDIVIDUAL RUNS VIEW
# ─────────────────────────────────────────────
def show_individual_runs(runs, team_stats, lang):
    st.title(t("runs_title", lang))

    drill_team    = st.session_state.get("drill_team", None)
    drill_run_ids = st.session_state.get("drill_run_ids", None)

    all_teams_opt = [t("all_teams", lang)] + sorted(team_stats.keys())
    default_idx   = all_teams_opt.index(drill_team) if drill_team in all_teams_opt else 0

    selected_team = st.selectbox(
        t("filter_by_champion", lang), all_teams_opt, index=default_idx
    )

    if selected_team != drill_team:
        st.session_state.pop("drill_team", None)
        st.session_state.pop("drill_run_ids", None)
        drill_run_ids = None

    if selected_team == t("all_teams", lang):
        filtered_runs = runs
    elif drill_run_ids is not None:
        filtered_runs = [r for r in runs if r["run_id"] in set(drill_run_ids)]
    else:
        filtered_runs = [r for r in runs if r["champion"] == selected_team]

    st.markdown(t("showing_runs", lang, n=len(filtered_runs)))

    if not filtered_runs:
        st.warning(t("no_runs_match", lang))
        return

    st.divider()

    col_list, col_bracket = st.columns([1, 2])

    with col_list:
        st.subheader(t("runs_subheader", lang))
        run_options = {
            t("run_label", lang,
              run_id=r["run_id"],
              champion=f"{flag(r['champion'])} {r['champion']}"): r["run_id"]
            for r in filtered_runs[:200]
        }
        if len(filtered_runs) > 200:
            st.caption(t("showing_first_n", lang, n=200, total=len(filtered_runs)))

        selected_label  = st.radio(
            t("select_run", lang),
            list(run_options.keys()),
            label_visibility="collapsed"
        )
        selected_run_id = run_options[selected_label]

    selected_run = next(r for r in runs if r["run_id"] == selected_run_id)

    with col_bracket:
        st.subheader(t("run_header", lang,
                       run_id=selected_run_id,
                       flag=flag(selected_run["champion"]),
                       champion=selected_run["champion"]))
        show_run_stats(selected_run, lang)
        show_bracket(selected_run, lang)

# ─────────────────────────────────────────────
# 6. BRACKET + MATCH CARD
# ─────────────────────────────────────────────
def render_match_card(m, lang):
    team_a   = m["a"]
    team_b   = m["b"]
    winner   = m["w"]
    goals_a  = m["ga"]
    goals_b  = m["gb"]
    went_et  = m.get("et", False)
    went_pen = m.get("pen", False)

    def short(name, max_len=14):
        return name if len(name) <= max_len else name[:max_len - 1] + "…"

    if went_pen:
        badge = t("badge_pen", lang)
    elif went_et:
        badge = t("badge_aet", lang)
    else:
        badge = ""

    if went_et and m.get("goals_a_et") is not None:
        et_a = m.get("goals_a_et", 0)
        et_b = m.get("goals_b_et", 0)
        if et_a > 0 or et_b > 0:
            score_a = f"{goals_a}+{et_a}"
            score_b = f"{goals_b}+{et_b}"
        else:
            score_a = str(goals_a)
            score_b = str(goals_b)
    else:
        score_a = str(goals_a)
        score_b = str(goals_b)

    st.markdown(
        f"""<div style="border:1px solid #374151; border-radius:8px; padding:8px 10px;
                       height:85px; box-sizing:border-box; background:#1F2937;
                       display:flex; flex-direction:column; justify-content:space-between;
                       margin-bottom:8px; overflow:hidden;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:0.82em; color:{'#10B981' if winner==team_a else '#D1D5DB'};
                             font-weight:{'700' if winner==team_a else '400'};
                             white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
                             max-width:75%;">{flag(team_a)} {short(team_a)}</span>
                <span style="font-size:0.9em; font-weight:700;
                             color:{'#10B981' if winner==team_a else '#D1D5DB'};">{score_a}</span>
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:0.82em; color:{'#10B981' if winner==team_b else '#D1D5DB'};
                             font-weight:{'700' if winner==team_b else '400'};
                             white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
                             max-width:75%;">{flag(team_b)} {short(team_b)}</span>
                <span style="font-size:0.9em; font-weight:700;
                             color:{'#10B981' if winner==team_b else '#D1D5DB'};">{score_b}</span>
            </div>
            <div style="font-size:0.7em; color:#6B7280; height:14px;">{badge}</div>
        </div>""",
        unsafe_allow_html=True
    )


def show_bracket(run, lang):
    with st.expander(t("group_results_expander", lang), expanded=False):
        gcols = st.columns(3)
        for i, (g, gdata) in enumerate(run["groups"].items()):
            with gcols[i % 3]:
                st.markdown(f"**{t('group_label', lang, g=g)}**")
                rows = []
                for row in gdata["standings"]:
                    rows.append({
                        t("col_team", lang): f"{flag(row['team'])} {row['team']}",
                        "Pts": row["pts"],
                        "GD":  row["gd"],
                        "GF":  row["gf"],
                    })
                gdf = pd.DataFrame(rows)

                def highlight_qualified(row):
                    idx = gdf.index.get_loc(row.name)
                    return ["background-color: rgba(16,185,129,0.2)"] * len(row) \
                        if idx < 2 else [""] * len(row)

                st.dataframe(
                    gdf.style.apply(highlight_qualified, axis=1),
                    use_container_width=True,
                    hide_index=True,
                    height=175,
                )

    st.markdown(t("third_qualified", lang, teams=", ".join(
        f"{flag(tm)} {tm}" for tm in run["third_qualified"]
    )))
    st.divider()

    # ── Knockout rounds ───────────────────────────────────────────────────────
    knockout_stages = [
        (t("round_of_32",    lang), run["matches"]["R32"], 4),
        (t("round_of_16",    lang), run["matches"]["R16"], 4),
        (t("quarter_finals", lang), run["matches"]["QF"],  4),
        (t("semi_finals",    lang), run["matches"]["SF"],  2),
    ]

    for stage_label_str, matches, n_cols in knockout_stages:
        st.markdown(stage_label_str)
        cols = st.columns(n_cols)
        for i, m in enumerate(matches):
            with cols[i % n_cols]:
                render_match_card(m, lang)
        st.divider()

    # ── Third place + Final ───────────────────────────────────────────────────
    st.markdown(t("third_and_final", lang))
    col_tp, col_spacer, col_final = st.columns([2, 1, 2])

    with col_tp:
        st.markdown(t("third_place_match", lang))
        if run["matches"]["TP"]:
            render_match_card(run["matches"]["TP"][0], lang)

    with col_final:
        st.markdown(t("final_match", lang))
        if run["matches"]["Final"]:
            render_match_card(run["matches"]["Final"][0], lang)

    st.divider()
    st.markdown(t("champion_banner", lang,
                  flag=flag(run["champion"]),
                  team=run["champion"]))

# ─────────────────────────────────────────────
# 7. MAIN
# ─────────────────────────────────────────────
def main():
    st.set_page_config(
        page_title="WC 2026 Simulator",
        page_icon="⚽",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    args = parse_args()

    # ── Language selector (before any translated content) ─────────────────────
    lang = st.sidebar.selectbox(
        "🌐 Language",
        ["en", "es"],
        format_func=lambda x: {"en": "English", "es": "Español"}[x],
    )

    # ── Load data ─────────────────────────────────────────────────────────────
    with st.spinner(t("loading", lang)):
        runs, team_stats, group_stats, n_runs = load_data(args.file, args.repo, args.filename)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    st.sidebar.title(t("app_title", lang))
    st.sidebar.markdown(f"**{t('app_subtitle', lang, n=n_runs)}**")
    st.sidebar.divider()

    view_options = [
        t("nav_overview", lang),
        t("nav_team",     lang),
        t("nav_runs",     lang),
    ]

    if "view" not in st.session_state:
        st.session_state["view"] = view_options[0]

    # Re-map if language changed and stored view is in old language
    if st.session_state["view"] not in view_options:
        st.session_state["view"] = view_options[0]

    view = st.sidebar.radio(
        t("nav_label", lang),
        view_options,
        index=view_options.index(st.session_state["view"]),
    )
    st.session_state["view"] = view

    # ── Route ─────────────────────────────────────────────────────────────────
    if view == t("nav_overview", lang):
        show_overview(team_stats, group_stats, n_runs, runs, lang)
    elif view == t("nav_team", lang):
        show_team_deep_dive(runs, team_stats, n_runs, lang)
    elif view == t("nav_runs", lang):
        show_individual_runs(runs, team_stats, lang)


main()