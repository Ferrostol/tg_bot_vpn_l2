#!/bin/bash
set -euo pipefail

REPO="Ferrostol/tg_bot_vpn_l2"

CURRENT_DIR="$(pwd)"
# Проверим наличие уже ранее выбранной ветки
BRANCH_FILE="${CURRENT_DIR}/BRANCH"
BRANCH=""

if [[ -s "$BRANCH_FILE" ]]; then
  saved_branch="$(head -n 1 "$BRANCH_FILE" | tr -d '\r')"
  if [[ -z "$saved_branch" ]]; then
    echo "Файл с ранее выбранной веткой пуст. Выбираем заново"
  else
    http_code="$(curl -sS -o /dev/null -w '%{http_code}' "https://api.github.com/repos/${REPO}/branches/${saved_branch}")" || http_code="000"
    case "${http_code}" in
      200)
        BRANCH="$saved_branch"
        echo "Ветка взята из $BRANCH_FILE: $BRANCH"
        ;;
      400)
        echo "Ветка '$saved_branch' из $BRANCH_FILE не найдена в репозитории. Выбираем заново"
        ;;
      *)
        echo "Не удалось определить ветку '$saved_branch' (HTTP код $http_code). " >&2
        exit 1
        ;;
    esac
  fi
fi


if [[ -z "$BRANCH" ]]; then
  # Получим список веток
  response="$(curl -fsS "https://api.github.com/repos/${REPO}/branches?per_page=10")" || {
    echo "Не удалось получить список веток репозитория" >&2
    exit 1
  }


  BRANCHES=()
  while IFS= read -r name; do
    [[ -n "$name" ]] && BRANCHES+=("$name")
  done < <(printf '%s' "$response" | grep -oE '"name": *"[^"]*"' | sed -E 's/^"name": *"(.*)"$/\1/')

  count=${#BRANCHES[@]}

  if (( count == 1 )); then
    BRANCH="${BRANCHES[0]}"
    echo "В репозитории одна ветка, выбрана автоматически: $BRANCH"
  else
    echo "Доступные ветки в репозитории:"
    for i in "${!BRANCHES[@]}"; do
      printf ' %d) %s\n' "$((i + 1))" "${BRANCHES[$i]}"
    done

    BRANCH=""
    while [[ -z "$BRANCH" ]]; do
      read -rp "Введите номер ветки (1-${count}): " num
      if [[ "$num" =~ ^[0-9]+$ ]] && (( num >= 1 && num <= count )); then
        BRANCH="${BRANCHES[$((num - 1))]}"
      else
        echo "Неверный номер, попробуй еще раз."
      fi
    done
  fi
  printf '%s\n' "$BRANCH" > "$BRANCH_FILE"
fi

echo "Используется ветка: $BRANCH"


echo "Загружаем скрипт из ветки"
SCRIPT_URL="https://raw.githubusercontent.com/$REPO/refs/heads/$BRANCH/install.sh"
REMOTE_CODE="$(curl -fsS "$SCRIPT_URL")" || {
  echo "Не удалось загрузить скрипт с $SCRIPT_URL" >&2
  exit 1
}

if [[ -z REMOTE_CODE ]]; then
  echo "Скрипт пустой"
  exit 1
fi


bash -c "$REMOTE_CODE" install "$BRANCH"
