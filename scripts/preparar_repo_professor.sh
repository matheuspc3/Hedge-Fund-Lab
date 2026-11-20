#!/usr/bin/env bash
# Prepara a branch que leva o historico do Hedge-Fund-Lab (origin, repo do Matheus)
# para o repositorio oficial do TCC (remote "professor"), sem configs de IA/editor,
# relatorios de agentes, arquivos gerados do LaTeX e o lixo dos primeiros commits.
# Autor, data e mensagem de cada commit sao preservados; so os SHAs mudam.
# A reescrita e deterministica: rodar de novo com commits novos so acrescenta commits.
# NAO envia nada: ao final imprime o comando de push.
#
# Uso (na raiz do repo, Git Bash): bash scripts/preparar_repo_professor.sh
set -euo pipefail
export MSYS_NO_PATHCONV=1 FILTER_BRANCH_SQUELCH_WARNING=1

PROFESSOR_URL=https://github.com/cefet-rj-dal-members/tcc-lucas-matheus.git
BRANCH=integra-historico-hedge-fund-lab
REMOVER=".claude .obsidian AGENTS.md CLAUDE.md tcc2/agent-reports
  tcc2/main.acn tcc2/main.aux tcc2/main.bbl tcc2/main.fdb_latexmk tcc2/main.fls
  tcc2/main.ist tcc2/main.lof tcc2/main.log tcc2/main.lot tcc2/main.out tcc2/main.toc
  tcc2/main.acr tcc2/main.alg tcc2/main.slg tcc2/main.blg
  tcc2/overleaf/main.acn tcc2/overleaf/main.aux tcc2/overleaf/main.bbl
  tcc2/overleaf/main.fdb_latexmk tcc2/overleaf/main.fls tcc2/overleaf/main.ist
  tcc2/overleaf/main.lof tcc2/overleaf/main.log tcc2/overleaf/main.lot tcc2/overleaf/main.out
  tcc2/overleaf/main.toc tcc2/overleaf/main.acr tcc2/overleaf/main.alg tcc2/overleaf/main.slg
  tcc2/overleaf/main.blg
  hedgefundlab.db .coverage backup"

git remote get-url professor >/dev/null 2>&1 || git remote add professor "$PROFESSOR_URL"
git fetch -q origin
git fetch -q professor

# Se o PR ainda esta aberto, continua a branch dele; senao parte do main oficial.
base=professor/main
git rev-parse -q --verify "refs/remotes/professor/$BRANCH" >/dev/null && base="professor/$BRANCH"

raiz=$(git rev-parse --show-toplevel)
wt=$(mktemp -d)
trap 'cd "$raiz"; git worktree remove --force "$wt" 2>/dev/null || true' EXIT
git worktree add -q -B "$BRANCH" "$wt" "$base"
cd "$wt"

# 1) Copia filtrada do historico do projeto.
git branch -f _filtrado origin/main
git filter-branch -f --prune-empty \
  --index-filter "git rm -r -q --cached --ignore-unmatch -- $(echo $REMOVER)" _filtrado >/dev/null
git update-ref -d refs/original/refs/heads/_filtrado 2>/dev/null || true

# 2) Junta ao repositorio oficial. Conflito so ocorre na 1a vez (README/.gitignore do template).
if ! git merge -q --allow-unrelated-histories --no-edit \
     -m "Integra o historico do Hedge-Fund-Lab ao repositorio oficial do TCC" _filtrado; then
  outros=$(git diff --name-only --diff-filter=U | grep -vxE 'README.md|\.gitignore' || true)
  [ -z "$outros" ] || { echo "Conflitos inesperados:"; echo "$outros"; exit 1; }
  git checkout --theirs README.md
  { git show _filtrado:.gitignore
    printf '\n# --- template original do repositorio do TCC (R) ---\n'
    git show professor/main:.gitignore; } > .gitignore
  git add README.md .gitignore
  git commit -q --no-edit
fi

# 3) Checagem: nenhum caminho removido aparece em nenhum commit do resultado.
vazou=$(git log --name-only --pretty=format: HEAD | grep -E '^(\.claude/|\.obsidian/|AGENTS\.md$|CLAUDE\.md$|tcc2/agent-reports/|tcc2/(overleaf/)?main\.(acn|aux|bbl|fdb_latexmk|fls|ist|lof|log|lot|out|toc|acr|alg|slg|blg)$|hedgefundlab\.db$|\.coverage$|backup/)' | sort -u || true)
[ -z "$vazou" ] || { echo "ERRO: caminhos removidos ainda no historico:"; echo "$vazou"; exit 1; }

git branch -D -q _filtrado
echo "OK: $(git rev-list --count HEAD) commits em $BRANCH (projeto original: $(git rev-list --count origin/main))."
echo "Para enviar: git push professor $BRANCH"
