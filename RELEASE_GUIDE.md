# Руководство по релизам AsyncMaxBot SDK

Этот документ описывает пошаговый процесс создания нового релиза библиотеки.

## 1. Подготовка к релизу

Перед началом релиза убедитесь, что все необходимые изменения влиты в ветку `develop`.

### 1.1. Обновление версии

Необходимо обновить номер версии в следующих файлах:

- `pyproject.toml` (например, `version = "X.Y.Z"`)
- `maxbot/__init__.py` (например, `__version__ = "X.Y.Z"`)
- `CHANGELOG.md`: Добавить новый раздел для релиза.
- Все файлы документации (`.md`) и примеры (`.py`), где упоминается старая версия.

Используйте поиск по проекту для нахождения всех упоминаний старой версии.

## 2. Процесс релиза в Git (Git Flow)

Мы используем Git Flow. Процесс состоит из следующих шагов:

1.  **Создать release-ветку** из `develop`:
    ```bash
    git checkout -b release/vX.Y.Z develop
    ```

2.  **Сделать коммит** с подготовкой релиза:
    ```bash
    git commit -am "chore: prepare release vX.Y.Z"
    ```

3.  **Влить релиз в `main`**:
    ```bash
    git checkout main
    git merge --no-ff release/vX.Y.Z
    ```

4.  **Создать Git-тег**:
    ```bash
    git tag -a vX.Y.Z -m "Release vX.Y.Z"
    ```

5.  **Влить релиз в `develop`**:
    ```bash
    git checkout develop
    git merge --no-ff release/vX.Y.Z
    ```

6.  **Удалить release-ветку**:
    ```bash
    git branch -d release/vX.Y.Z
    ```

7.  **Отправить изменения** на GitHub:
    ```bash
    git push origin main develop --tags
    ```

## 3. Публикация

### 3.1. PyPI

1.  **Очистить старые сборки** (ВАЖНО!):
    ```bash
    rm -r dist
    ```

2.  **Собрать пакет**:
    ```bash
    python -m build
    ```

3.  **Загрузить на PyPI**:
    ```bash
    twine upload --username __token__ --password <YOUR_PYPI_TOKEN> dist/*
    ```

### 3.2. GitHub Release

1.  **Создать релиз на GitHub** с помощью `gh` CLI:
    ```bash
    gh release create vX.Y.Z --title "Release vX.Y.Z" --notes-from-tag
    ```
    Или можно добавить заметки вручную:
    ```bash
    gh release create vX.Y.Z --title "Release vX.Y.Z" --notes "Описание релиза..."
    ```

## 4. Обновление документации

После релиза необходимо обновить документацию на GitHub Pages:

```bash
mkdocs gh-deploy --clean
```

## 5. Работа с тегами (исправление ошибок)

Если необходимо удалить некорректный релиз/тег:

1.  **Удалить релиз на GitHub**:
    ```bash
    gh release delete <tag_name> --yes
    ```

2.  **Удалить тег локально**:
    ```bash
    git tag -d <tag_name>
    ```

3.  **Удалить тег на удаленном репозитории**:
    ```bash
    git push origin :refs/tags/<tag_name>
    ``` 