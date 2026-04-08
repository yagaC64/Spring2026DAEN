#!/usr/bin/env bash
#
# Local DuckDB + Streamlit workbench runner for Spring2026DAEN.
# This is an additive, local-first helper. It does not replace the
# notebook-first workflow or the existing GitHub Pages dashboard.
#
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${ROOT_DIR}/run_local_proto.log"
PID_FILE="${ROOT_DIR}/.streamlit_local.pid"
DEFAULT_VENV="${ROOT_DIR}/.venv"
DB_PATH="${ROOT_DIR}/data/local/duckdb/spring2026daen_baseline.duckdb"
BUILD_SUMMARY_PATH="${ROOT_DIR}/data/local/duckdb/duckdb_baseline_build_summary.json"
PYTEST_TARGET="${ROOT_DIR}/tests"
STREAMLIT_PORT="${STREAMLIT_PORT:-8501}"
STREAMLIT_URL="http://127.0.0.1:${STREAMLIT_PORT}"
MAX_LOG_BYTES=1048576

C_RESET=$'\033[0m'
C_GREEN=$'\033[0;32m'
C_RED=$'\033[0;31m'
C_YELLOW=$'\033[0;33m'
C_BLUE=$'\033[0;34m'
C_CYAN=$'\033[0;36m'
C_BOLD=$'\033[1m'

log() {
  printf "\n${C_BOLD}[%s] %s${C_RESET}\n" "$(date +'%H:%M:%S')" "$*"
}

warn() {
  printf "${C_YELLOW}%s${C_RESET}\n" "$*"
}

die() {
  printf "${C_RED}%s${C_RESET}\n" "$*" >&2
  exit 1
}

on_error() {
  local exit_code=$?
  local line_no="${1:-unknown}"
  printf "\n${C_RED}${C_BOLD}[%s] ERROR: Script stopped at line %s (exit code %s).${C_RESET}\n" \
    "$(date +'%H:%M:%S')" "${line_no}" "${exit_code}" >&2
  printf "${C_RED}Check %s for background-service output.${C_RESET}\n" "${LOG_FILE}" >&2
}

trap 'on_error "$LINENO"' ERR

port_pid() {
  local port="$1"
  lsof -ti tcp:"${port}" 2>/dev/null || true
}

pid_command() {
  local pid="$1"
  ps -p "${pid}" -o command= 2>/dev/null || true
}

managed_streamlit_pid() {
  local pid="$1"
  local cmd
  cmd="$(pid_command "${pid}")"
  [[ -n "${cmd}" && "${cmd}" == *"streamlit"* && "${cmd}" == *"app/streamlit_app.py"* ]]
}

port_ready() {
  [[ -z "$(port_pid "$1")" ]]
}

wait_for_port_release() {
  local port="$1"
  local attempts="${2:-10}"
  for _ in $(seq 1 "${attempts}"); do
    if port_ready "${port}"; then
      return 0
    fi
    sleep 0.5
  done
  return 1
}

streamlit_running() {
  curl -fsS "${STREAMLIT_URL}" >/dev/null 2>&1
}

open_in_default_browser() {
  local url="$1"
  if command -v open >/dev/null 2>&1; then
    open "${url}" >/dev/null 2>&1 &
  elif command -v xdg-open >/dev/null 2>&1; then
    xdg-open "${url}" >/dev/null 2>&1 &
  else
    return 1
  fi
}

offer_open_browser() {
  [[ -t 0 && -t 1 ]] || return 0

  local answer
  read -r -p "Open it in the default browser now? [Y/n/q]: " answer
  case "${answer:-Y}" in
    [Yy]|Y)
      if open_in_default_browser "${STREAMLIT_URL}"; then
        log "Opened ${STREAMLIT_URL} in the default browser"
      else
        warn "Could not find a supported browser opener. Open ${STREAMLIT_URL} manually."
      fi
      ;;
    [Qq])
      log "Leaving the local app running without opening a browser"
      ;;
    *)
      log "Skipping automatic browser launch"
      ;;
  esac
}

mask_bool() {
  if [[ "$1" == "1" ]]; then
    printf "${C_GREEN}yes${C_RESET}"
  else
    printf "${C_RED}no${C_RESET}"
  fi
}

ensure_python() {
  command -v python3 >/dev/null 2>&1 || die "python3 is required but was not found."
}

python_bin() {
  if [[ -f "${DEFAULT_VENV}/bin/python" ]]; then
    printf "%s" "${DEFAULT_VENV}/bin/python"
  else
    command -v python3
  fi
}

ensure_venv() {
  ensure_python
  if [[ -n "${VIRTUAL_ENV-}" && "${VIRTUAL_ENV}" == "${DEFAULT_VENV}" ]]; then
    return
  fi
  if [[ ! -f "${DEFAULT_VENV}/bin/activate" ]]; then
    log "Creating local Python environment at ${DEFAULT_VENV}"
    python3 -m venv "${DEFAULT_VENV}"
  fi
  # shellcheck disable=SC1090
  source "${DEFAULT_VENV}/bin/activate"
}

python_import_status() {
  "$(python_bin)" - <<'PY'
import importlib.util
mods = ["duckdb", "pandas", "pyarrow", "streamlit", "pytest", "yaml"]
for mod in mods:
    print(f"{mod}:{1 if importlib.util.find_spec(mod) else 0}")
PY
}

requirements_ready() {
  ensure_venv
  python - <<'PY'
import importlib.util
import sys

mods = ["duckdb", "pandas", "pyarrow", "streamlit", "pytest", "yaml"]
missing = [mod for mod in mods if importlib.util.find_spec(mod) is None]
if missing:
    print(",".join(missing))
    sys.exit(1)
sys.exit(0)
PY
}

format_bytes() {
  python3 - "$1" <<'PY'
import sys
value = int(sys.argv[1])
units = ["B", "KB", "MB", "GB", "TB"]
size = float(value)
for unit in units:
    if size < 1024 or unit == units[-1]:
        print(f"{size:.1f} {unit}")
        break
    size /= 1024
PY
}

print_status_row() {
  printf "%-28s | %-18s | %s\n" "$1" "$2" "$3"
}

show_status() {
  log "Gathering local workbench status"

  local expected_outputs=(
    "${ROOT_DIR}/JupyterNotebooks/outputs/index_pipeline/30_scoring/municipio_indices_scored.csv"
    "${ROOT_DIR}/JupyterNotebooks/outputs/index_pipeline/50_products/priority_actions.csv"
    "${ROOT_DIR}/JupyterNotebooks/outputs/index_pipeline/01_ingest/flood_station_latest_features.csv"
    "${ROOT_DIR}/JupyterNotebooks/outputs/index_pipeline/01_ingest/nws_alerts_enriched.csv"
    "${ROOT_DIR}/outputs/index_pipeline/15_terrain/municipio_terrain_features.csv"
    "${ROOT_DIR}/outputs/noaa_pr/noaa_pr_station_summary.csv"
  )

  printf "\n${C_BOLD}%-28s | %-18s | %s${C_RESET}\n" "Check" "Status" "Details"
  printf '%*s\n' "${COLUMNS:-100}" '' | tr ' ' -

  local venv_status details
  if [[ -n "${VIRTUAL_ENV-}" && "${VIRTUAL_ENV}" == "${DEFAULT_VENV}" ]]; then
    venv_status="${C_GREEN}ACTIVE${C_RESET}"
    details="${DEFAULT_VENV}"
  elif [[ -n "${VIRTUAL_ENV-}" ]]; then
    venv_status="${C_YELLOW}OTHER${C_RESET}"
    details="${VIRTUAL_ENV} (recommended: ${DEFAULT_VENV})"
  else
    venv_status="${C_RED}INACTIVE${C_RESET}"
    details="Select 1) or 3), or run './run.sh up' or './run.sh install' to create/use ${DEFAULT_VENV}"
  fi
  print_status_row "Python venv" "${venv_status}" "${details}"

  local py_version
  py_version="$(python3 --version 2>/dev/null || echo "Not found")"
  print_status_row "Python" "$( [[ "${py_version}" == "Not found" ]] && printf "${C_RED}missing${C_RESET}" || printf "${C_GREEN}found${C_RESET}" )" "${py_version}"

  local dep_lines dep_missing=0
  dep_lines="$(python_import_status)"
  while IFS=: read -r name ok; do
    if [[ "${ok}" == "1" ]]; then
      print_status_row "Dependency: ${name}" "${C_GREEN}ready${C_RESET}" "-"
    else
      dep_missing=1
      print_status_row "Dependency: ${name}" "${C_RED}missing${C_RESET}" "Select 1) or 3), or run './run.sh up' or './run.sh install'"
    fi
  done <<< "${dep_lines}"

  local available=0
  for path in "${expected_outputs[@]}"; do
    if [[ -f "${path}" ]]; then
      available=$((available + 1))
    fi
  done
  print_status_row "Curated baseline inputs" "${C_GREEN}${available}/6${C_RESET}" "Current stable local inputs discovered"

  if [[ -f "${DB_PATH}" ]]; then
    local db_size
    db_size="$(stat -f%z "${DB_PATH}")"
    print_status_row "DuckDB baseline file" "${C_GREEN}present${C_RESET}" "${DB_PATH#${ROOT_DIR}/} ($(format_bytes "${db_size}"))"
  else
    print_status_row "DuckDB baseline file" "${C_YELLOW}not built${C_RESET}" "Select 1) or 5), or run './run.sh up' or './run.sh build'"
  fi

  if [[ -f "${BUILD_SUMMARY_PATH}" ]]; then
    local summary_line
    summary_line="$(python3 - "${BUILD_SUMMARY_PATH}" <<'PY'
import json, sys
path = sys.argv[1]
data = json.load(open(path))
print(f"loaded={len(data.get('loaded_sources', []))}, missing={len(data.get('missing_sources', []))}, inventory_only={len(data.get('inventory_only_sources', []))}")
PY
)"
    print_status_row "DuckDB build summary" "${C_GREEN}present${C_RESET}" "${summary_line}"
  else
    print_status_row "DuckDB build summary" "${C_YELLOW}not built${C_RESET}" "-"
  fi

  if streamlit_running; then
    print_status_row "Streamlit app" "${C_GREEN}running${C_RESET}" "${STREAMLIT_URL} | Select 9) or run './run.sh stop' to stop it cleanly"
  else
    print_status_row "Streamlit app" "${C_RED}stopped${C_RESET}" "Select 1) or 8), or run './run.sh up' or './run.sh start'"
  fi

  if port_ready "${STREAMLIT_PORT}"; then
    print_status_row "Streamlit port ${STREAMLIT_PORT}" "${C_GREEN}ready${C_RESET}" "Port is free for this app or other local tools"
  else
    local port_detail
    if managed_streamlit_pid "$(port_pid "${STREAMLIT_PORT}" | head -n 1)"; then
      port_detail="Select 9) or run './run.sh stop' to gracefully stop the app and free the port"
    else
      port_detail="Another local process is holding the port. Stop that app or set STREAMLIT_PORT to another value"
    fi
    print_status_row "Streamlit port ${STREAMLIT_PORT}" "${C_YELLOW}busy${C_RESET}" "${port_detail}"
  fi

  print_status_row "Public GitHub Pages" "${C_BLUE}unchanged${C_RESET}" "This script does not touch the public dashboard flow"
  printf "\n"
}

install_dependencies() {
  log "Installing local baseline dependencies"
  ensure_venv
  python -m pip install --upgrade pip
  python -m pip install -r "${ROOT_DIR}/requirements.txt"
  python -m pip check
  log "Dependency installation complete"
}

ensure_requirements_ready() {
  ensure_venv
  local missing
  if missing="$(requirements_ready 2>/dev/null)"; then
    log "Local baseline requirements already look ready in ${DEFAULT_VENV}"
  else
    warn "Missing local baseline requirements detected: ${missing:-unknown}"
    install_dependencies
  fi
}

build_duckdb_baseline() {
  log "Building or refreshing the local DuckDB baseline"
  ensure_venv
  mkdir -p "$(dirname "${DB_PATH}")"
  python "${ROOT_DIR}/scripts/build_duckdb_baseline.py" | tee -a "${LOG_FILE}"
  log "DuckDB baseline build finished"
}

optimize_duckdb() {
  log "Optimizing the local DuckDB baseline"
  ensure_venv
  [[ -f "${DB_PATH}" ]] || die "DuckDB baseline not found at ${DB_PATH}. Build it first."
  if python - "${DB_PATH}" <<'PY'
import os
import sys
import duckdb

db_path = sys.argv[1]
before = os.path.getsize(db_path)
try:
    con = duckdb.connect(db_path)
    con.execute("CHECKPOINT")
    con.execute("VACUUM")
    con.execute("ANALYZE")
    size_info = con.execute("PRAGMA database_size").fetchdf()
    con.close()
except Exception as exc:
    print(f"optimize_error={exc}")
    raise SystemExit(2)
after = os.path.getsize(db_path)
print(f"before_bytes={before}")
print(f"after_bytes={after}")
if not size_info.empty:
    print(size_info.to_string(index=False))
PY
  then
    log "DuckDB optimization finished"
  else
    warn "DuckDB optimize could not get a write lock. Stop other DB users and retry."
    return 1
  fi
}

run_sample_queries() {
  log "Running a few starter DuckDB queries"
  ensure_venv
  [[ -f "${DB_PATH}" ]] || die "DuckDB baseline not found at ${DB_PATH}. Build it first."
  python - "${DB_PATH}" <<'PY'
import sys
import duckdb

db_path = sys.argv[1]
con = duckdb.connect(db_path, read_only=True)
queries = {
    "source_status": "SELECT name, status, row_count FROM vw_baseline_source_status ORDER BY name",
    "top_municipios": "SELECT municipio, priority_index_conf_adj, priority_band FROM vw_municipio_risk_summary ORDER BY priority_index_conf_adj DESC NULLS LAST LIMIT 10",
    "station_snapshot": "SELECT station_id, station_name, flood_hazard_final FROM vw_station_water_summary ORDER BY flood_hazard_final DESC NULLS LAST, station_name LIMIT 10",
}
for name, query in queries.items():
    print(f"\n=== {name} ===")
    print(con.execute(query).df().to_string(index=False))
con.close()
PY
}

run_smoke_tests() {
  log "Running local DuckDB + Streamlit smoke tests"
  ensure_requirements_ready
  [[ -e "${PYTEST_TARGET}" ]] || die "Pytest target not found at ${PYTEST_TARGET}"
  python -m pytest -q "${PYTEST_TARGET}"
  log "Smoke tests passed"
}

bring_stack_up() {
  local total_steps=4
  log "Starting local workbench stack-up workflow"
  log "Step 1/${total_steps}: checking or installing requirements"
  ensure_requirements_ready
  log "Step 2/${total_steps}: running pytest smoke tests"
  run_smoke_tests
  log "Step 3/${total_steps}: building or refreshing the local DuckDB baseline"
  build_duckdb_baseline
  log "Step 4/${total_steps}: starting the local Streamlit prototype"
  start_streamlit
}

start_streamlit() {
  log "Starting the local Streamlit prototype"
  ensure_venv
  [[ -f "${DB_PATH}" ]] || warn "DuckDB baseline not found yet. The app will prompt for a build if needed."

  if streamlit_running; then
    warn "Streamlit is already running at ${STREAMLIT_URL}"
    return 0
  fi

  local port_holders
  port_holders="$(port_pid "${STREAMLIT_PORT}")"
  if [[ -n "${port_holders}" ]]; then
    local holder_pid
    holder_pid="$(printf "%s\n" "${port_holders}" | head -n 1)"
    if managed_streamlit_pid "${holder_pid}"; then
      warn "A prior local Streamlit process appears to still own port ${STREAMLIT_PORT}. Cleaning it up first."
      stop_streamlit
    else
      die "Port ${STREAMLIT_PORT} is already in use by another process (${holder_pid}). Stop that app first or set STREAMLIT_PORT to a different value."
    fi
  fi

  if [[ -f "${PID_FILE}" ]]; then
    local existing_pid
    existing_pid="$(cat "${PID_FILE}" || true)"
    if [[ -n "${existing_pid}" ]] && ps -p "${existing_pid}" >/dev/null 2>&1; then
      warn "PID file exists and process ${existing_pid} is still alive. Cleaning up before restart."
      kill "${existing_pid}" || true
    fi
    rm -f "${PID_FILE}"
  fi

  cd "${ROOT_DIR}" || exit 1
  nohup streamlit run app/streamlit_app.py --server.headless true --server.port "${STREAMLIT_PORT}" >> "${LOG_FILE}" 2>&1 &
  local pid
  pid="$!"
  disown "${pid}" 2>/dev/null || true
  echo "${pid}" > "${PID_FILE}"

  for _ in $(seq 1 20); do
    if streamlit_running; then
      log "Streamlit is running at ${STREAMLIT_URL}"
      offer_open_browser
      return 0
    fi
    if ! ps -p "${pid}" >/dev/null 2>&1; then
      break
    fi
    sleep 0.5
  done

  warn "Streamlit did not become reachable. Recent log output:"
  tail -n 30 "${LOG_FILE}" || true
  return 1
}

stop_streamlit() {
  log "Stopping the local Streamlit prototype"
  local candidate_pids external_pids stopped=0
  candidate_pids="$(
    {
      if [[ -f "${PID_FILE}" ]]; then
        cat "${PID_FILE}" || true
      fi
      port_pid "${STREAMLIT_PORT}"
    } | awk 'NF' | sort -u
  )"

  while read -r pid; do
    [[ -n "${pid}" ]] || continue
    if [[ -f "${PID_FILE}" ]] && [[ "${pid}" == "$(cat "${PID_FILE}" 2>/dev/null || true)" ]]; then
      kill -TERM "${pid}" 2>/dev/null || true
      stopped=1
    elif managed_streamlit_pid "${pid}"; then
      kill -TERM "${pid}" 2>/dev/null || true
      stopped=1
    else
      external_pids="${external_pids} ${pid}"
    fi
  done <<< "${candidate_pids}"

  rm -f "${PID_FILE}"

  if [[ "${stopped}" == "1" ]] && wait_for_port_release "${STREAMLIT_PORT}" 10; then
    log "Streamlit stopped cleanly and port ${STREAMLIT_PORT} is now free for other apps"
    return 0
  fi

  if [[ "${stopped}" == "1" ]]; then
    warn "Graceful stop did not release port ${STREAMLIT_PORT} in time. Escalating to SIGKILL for managed processes."
    while read -r pid; do
      [[ -n "${pid}" ]] || continue
      if managed_streamlit_pid "${pid}"; then
        kill -KILL "${pid}" 2>/dev/null || true
      fi
    done <<< "${candidate_pids}"
    if wait_for_port_release "${STREAMLIT_PORT}" 10; then
      log "Managed Streamlit process was force-stopped and port ${STREAMLIT_PORT} is now free"
      return 0
    fi
  fi

  if [[ -n "${external_pids// }" ]]; then
    warn "Port ${STREAMLIT_PORT} is still occupied by another local process:${external_pids}. It was not stopped automatically."
    return 1
  fi

  warn "No managed Streamlit process was found on port ${STREAMLIT_PORT}"
}

tail_logs() {
  log "Recent run log output"
  if [[ -f "${LOG_FILE}" ]]; then
    tail -n 40 "${LOG_FILE}"
  else
    warn "No log file found yet at ${LOG_FILE}"
  fi
}

show_help() {
  cat <<EOF
Usage: ./run.sh [command]

Commands:
  menu       Interactive menu (default)
  up         Check/install requirements, run pytest, build DuckDB baseline, and start Streamlit
  status     Show local baseline status
  install    Create/use .venv and install requirements.txt
  test       Run local pytest smoke tests for the baseline
  build      Build or refresh the local DuckDB baseline
  optimize   Run CHECKPOINT/VACUUM/ANALYZE on the local DuckDB baseline
  query      Run a few starter DuckDB queries
  start      Start the local Streamlit prototype in the background
  stop       Gracefully stop the local Streamlit prototype and free the port
  logs       Show recent run log output
  help       Show this help
EOF
}

rotate_log_if_needed() {
  if [[ -f "${LOG_FILE}" ]]; then
    local size
    size="$(stat -f%z "${LOG_FILE}" 2>/dev/null || echo 0)"
    if [[ "${size}" -ge "${MAX_LOG_BYTES}" ]]; then
      mv "${LOG_FILE}" "${LOG_FILE}.1"
    fi
  fi
  touch "${LOG_FILE}"
}

main_menu() {
  while true; do
    printf "\n${C_BOLD}PR Hazard and Readiness Analysis Workbench Menu${C_RESET}\n"
    echo "  1. Bring local stack up (recommended)"
    echo "  2. Status check"
    echo "  3. Install/update local baseline dependencies"
    echo "  4. Run local pytest smoke tests"
    echo "  5. Build/refresh local DuckDB baseline"
    echo "  6. Optimize/VACUUM DuckDB baseline"
    echo "  7. Run starter DuckDB queries"
    echo "  8. Start local Streamlit prototype only"
    echo "  9. Stop local Streamlit prototype and free the port"
    echo "  10. Show recent log output"
    echo "  q. Quit"

    read -r -p "Select an option [1/2/3/4/5/6/7/8/9/10/q]: " choice
    case "${choice}" in
      1) bring_stack_up ;;
      2) show_status ;;
      3) install_dependencies ;;
      4) run_smoke_tests ;;
      5) build_duckdb_baseline ;;
      6) optimize_duckdb ;;
      7) run_sample_queries ;;
      8) start_streamlit ;;
      9) stop_streamlit ;;
      10) tail_logs ;;
      [Qq]) break ;;
      *) warn "Invalid option. Please try again." ;;
    esac
  done
}

rotate_log_if_needed

case "${1:-menu}" in
  menu) show_status; main_menu ;;
  up) bring_stack_up ;;
  status) show_status ;;
  install) install_dependencies ;;
  test) run_smoke_tests ;;
  build) build_duckdb_baseline ;;
  optimize) optimize_duckdb ;;
  query) run_sample_queries ;;
  start) start_streamlit ;;
  stop) stop_streamlit ;;
  logs) tail_logs ;;
  help|-h|--help) show_help ;;
  *) die "Unknown command: ${1}. Use './run.sh help' for options." ;;
esac
