# e2e-набор — браузерные сценарии приёмки

Накопительный чек-лист: каждая приёмка блока гоняет **весь** набор (регрессия прошлых блоков),
а не только свой файл, и дописывает сюда новые сценарии. Автоматизации нет — сценарии гоняются
в реальном браузере на деве (Claude in Chrome или руками) по шагам «URL → действие → ожидание».

| Файл | Инициатива | Что покрывает |
|---|---|---|
| `events-front.md` | лендинги событий (EF) | лендинги Day/Skills/Leader, «прошло», модалка → `Lead`, лента `/events/`, карусель главной, sitemap, i18n, Актау |

## Подготовка стенда

- Из workspace `/tamos`: `docker compose up -d` → дев http://localhost:8000.
- Ассеты на деве (`DEBUG=True`) отдаёт Vite dev-сервер `:3000`: `cd tamosapp/app/spaceschool && pnpm dev`
  (новый файл в `spaceschool/pages/` подхватывается только после перезапуска `pnpm dev`).
- Гейты до браузера: `docker compose exec tamosapp python manage.py check` ·
  `makemigrations --check --dry-run` · `test`; `pnpm build` в `spaceschool/` (после сборки
  `git status` чист — артефакты `static/` закоммичены); CI на голове `main` зелёный (`gh run list --limit 1`).

## Приёмы

- **Ширина 393.** Окно Chrome не сужается до 393, а `X-Frame-Options: DENY` запрещает обычный
  iframe. На любой странице дева выполнить в консоли/`javascript_tool`:

  ```js
  window.mobile = async (url, w = 393, h = 780) => {
    const html = await fetch(url).then(r => r.text());
    const doc = html.replace('<head>', `<head><base href="${location.origin}${url}">`);
    document.body.innerHTML = ''; document.body.style.cssText = 'margin:0;background:#888';
    const f = document.createElement('iframe'); f.id = 'm';
    f.style.cssText = `width:${w}px;height:${h}px;border:0;background:#fff;display:block`;
    document.body.appendChild(f); f.srcdoc = doc;
    await new Promise(r => f.onload = r); await new Promise(r => setTimeout(r, 1500));
    return { iw: f.contentWindow.innerWidth, sw: f.contentDocument.documentElement.scrollWidth };
  };
  await mobile('/ru/astana/event/cambridge-day/');   // sw === 393 → нет горизонтального скролла
  ```

  Прокрутка — `document.getElementById('m').contentWindow.scrollTo(0, Y)`. Хелпер живёт до навигации.
- **Десктоп.** Ширина окна 1440–1535 — один брейкпоинт-диапазон (ниже `2xl`), годится как «1440».
- **Admin без пароля.** Пароль дев-суперпользователя у владельца; страницы admin/бэкофиса можно
  проверить рендером под суперпользователем без записи в БД:

  ```sh
  docker compose exec -T tamosapp python manage.py shell -c "
  from django.test import Client; from django.contrib.auth import get_user_model
  c = Client(HTTP_HOST='localhost'); c.force_login(get_user_model().objects.filter(is_superuser=True).first())
  r = c.get('/admin/feedback/lead/'); print(r.status_code, 'Мероприятие' in r.content.decode())"
  ```
- **Временные состояния** (публикация черновика, сдвиг даты) — через admin или `manage.py shell`
  `.update(...)`; **вернуть до конца сессии** и проверить возврат (URL черновика → 404).
- **Тестовые заявки** — имя с префиксом `Приёмка <ID>`, телефон `700000000N`; после сценария
  удалить только свои (`Lead.objects.filter(pk__in=[…], name__startswith='Приёмка')`).
- Консоль — без ошибок на каждой странице сценария (`read_console_messages`, `onlyErrors`).
