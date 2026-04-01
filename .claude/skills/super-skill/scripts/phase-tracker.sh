#!/bin/bash
# Phase Tracker Script for Super-Skill
# Ensures strict execution of all 14 phases

PHASE_FILE="$HOME/.claude/logs/super-skill-phase-tracking.jsonl"
PHASES=("Phase 0: Vision" "Phase 1: Feasibility" "Phase 2: GitHub Discovery" "Phase 2b: Skills Discovery" "Phase 3: Knowledge Base" "Phase 4: Requirements" "Phase 5: Architecture" "Phase 5b: Design" "Phase 6: WBS" "Phase 7: Init" "Phase 8: Development" "Phase 9: QA" "Phase 10: Ralph Loop" "Phase 11: Deployment" "Phase 12: Evolution")

mkdir -p "$(dirname "$PHASE_FILE")"

start_phase() {
    local phase_num=$1
    local timestamp=$(date -Iseconds)
    echo "{\"action\":\"start\",\"phase\":$phase_num,\"name\":\"${PHASES[$phase_num]}\",\"timestamp\":\"$timestamp\"}" >> "$PHASE_FILE"
    echo "▶ Started ${PHASES[$phase_num]} at $timestamp"
}

complete_phase() {
    local phase_num=$1
    local timestamp=$(date -Iseconds)
    echo "{\"action\":\"complete\",\"phase\":$phase_num,\"name\":\"${PHASES[$phase_num]}\",\"timestamp\":\"$timestamp\"}" >> "$PHASE_FILE"
    echo "✓ Completed ${PHASES[$phase_num]} at $timestamp"
}

check_phase_status() {
    local phase_num=$1
    if [ -f "$PHASE_FILE" ]; then
        local last_action=$(grep "\"phase\":$phase_num" "$PHASE_FILE" | tail -1)
        if echo "$last_action" | grep -q '"action":"complete"'; then
            echo "completed"
        elif echo "$last_action" | grep -q '"action":"start"'; then
            echo "in_progress"
        else
            echo "not_started"
        fi
    else
        echo "not_started"
    fi
}

get_current_phase() {
    for i in "${!PHASES[@]}"; do
        if [ "$(check_phase_status $i)" = "not_started" ] || [ "$(check_phase_status $i)" = "in_progress" ]; then
            echo "$i"
            return
        fi
    done
    echo "-1"
}

reset_tracking() {
    rm -f "$PHASE_FILE"
    echo "Phase tracking reset"
}

case "$1" in
    start) start_phase "$2" ;;
    complete) complete_phase "$2" ;;
    status) check_phase_status "$2" ;;
    current) get_current_phase ;;
    reset) reset_tracking ;;
    list)
        for i in "${!PHASES[@]}"; do
            status=$(check_phase_status $i)
            case $status in
                completed) icon="✓" ;;
                in_progress) icon="▶" ;;
                *) icon="○" ;;
            esac
            echo "$icon Phase $i: ${PHASES[$i]}"
        done
        ;;
    *)
        echo "Usage: $0 {start|complete|status|current|reset|list} [phase_number]"
        ;;
esac
