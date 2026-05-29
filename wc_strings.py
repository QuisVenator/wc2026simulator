# strings.py
# All UI strings for the WC 2026 Simulator visualizer.
# Add new languages by adding a new key to STRINGS matching all keys in "en".

STRINGS = {
    "en": {
        # ── App / sidebar ──────────────────────────────────────────────────────
        "app_title":                "⚽ WC 2026 Simulator",
        "app_subtitle":             "{n:,} simulated runs",
        "file_label":               "File",
        "language_selector":        "🌐 Language",
        "nav_overview":             "🌍 Tournament Overview",
        "nav_team":                 "🔍 Team Deep Dive",
        "nav_runs":                 "🏆 Individual Runs",
        "nav_label":                "View",
        "loading":                  "Loading simulation data...",
        "file_not_found":           "File not found: {path}",

        # ── Stage labels ───────────────────────────────────────────────────────
        "stage_group":              "Group Stage",
        "stage_R32":                "Round of 32",
        "stage_R16":                "Round of 16",
        "stage_QF":                 "Quarter-Final",
        "stage_SF":                 "Semi-Final",
        "stage_final":              "Final",
        "stage_champion":           "Champion",

        # ── Overview page ──────────────────────────────────────────────────────
        "overview_title":           "🌍 Tournament Overview",
        "overview_subtitle":        "Aggregated results across **{n:,} simulated tournaments**",
        "champion_prob":            "Champion Probability",
        "champion_prob_axis":       "Champion probability (%)",
        "stage_reach":              "Stage Reach Probability",
        "group_summary":            "Group Stage — Most Likely Winners",
        "group_label":              "Group {g}",
        "pos_1st":                  "1st %",
        "pos_2nd":                  "2nd %",
        "pos_3rd":                  "3rd %",
        "pos_4th":                  "4th %",
        "col_team":                 "Team",
        "col_conf":                 "Conf",

        # ── Global stats ───────────────────────────────────────────────────────
        "global_stats_title":       "📊 Across All Runs",
        "stat_avg_goals":           "Avg goals/game",
        "stat_avg_draws":           "Avg draws/run",
        "stat_avg_aet":             "Avg AET/run",
        "stat_avg_pen":             "Avg PEN/run",
        "stat_highest_scoring":     "Highest scoring game ever",
        "stat_goals_suffix":        "{n} goals",

        # ── Run stats ──────────────────────────────────────────────────────────
        "run_stats_title":          "📊 Run Summary",
        "stat_total_matches":       "Total matches",
        "stat_group_draws":         "Group draws",
        "stat_went_aet":            "Went to AET",
        "stat_decided_pen":         "Decided by PEN",
        "stat_avg_goals_game":      "Avg goals/game",
        "stat_most_goals_game":     "Most goals in game",
        "stat_biggest_margin":      "Biggest margin",
        "stat_biggest_margin_val":  "{n}-goal win",
        "stat_most_goals_scored":   "Most goals scored",
        "stat_goals_all_matches":   "{n} goals across all matches",

        # ── Team deep dive ─────────────────────────────────────────────────────
        "team_title":               "🔍 Team Deep Dive",
        "select_team":              "Select a team",
        "metric_champion":          "Champion",
        "metric_reach_final":       "Reach Final",
        "metric_reach_sf":          "Reach SF",
        "metric_reach_qf":          "Reach QF",
        "metric_reach_r16":         "Reach R16",
        "progression_title":        "Tournament Progression",
        "eliminated_by_title":      "Most Often Eliminated By",
        "eliminated_pct_axis":      "% of all runs",
        "eliminated_hover":         "Eliminated {pct:.1f}% of runs",
        "no_elim_data":             "No elimination data — this team wins every run!",
        "exit_round_title":         "Exit Round Distribution",
        "runs_label":               "{n} runs",
        "group_finish_title":       "Group Stage Finish",
        "group_teams_label":        "Group **{g}**: {teams}",
        "avg_pts":                  "Avg pts",
        "winning_runs_title":       "🏆 Winning Runs",
        "winning_runs_desc":        "**{team}** won the tournament in **{n}** runs ({pct:.1f}%)",
        "browse_runs_btn":          "Browse {n} winning runs →",
        "no_wins":                  "{team} did not win any simulated tournaments.",

        # ── Individual runs page ───────────────────────────────────────────────
        "runs_title":               "🏆 Individual Runs",
        "filter_by_champion":       "Filter by champion",
        "all_teams":                "(All teams)",
        "showing_runs":             "Showing **{n}** runs",
        "no_runs_match":            "No runs match this filter.",
        "runs_subheader":           "Runs",
        "showing_first_n":          "Showing first {n} of {total} runs",
        "select_run":               "Select a run to view",
        "run_label":                "Run #{run_id}  —  {champion}",
        "run_header":               "Run #{run_id} — Champion: {flag} {champion}",

        # ── Bracket ────────────────────────────────────────────────────────────
        "group_results_expander":   "📋 Group Stage Results",
        "third_qualified":          "**Third place qualifiers:** {teams}",
        "third_place_match":        "**Third Place Match**",
        "final_match":              "**Final**",
        "third_and_final":          "### 🥉 Third Place & 🏆 Final",
        "champion_banner":          "### {flag} Champion: {team}",
        "round_of_32":              "### Round of 32",
        "round_of_16":              "### Round of 16",
        "quarter_finals":           "### Quarter-Finals",
        "semi_finals":              "### Semi-Finals",

        # ── Match card ────────────────────────────────────────────────────────
        "badge_pen":                "PEN",
        "badge_aet":                "AET",
    },

    "es": {
        # ── App / sidebar ──────────────────────────────────────────────────────
        "app_title":                "⚽ Simulador Mundial 2026",
        "app_subtitle":             "{n:,} simulaciones",
        "file_label":               "Archivo",
        "language_selector":        "🌐 Idioma",
        "nav_overview":             "🌍 Vista General",
        "nav_team":                 "🔍 Análisis por Equipo",
        "nav_runs":                 "🏆 Simulaciones",
        "nav_label":                "Vista",
        "loading":                  "Cargando datos...",
        "file_not_found":           "Archivo no encontrado: {path}",

        # ── Stage labels ───────────────────────────────────────────────────────
        "stage_group":              "Fase de Grupos",
        "stage_R32":                "Ronda de 32",
        "stage_R16":                "Octavos de Final",
        "stage_QF":                 "Cuartos de Final",
        "stage_SF":                 "Semifinal",
        "stage_final":              "Final",
        "stage_champion":           "Campeón",

        # ── Overview page ──────────────────────────────────────────────────────
        "overview_title":           "🌍 Vista General del Torneo",
        "overview_subtitle":        "Resultados agregados de **{n:,} torneos simulados**",
        "champion_prob":            "Probabilidad de Campeón",
        "champion_prob_axis":       "Probabilidad de campeonato (%)",
        "stage_reach":              "Probabilidad de Alcanzar Cada Fase",
        "group_summary":            "Fase de Grupos — Ganadores Más Probables",
        "group_label":              "Grupo {g}",
        "pos_1st":                  "1° %",
        "pos_2nd":                  "2° %",
        "pos_3rd":                  "3° %",
        "pos_4th":                  "4° %",
        "col_team":                 "Equipo",
        "col_conf":                 "Conf",

        # ── Global stats ───────────────────────────────────────────────────────
        "global_stats_title":       "📊 En Todas las Simulaciones",
        "stat_avg_goals":           "Goles promedio/partido",
        "stat_avg_draws":           "Empates promedio/simulación",
        "stat_avg_aet":             "Prórrogas promedio/simulación",
        "stat_avg_pen":             "Penales promedio/simulación",
        "stat_highest_scoring":     "Partido con más goles",
        "stat_goals_suffix":        "{n} goles",

        # ── Run stats ──────────────────────────────────────────────────────────
        "run_stats_title":          "📊 Resumen de la Simulación",
        "stat_total_matches":       "Total de partidos",
        "stat_group_draws":         "Empates en grupos",
        "stat_went_aet":            "Fueron a prórroga",
        "stat_decided_pen":         "Decididos por penales",
        "stat_avg_goals_game":      "Goles promedio/partido",
        "stat_most_goals_game":     "Más goles en un partido",
        "stat_biggest_margin":      "Mayor diferencia",
        "stat_biggest_margin_val":  "victoria por {n} goles",
        "stat_most_goals_scored":   "Más goles anotados",
        "stat_goals_all_matches":   "{n} goles en todos los partidos",

        # ── Team deep dive ─────────────────────────────────────────────────────
        "team_title":               "🔍 Análisis por Equipo",
        "select_team":              "Seleccionar equipo",
        "metric_champion":          "Campeón",
        "metric_reach_final":       "Llegar a la Final",
        "metric_reach_sf":          "Llegar a Semis",
        "metric_reach_qf":          "Llegar a Cuartos",
        "metric_reach_r16":         "Llegar a Octavos",
        "progression_title":        "Progresión en el Torneo",
        "eliminated_by_title":      "Eliminado Más Frecuentemente Por",
        "eliminated_pct_axis":      "% de todas las simulaciones",
        "eliminated_hover":         "Eliminó en {pct:.1f}% de simulaciones",
        "no_elim_data":             "Sin datos de eliminación — ¡este equipo gana siempre!",
        "exit_round_title":         "Distribución por Ronda de Eliminación",
        "runs_label":               "{n} simulaciones",
        "group_finish_title":       "Posición en la Fase de Grupos",
        "group_teams_label":        "Grupo **{g}**: {teams}",
        "avg_pts":                  "Pts prom.",
        "winning_runs_title":       "🏆 Simulaciones Ganadoras",
        "winning_runs_desc":        "**{team}** ganó el torneo en **{n}** simulaciones ({pct:.1f}%)",
        "browse_runs_btn":          "Ver {n} simulaciones ganadoras →",
        "no_wins":                  "{team} no ganó ningún torneo simulado.",

        # ── Individual runs page ───────────────────────────────────────────────
        "runs_title":               "🏆 Simulaciones Individuales",
        "filter_by_champion":       "Filtrar por campeón",
        "all_teams":                "(Todos los equipos)",
        "showing_runs":             "Mostrando **{n}** simulaciones",
        "no_runs_match":            "Ninguna simulación coincide con el filtro.",
        "runs_subheader":           "Simulaciones",
        "showing_first_n":          "Mostrando las primeras {n} de {total} simulaciones",
        "select_run":               "Seleccionar simulación",
        "run_label":                "Sim. #{run_id}  —  {champion}",
        "run_header":               "Sim. #{run_id} — Campeón: {flag} {champion}",

        # ── Bracket ────────────────────────────────────────────────────────────
        "group_results_expander":   "📋 Resultados de la Fase de Grupos",
        "third_qualified":          "**Clasificados en tercer lugar:** {teams}",
        "third_place_match":        "**Partido por el Tercer Puesto**",
        "final_match":              "**Final**",
        "third_and_final":          "### 🥉 Tercer Puesto & 🏆 Final",
        "champion_banner":          "### {flag} Campeón: {team}",
        "round_of_32":              "### Ronda de 32",
        "round_of_16":              "### Octavos de Final",
        "quarter_finals":           "### Cuartos de Final",
        "semi_finals":              "### Semifinales",

        # ── Match card ────────────────────────────────────────────────────────
        "badge_pen":                "PEN",
        "badge_aet":                "PROR",
    },
}

# Convenience: map stage key → string key
STAGE_STRING_KEYS = {
    "group":    "stage_group",
    "R32":      "stage_R32",
    "R16":      "stage_R16",
    "QF":       "stage_QF",
    "SF":       "stage_SF",
    "final":    "stage_final",
    "champion": "stage_champion",
}

def t(key: str, lang: str = "en", **kwargs) -> str:
    """
    Get a translated string by key.
    Falls back to English if the key is missing in the requested language.
    Supports format arguments: t("overview_subtitle", lang, n=1000)
    """
    lang_strings = STRINGS.get(lang, STRINGS["en"])
    s = lang_strings.get(key) or STRINGS["en"].get(key) or f"[{key}]"
    return s.format(**kwargs) if kwargs else s

def stage_label(stage_key: str, lang: str = "en") -> str:
    """Get the translated label for a stage key like 'R32', 'QF', etc."""
    return t(STAGE_STRING_KEYS.get(stage_key, "stage_group"), lang)