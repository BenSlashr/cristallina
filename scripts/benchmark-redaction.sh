#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# benchmark-redaction.sh
# Benchmark de rédaction d'articles Cristallina via API Anthropic et OpenAI
#
# Usage:
#   ./scripts/benchmark-redaction.sh --model sonnet --articles articles.csv
#   ./scripts/benchmark-redaction.sh --model nano --articles articles.csv --parallel 5
#   ./scripts/benchmark-redaction.sh --model haiku --articles articles.csv --skip-preprocess
#
# Modèles supportés :
#   Anthropic : opus, sonnet, haiku
#   OpenAI    : nano, mini  (gpt-5-nano, gpt-5-mini via Responses API)
#
# CSV format (avec header) :
#   slug,keyword,branch,parent,order
#   mon-article,mon mot-cle SEO,ma-branche,mon-hub,1
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SITE_DIR="$PROJECT_DIR/site"
SYSTEM_PROMPT_FILE="$SCRIPT_DIR/redaction-system-prompt.md"

# --- Defaults ---
MODEL_SHORT="sonnet"
ARTICLES_CSV=""
PARALLEL=3
SKIP_PREPROCESS=false
NO_DEPLOY=false
MAX_TOKENS=8192
COOLDOWN=-1  # -1 = auto (30s pour Anthropic, 0 pour OpenAI)

# ============================================================
# Provider / Model resolution
# ============================================================

# Retourne le provider : "anthropic" ou "openai"
get_provider() {
    case "$1" in
        opus|sonnet|haiku|claude-*) echo "anthropic" ;;
        nano|mini|gpt-*)            echo "openai" ;;
        *) echo "unknown" ;;
    esac
}

# Retourne le model ID complet
resolve_model() {
    case "$1" in
        opus)       echo "claude-opus-4-6" ;;
        sonnet)     echo "claude-sonnet-4-5-20250929" ;;
        haiku)      echo "claude-haiku-4-5-20251001" ;;
        nano)       echo "gpt-5-nano" ;;
        mini)       echo "gpt-5-mini" ;;
        claude-*)   echo "$1" ;;
        gpt-*)      echo "$1" ;;
        *) echo "Modèle inconnu: $1" >&2; exit 1 ;;
    esac
}

# Prix par million de tokens (input output)
model_prices() {
    case "$1" in
        opus|claude-opus-4-6)                   echo "15 75" ;;
        sonnet|claude-sonnet-4-5-20250929)      echo "3 15" ;;
        haiku|claude-haiku-4-5-20251001)        echo "0.80 4" ;;
        nano|gpt-5-nano)                        echo "0.05 0.40" ;;
        mini|gpt-5-mini)                        echo "0.25 2.00" ;;
        *) echo "0 0" ;;
    esac
}

# ============================================================
# Parse args
# ============================================================
while [[ $# -gt 0 ]]; do
    case "$1" in
        --model)    MODEL_SHORT="$2"; shift 2 ;;
        --articles) ARTICLES_CSV="$2"; shift 2 ;;
        --parallel) PARALLEL="$2"; shift 2 ;;
        --skip-preprocess) SKIP_PREPROCESS=true; shift ;;
        --no-deploy) NO_DEPLOY=true; shift ;;
        --max-tokens) MAX_TOKENS="$2"; shift 2 ;;
        --cooldown) COOLDOWN="$2"; shift 2 ;;
        -h|--help)
            echo "Usage: $0 --model <opus|sonnet|haiku|nano|mini> --articles <csv> [--parallel N] [--cooldown N] [--skip-preprocess] [--no-deploy]"
            echo ""
            echo "Modèles :"
            echo "  Anthropic : opus, sonnet, haiku"
            echo "  OpenAI    : nano (gpt-5-nano), mini (gpt-5-mini)"
            exit 0 ;;
        *) echo "Option inconnue: $1" >&2; exit 1 ;;
    esac
done

if [ -z "$ARTICLES_CSV" ]; then
    echo "Erreur: --articles requis" >&2
    echo "Usage: $0 --model <opus|sonnet|haiku|nano|mini> --articles <csv>" >&2
    exit 1
fi

if [ ! -f "$ARTICLES_CSV" ]; then
    echo "Erreur: fichier $ARTICLES_CSV introuvable" >&2
    exit 1
fi

# --- Resolve model ---
MODEL_ID=$(resolve_model "$MODEL_SHORT")
PROVIDER=$(get_provider "$MODEL_SHORT")

if [ "$PROVIDER" = "unknown" ]; then
    echo "Erreur: provider inconnu pour le modèle '$MODEL_SHORT'" >&2
    exit 1
fi

# --- Environment ---
if [ -f "$SITE_DIR/.env" ]; then
    set -a
    source "$SITE_DIR/.env"
    set +a
fi

if [ "$PROVIDER" = "anthropic" ] && [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    echo "Erreur: ANTHROPIC_API_KEY non définie (dans .env ou env)" >&2
    exit 1
fi

if [ "$PROVIDER" = "openai" ] && [ -z "${OPENAI_API_KEY:-}" ]; then
    echo "Erreur: OPENAI_API_KEY non définie (dans .env ou env)" >&2
    exit 1
fi

# --- Dependencies ---
for cmd in curl jq; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "Erreur: '$cmd' requis" >&2
        exit 1
    fi
done

# --- Setup ---
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BENCH_DIR="/tmp/benchmark-${MODEL_SHORT}-${TIMESTAMP}"
mkdir -p "$BENCH_DIR"

SYSTEM_PROMPT=$(cat "$SYSTEM_PROMPT_FILE")

QUIZ_PROMPT_FILE="$SCRIPT_DIR/quiz-system-prompt.md"
QUIZ_PROMPT=""
if [ -f "$QUIZ_PROMPT_FILE" ]; then
    QUIZ_PROMPT=$(cat "$QUIZ_PROMPT_FILE")
fi
QUIZ_JSON="$SITE_DIR/src/data/quizzes.json"

echo "============================================"
echo "  Benchmark rédaction [PROJECT_NAME]"
echo "============================================"
echo "  Modèle     : $MODEL_SHORT ($MODEL_ID)"
echo "  Provider   : $PROVIDER"
echo "  Articles   : $ARTICLES_CSV"
echo "  Parallèle  : $PARALLEL"
echo "  Sortie     : $BENCH_DIR"
echo "  Max tokens : $MAX_TOKENS"
echo "  Cooldown   : ${COOLDOWN}s (auto si -1)"
echo "============================================"
echo ""

# --- Mots interdits pour vérification inline ---
FORBIDDEN='crucial|fondamental|primordial|incontournable|néanmoins|toutefois|dorénavant|dès lors|il convient de|captivant|fascinant|révolutionnaire|novateur|époustouflant|majestueux|remarquable|exceptionnel|inégalé|indéniablement|assurément|indubitablement|incontestablement|véritablement|considérablement|substantiellement|pléthore|myriade|subséquent|tapisserie|pierre angulaire|fer de lance|exacerber|appréhender|corroborer|éluder|entraver|préconiser|prôner|stipuler|soulignons que|notons que|mentionnons que'

# ============================================================
# Preprocessing
# ============================================================
preprocess_one() {
    local slug="$1" keyword="$2" branch="$3" parent="$4" order="$5"
    if [ -f "/tmp/preprocess-${slug}/prompt-data.md" ] && [ "$SKIP_PREPROCESS" = true ]; then
        echo "[$slug] Preprocess: skip (données existantes)"
        return 0
    fi
    "$SCRIPT_DIR/preprocess-article.sh" "$slug" "$keyword" "$branch" "$parent" "$order"
}

# ============================================================
# API call : Anthropic Messages API
# ============================================================
call_anthropic() {
    local slug="$1" user_content="$2" output_mdx="$3" output_meta="$4"

    local payload
    payload=$(jq -n \
        --arg model "$MODEL_ID" \
        --argjson max_tokens "$MAX_TOKENS" \
        --arg system "$SYSTEM_PROMPT" \
        --arg user "$user_content" \
        '{
            model: $model,
            max_tokens: $max_tokens,
            system: $system,
            messages: [{role: "user", content: $user}]
        }')

    local start_time response end_time elapsed_ms
    start_time=$(date +%s%N)

    response=$(curl -s --max-time 300 \
        -X POST "https://api.anthropic.com/v1/messages" \
        -H "content-type: application/json" \
        -H "x-api-key: $ANTHROPIC_API_KEY" \
        -H "anthropic-version: 2023-06-01" \
        -d "$payload" 2>/dev/null) || {
        echo "[$slug] Erreur: appel API Anthropic échoué" >&2
        echo '{"error":"api_call_failed"}' > "$output_meta"
        return 1
    }

    end_time=$(date +%s%N)
    elapsed_ms=$(( (end_time - start_time) / 1000000 ))

    # Check error
    local api_error
    api_error=$(echo "$response" | jq -r '.error.message // empty' 2>/dev/null || true)
    if [ -n "$api_error" ]; then
        echo "[$slug] Erreur API Anthropic: $api_error" >&2
        echo "$response" > "$output_meta"
        return 1
    fi

    # Extract text
    local article_text
    article_text=$(echo "$response" | jq -r '.content[0].text // empty' 2>/dev/null || true)
    if [ -z "$article_text" ]; then
        echo "[$slug] Erreur: réponse Anthropic vide" >&2
        echo "$response" > "$output_meta"
        return 1
    fi

    # Strip code fences
    article_text=$(echo "$article_text" | sed -E '1s/^```(mdx|markdown|yaml)?[[:space:]]*$//' | sed -E '$ s/^```[[:space:]]*$//')
    echo "$article_text" > "$output_mdx"

    # Usage
    local input_tokens output_tokens stop_reason
    input_tokens=$(echo "$response" | jq -r '.usage.input_tokens // 0')
    output_tokens=$(echo "$response" | jq -r '.usage.output_tokens // 0')
    stop_reason=$(echo "$response" | jq -r '.stop_reason // "unknown"')

    jq -n \
        --arg slug "$slug" \
        --arg model "$MODEL_ID" \
        --arg provider "anthropic" \
        --argjson input_tokens "$input_tokens" \
        --argjson output_tokens "$output_tokens" \
        --argjson elapsed_ms "$elapsed_ms" \
        --arg stop_reason "$stop_reason" \
        '{slug: $slug, model: $model, provider: $provider, input_tokens: $input_tokens, output_tokens: $output_tokens, elapsed_ms: $elapsed_ms, stop_reason: $stop_reason}' \
        > "$output_meta"

    echo "[$slug] OK (${input_tokens}in/${output_tokens}out, ${elapsed_ms}ms, stop:${stop_reason})"
}

# ============================================================
# API call : OpenAI Responses API
# ============================================================
call_openai() {
    local slug="$1" user_content="$2" output_mdx="$3" output_meta="$4"

    local payload
    payload=$(jq -n \
        --arg model "$MODEL_ID" \
        --argjson max_output_tokens "$MAX_TOKENS" \
        --arg instructions "$SYSTEM_PROMPT" \
        --arg input "$user_content" \
        '{
            model: $model,
            max_output_tokens: $max_output_tokens,
            instructions: $instructions,
            input: $input
        }')

    local start_time response end_time elapsed_ms
    start_time=$(date +%s%N)

    response=$(curl -s --max-time 300 \
        -X POST "https://api.openai.com/v1/responses" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $OPENAI_API_KEY" \
        -d "$payload" 2>/dev/null) || {
        echo "[$slug] Erreur: appel API OpenAI échoué" >&2
        echo '{"error":"api_call_failed"}' > "$output_meta"
        return 1
    }

    end_time=$(date +%s%N)
    elapsed_ms=$(( (end_time - start_time) / 1000000 ))

    # Check error
    local api_error
    api_error=$(echo "$response" | jq -r '.error.message // empty' 2>/dev/null || true)
    if [ -n "$api_error" ]; then
        echo "[$slug] Erreur API OpenAI: $api_error" >&2
        echo "$response" > "$output_meta"
        return 1
    fi

    # Extract text : cherche le bloc type=message dans output[]
    local article_text
    article_text=$(echo "$response" | jq -r '[ .output[] | select(.type == "message") | .content[] | select(.type == "output_text") | .text ] | first // empty' 2>/dev/null || true)
    if [ -z "$article_text" ]; then
        echo "[$slug] Erreur: réponse OpenAI vide" >&2
        echo "$response" > "$output_meta"
        return 1
    fi

    # Strip code fences
    article_text=$(echo "$article_text" | sed -E '1s/^```(mdx|markdown|yaml)?[[:space:]]*$//' | sed -E '$ s/^```[[:space:]]*$//')
    echo "$article_text" > "$output_mdx"

    # Usage
    local input_tokens output_tokens stop_reason
    input_tokens=$(echo "$response" | jq -r '.usage.input_tokens // 0')
    output_tokens=$(echo "$response" | jq -r '.usage.output_tokens // 0')
    stop_reason=$(echo "$response" | jq -r '.status // "unknown"')

    jq -n \
        --arg slug "$slug" \
        --arg model "$MODEL_ID" \
        --arg provider "openai" \
        --argjson input_tokens "$input_tokens" \
        --argjson output_tokens "$output_tokens" \
        --argjson elapsed_ms "$elapsed_ms" \
        --arg stop_reason "$stop_reason" \
        '{slug: $slug, model: $model, provider: $provider, input_tokens: $input_tokens, output_tokens: $output_tokens, elapsed_ms: $elapsed_ms, stop_reason: $stop_reason}' \
        > "$output_meta"

    echo "[$slug] OK (${input_tokens}in/${output_tokens}out, ${elapsed_ms}ms, status:${stop_reason})"
}

# ============================================================
# Dispatch : choisit le bon provider
# ============================================================
write_one() {
    local slug="$1" keyword="$2" branch="$3" parent="$4" order="$5"
    local prompt_data="/tmp/preprocess-${slug}/prompt-data.md"
    local output_mdx="$BENCH_DIR/${slug}.md"
    local output_meta="$BENCH_DIR/${slug}.meta.json"

    if [ ! -f "$prompt_data" ]; then
        echo "[$slug] Erreur: $prompt_data introuvable (preprocess manqué ?)" >&2
        echo '{"error":"prompt-data manquant"}' > "$output_meta"
        return 1
    fi

    local user_content
    user_content=$(cat "$prompt_data")
    user_content="Rédige l'article Markdown complet à partir des données ci-dessous. Retourne uniquement le MDX (frontmatter + corps), rien d'autre.

${user_content}"

    case "$PROVIDER" in
        anthropic)  call_anthropic "$slug" "$user_content" "$output_mdx" "$output_meta" ;;
        openai)     call_openai    "$slug" "$user_content" "$output_mdx" "$output_meta" ;;
    esac
}

# ============================================================
# Vérification inline
# ============================================================
verify_one() {
    local slug="$1"
    local filepath="$BENCH_DIR/${slug}.md"

    if [ ! -f "$filepath" ]; then
        echo "$slug|-|-|-|-|-|-|MANQUANT"
        return
    fi

    local words accents forbidden_count typo_count callout_count mermaid_count
    words=$(awk 'BEGIN{c=0} /^---$/{c++; next} c>=2{print}' "$filepath" | wc -w | tr -d ' ') || words=0
    accents=$(grep -o '[éèêëàâùûîïôçÉÈÊËÀÂÙÛÎÏÔÇ]' "$filepath" 2>/dev/null | wc -l | tr -d ' ') || accents=0
    forbidden_count=$(grep -ciE "$FORBIDDEN" "$filepath" 2>/dev/null) || forbidden_count=0
    typo_count=$(grep -cP '[\x{2014}\x{2013}\x{2018}\x{2019}\x{201C}\x{201D}\x{2026}]' "$filepath" 2>/dev/null) || typo_count=0
    callout_count=$(grep -c '> \[!' "$filepath" 2>/dev/null) || callout_count=0
    mermaid_count=$(grep -c '```mermaid' "$filepath" 2>/dev/null) || mermaid_count=0

    local status="OK" issues=""
    [ "$accents" -lt 50 ] && issues="${issues}acc "
    [ "$forbidden_count" -gt 0 ] && issues="${issues}mots "
    [ "$typo_count" -gt 0 ] && issues="${issues}typo "
    [ "$callout_count" -lt 3 ] && issues="${issues}call< "
    [ "$callout_count" -gt 5 ] && issues="${issues}call> "
    [ "$mermaid_count" -lt 1 ] && issues="${issues}mmd< "
    [ "$mermaid_count" -gt 3 ] && issues="${issues}mmd> "
    [ "$words" -lt 1800 ] && issues="${issues}court "
    [ "$words" -gt 3000 ] && issues="${issues}long "
    if ! head -1 "$filepath" | grep -q '^---'; then
        issues="${issues}fm "
    fi

    [ -n "$issues" ] && status="WARN: ${issues}"
    echo "$slug|$words|$accents|$forbidden_count|$typo_count|$callout_count|$mermaid_count|$status"
}

# ============================================================
# Quiz generation
# ============================================================
quiz_one() {
    local slug="$1"
    local article_mdx="$BENCH_DIR/${slug}.md"
    local output_quiz="$BENCH_DIR/${slug}.quiz.json"

    if [ ! -f "$article_mdx" ]; then
        echo "[$slug] Quiz: article MDX manquant, skip"
        return 1
    fi

    if [ -z "$QUIZ_PROMPT" ]; then
        echo "[$slug] Quiz: prompt manquant ($QUIZ_PROMPT_FILE), skip"
        return 1
    fi

    local article_content user_content
    article_content=$(cat "$article_mdx")
    user_content="Génère un quiz de 3 questions basé sur cet article :

${article_content}"

    local response quiz_text

    case "$PROVIDER" in
        anthropic)
            local payload
            payload=$(jq -n \
                --arg model "$MODEL_ID" \
                --argjson max_tokens 1024 \
                --arg system "$QUIZ_PROMPT" \
                --arg user "$user_content" \
                '{model: $model, max_tokens: $max_tokens, system: $system, messages: [{role: "user", content: $user}]}')

            response=$(curl -s --max-time 120 \
                -X POST "https://api.anthropic.com/v1/messages" \
                -H "content-type: application/json" \
                -H "x-api-key: $ANTHROPIC_API_KEY" \
                -H "anthropic-version: 2023-06-01" \
                -d "$payload" 2>/dev/null) || {
                echo "[$slug] Quiz: erreur API Anthropic" >&2
                return 1
            }
            quiz_text=$(echo "$response" | jq -r '.content[0].text // empty' 2>/dev/null || true)
            ;;
        openai)
            local payload
            payload=$(jq -n \
                --arg model "$MODEL_ID" \
                --argjson max_output_tokens 1024 \
                --arg instructions "$QUIZ_PROMPT" \
                --arg input "$user_content" \
                '{model: $model, max_output_tokens: $max_output_tokens, instructions: $instructions, input: $input}')

            response=$(curl -s --max-time 120 \
                -X POST "https://api.openai.com/v1/responses" \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer $OPENAI_API_KEY" \
                -d "$payload" 2>/dev/null) || {
                echo "[$slug] Quiz: erreur API OpenAI" >&2
                return 1
            }
            quiz_text=$(echo "$response" | jq -r '[ .output[] | select(.type == "message") | .content[] | select(.type == "output_text") | .text ] | first // empty' 2>/dev/null || true)
            ;;
    esac

    if [ -z "$quiz_text" ]; then
        echo "[$slug] Quiz: réponse vide" >&2
        return 1
    fi

    # Strip potential code fences (```json ... ```)
    quiz_text=$(echo "$quiz_text" | sed -E '1s/^```(json)?[[:space:]]*$//' | sed -E '$ s/^```[[:space:]]*$//')

    # Validate JSON and check structure (3 questions required)
    if echo "$quiz_text" | jq -e '.title and .questions and (.questions | length == 3)' >/dev/null 2>&1; then
        echo "$quiz_text" | jq '.' > "$output_quiz"
        echo "[$slug] Quiz: OK (3 questions)"
    else
        echo "[$slug] Quiz: JSON invalide ou structure incorrecte" >&2
        echo "$quiz_text" > "${output_quiz}.raw"
        return 1
    fi
}

# ============================================================
# Main
# ============================================================

# Read CSV (skip header)
declare -a SLUGS KEYWORDS BRANCHES PARENTS ORDERS
while IFS=',' read -r slug keyword branch parent order; do
    [[ "$slug" == "slug" ]] && continue
    [[ -z "$slug" ]] && continue
    slug=$(echo "$slug" | tr -d ' ')
    branch=$(echo "$branch" | tr -d ' ')
    parent=$(echo "$parent" | tr -d ' ')
    order=$(echo "$order" | tr -d ' ')
    SLUGS+=("$slug")
    KEYWORDS+=("$keyword")
    BRANCHES+=("$branch")
    PARENTS+=("$parent")
    ORDERS+=("$order")
done < "$ARTICLES_CSV"

TOTAL=${#SLUGS[@]}
echo "Articles à traiter : $TOTAL"
echo ""

# --- Phase 1 : Preprocessing ---
if [ "$SKIP_PREPROCESS" = false ]; then
    echo "=== Phase 1 : Preprocessing ==="
    PREPROCESS_PIDS=()
    for i in "${!SLUGS[@]}"; do
        preprocess_one "${SLUGS[$i]}" "${KEYWORDS[$i]}" "${BRANCHES[$i]}" "${PARENTS[$i]}" "${ORDERS[$i]}" &
        PREPROCESS_PIDS+=($!)
        if [ $(( (i + 1) % PARALLEL )) -eq 0 ]; then
            for pid in "${PREPROCESS_PIDS[@]}"; do wait "$pid" 2>/dev/null || true; done
            PREPROCESS_PIDS=()
        fi
    done
    for pid in "${PREPROCESS_PIDS[@]}"; do wait "$pid" 2>/dev/null || true; done
    echo ""
fi

# --- Phase 2 : Rédaction ---
echo "=== Phase 2 : Rédaction ($MODEL_SHORT via $PROVIDER) ==="
# Cooldown auto : 30s pour Anthropic (rate limit), 0 pour OpenAI
if [ "$COOLDOWN" -eq -1 ]; then
    if [ "$PROVIDER" = "anthropic" ]; then
        COOLDOWN=30
    else
        COOLDOWN=0
    fi
fi
if [ "$COOLDOWN" -gt 0 ]; then
    echo "  (cooldown ${COOLDOWN}s entre articles, parallèle: $PARALLEL)"
fi

WRITE_PIDS=()
STARTED=0
for i in "${!SLUGS[@]}"; do
    # Cooldown entre articles (pas avant le premier)
    if [ "$COOLDOWN" -gt 0 ] && [ "$STARTED" -gt 0 ]; then
        echo "  ... cooldown ${COOLDOWN}s ..."
        sleep "$COOLDOWN"
    fi
    write_one "${SLUGS[$i]}" "${KEYWORDS[$i]}" "${BRANCHES[$i]}" "${PARENTS[$i]}" "${ORDERS[$i]}" &
    WRITE_PIDS+=($!)
    STARTED=$((STARTED + 1))
    if [ $(( STARTED % PARALLEL )) -eq 0 ]; then
        for pid in "${WRITE_PIDS[@]}"; do wait "$pid" 2>/dev/null || true; done
        WRITE_PIDS=()
    fi
done
for pid in "${WRITE_PIDS[@]}"; do wait "$pid" 2>/dev/null || true; done
echo ""

# --- Phase 2b : Quiz ---
if [ -n "$QUIZ_PROMPT" ]; then
    echo "=== Phase 2b : Génération des quiz ==="
    QUIZ_DONE=0
    for i in "${!SLUGS[@]}"; do
        if [ "$COOLDOWN" -gt 0 ] && [ "$QUIZ_DONE" -gt 0 ]; then
            echo "  ... cooldown ${COOLDOWN}s ..."
            sleep "$COOLDOWN"
        fi
        quiz_one "${SLUGS[$i]}" && QUIZ_DONE=$((QUIZ_DONE + 1)) || true
    done
    echo "  $QUIZ_DONE/$TOTAL quiz générés"
    echo ""
else
    echo "=== Phase 2b : Quiz ignoré (prompt manquant) ==="
    echo ""
fi

# --- Phase 3 : Vérification ---
echo "=== Phase 3 : Vérification ==="
printf "%-30s %6s %5s %4s %4s %5s %4s  %s\n" "Article" "Mots" "Acc" "Int" "Typo" "Call" "Mmd" "Statut"
printf "%-30s %6s %5s %4s %4s %5s %4s  %s\n" "-------" "----" "---" "---" "----" "----" "---" "------"

for slug in "${SLUGS[@]}"; do
    result=$(verify_one "$slug")
    IFS='|' read -r s_slug s_words s_acc s_int s_typo s_call s_mmd s_status <<< "$result"
    printf "%-30s %6s %5s %4s %4s %5s %4s  %s\n" "$s_slug" "$s_words" "$s_acc" "$s_int" "$s_typo" "$s_call" "$s_mmd" "$s_status"
done
echo ""

# --- Phase 4 : Rapport ---
echo "=== Rapport ==="
TOTAL_INPUT=0
TOTAL_OUTPUT=0
TOTAL_TIME=0
SUCCESS=0
ERRORS=0

for slug in "${SLUGS[@]}"; do
    meta="$BENCH_DIR/${slug}.meta.json"
    if [ -f "$meta" ] && [ "$(jq -r '.error // empty' "$meta" 2>/dev/null)" = "" ]; then
        input_t=$(jq -r '.input_tokens // 0' "$meta")
        output_t=$(jq -r '.output_tokens // 0' "$meta")
        elapsed=$(jq -r '.elapsed_ms // 0' "$meta")
        TOTAL_INPUT=$((TOTAL_INPUT + input_t))
        TOTAL_OUTPUT=$((TOTAL_OUTPUT + output_t))
        TOTAL_TIME=$((TOTAL_TIME + elapsed))
        SUCCESS=$((SUCCESS + 1))
    else
        ERRORS=$((ERRORS + 1))
    fi
done

read -r PRICE_IN PRICE_OUT <<< "$(model_prices "$MODEL_SHORT")"
if [ "$SUCCESS" -gt 0 ]; then
    COST_INPUT=$(echo "scale=4; $TOTAL_INPUT * $PRICE_IN / 1000000" | bc)
    COST_OUTPUT=$(echo "scale=4; $TOTAL_OUTPUT * $PRICE_OUT / 1000000" | bc)
    COST_TOTAL=$(echo "scale=4; $COST_INPUT + $COST_OUTPUT" | bc)
    AVG_TIME=$((TOTAL_TIME / SUCCESS))
    AVG_INPUT=$((TOTAL_INPUT / SUCCESS))
    AVG_OUTPUT=$((TOTAL_OUTPUT / SUCCESS))
    COST_PER=$(echo "scale=4; $COST_TOTAL / $SUCCESS" | bc)
else
    COST_INPUT="0"; COST_OUTPUT="0"; COST_TOTAL="0"; COST_PER="0"
    AVG_TIME=0; AVG_INPUT=0; AVG_OUTPUT=0
fi

echo "  Modèle         : $MODEL_SHORT ($MODEL_ID)"
echo "  Provider       : $PROVIDER"
echo "  Articles       : $SUCCESS OK, $ERRORS erreurs / $TOTAL total"
echo "  Tokens input   : $TOTAL_INPUT (moy: ${AVG_INPUT}/article)"
echo "  Tokens output  : $TOTAL_OUTPUT (moy: ${AVG_OUTPUT}/article)"
echo "  Temps moyen    : ${AVG_TIME}ms/article"
echo "  Coût input     : \$${COST_INPUT}"
echo "  Coût output    : \$${COST_OUTPUT}"
echo "  Coût total     : \$${COST_TOTAL}"
echo "  Coût/article   : \$${COST_PER}"
echo ""
echo "  Fichiers MD   : $BENCH_DIR/*.md"
echo "  Métadonnées    : $BENCH_DIR/*.meta.json"
echo ""

# Save summary
jq -n \
    --arg model "$MODEL_ID" \
    --arg model_short "$MODEL_SHORT" \
    --arg provider "$PROVIDER" \
    --argjson total "$TOTAL" \
    --argjson success "$SUCCESS" \
    --argjson errors "$ERRORS" \
    --argjson input_tokens "$TOTAL_INPUT" \
    --argjson output_tokens "$TOTAL_OUTPUT" \
    --arg cost_input "$COST_INPUT" \
    --arg cost_output "$COST_OUTPUT" \
    --arg cost_total "$COST_TOTAL" \
    --argjson avg_time_ms "$AVG_TIME" \
    '{model: $model, model_short: $model_short, provider: $provider, total: $total, success: $success, errors: $errors, input_tokens: $input_tokens, output_tokens: $output_tokens, cost_input: $cost_input, cost_output: $cost_output, cost_total: $cost_total, avg_time_ms: $avg_time_ms}' \
    > "$BENCH_DIR/summary.json"

# --- Phase 5 : Merge quiz dans le projet ---
QUIZ_COUNT=$(find "$BENCH_DIR" -name "*.quiz.json" 2>/dev/null | wc -l | tr -d ' ')
if [ "$QUIZ_COUNT" -gt 0 ] && [ -f "$QUIZ_JSON" ]; then
    echo "=== Phase 5 : Merge quiz ($QUIZ_COUNT) ==="
    for f in "$BENCH_DIR"/*.quiz.json; do
        slug=$(basename "$f" .quiz.json)
        jq --arg slug "$slug" --slurpfile quiz "$f" \
            '. + {($slug): $quiz[0]}' "$QUIZ_JSON" > "${QUIZ_JSON}.tmp" \
            && mv "${QUIZ_JSON}.tmp" "$QUIZ_JSON"
        echo "  [$slug] quiz ajouté à quizzes.json"
    done
    echo ""
fi

# --- Phase 6 : Déploiement des articles validés ---
if [ "$NO_DEPLOY" = false ]; then
    echo "=== Phase 6 : Déploiement ==="
    DEPLOYED=0
    for i in "${!SLUGS[@]}"; do
        slug="${SLUGS[$i]}"
        branch="${BRANCHES[$i]}"
        result=$(verify_one "$slug")
        status="${result##*|}"

        if [ "$status" = "OK" ]; then
            target_dir="$SITE_DIR/src/content/guides/$branch"
            mkdir -p "$target_dir"
            cp "$BENCH_DIR/${slug}.md" "$target_dir/${slug}.md"
            echo "  [$slug] -> site/src/content/guides/$branch/${slug}.md"
            DEPLOYED=$((DEPLOYED + 1))
        else
            echo "  [$slug] SKIP ($status)"
        fi
    done
    echo "  $DEPLOYED/$TOTAL articles déployés"
    echo ""
else
    echo "=== Phase 6 : Déploiement ignoré (--no-deploy) ==="
    echo ""
fi

echo "Résumé JSON : $BENCH_DIR/summary.json"
