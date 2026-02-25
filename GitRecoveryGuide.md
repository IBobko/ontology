# Инструкция, если «git сломался» после rebase

Короткий сценарий для типичных ошибок:

- `! [rejected] main -> main (non-fast-forward)`
- `some local refs could not be updated`

## 1) Сделай страховку

```bash
git status
git branch --show-current
git branch backup/local-main-before-fix
git tag backup-before-fix-$(date +%Y%m%d-%H%M%S)
```

## 2) Почини локальные remote refs

```bash
git remote prune origin
git fetch --all --prune
git branch -r | grep codex
```

Если ошибка про refs не ушла:

```bash
rm -rf .git/refs/remotes/origin
git fetch origin --prune
```

## 3) Выбери стратегию по `main`

### Вариант A (рекомендуется): сохранить remote `main`

```bash
git fetch origin
git rebase origin/main
git push
```

Если снова reject, повтори:

```bash
git fetch origin
git rebase origin/main
git push
```

### Вариант B: осознанно перезаписать remote `main`

Используй, только если точно понимаешь последствия:

```bash
git fetch origin
git checkout main
git push --force-with-lease origin main
```

## 4) Быстрая проверка, что всё синхронизировалось

```bash
git status
git branch -vv
git log -1 --decorate --oneline
git push
```

Ожидаемо: `Everything up-to-date`.
