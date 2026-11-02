# events-front — лендинги событий (EF)

Заведено приёмкой блока 1 (2026-11-02). Исходное состояние дева: опубликованы `cambridge-day`
(день 14.11.2026 11:00–14:00) и `cambridge-programme-leader` (21–22.11), `skills-xxi` — черновик.
Сценарии со временными состояниями (E3, E5) возвращают его в конце. Макеты — `memory/frontend/
design.md#screens-events` (репо процесса), допустимые расхождения — там же `#deltas`.

## E1. Day — лендинг, 1440

1. `/ru/astana/event/cambridge-day/` → 200, `h1` «Cambridge Day», в hero Date card «Ноября / 14 /
   11:00–14:00 | Стоимость / Бесплатно / по предварительной регистрации», одна кнопка
   «Зарегистрироваться бесплатно».
2. Секции по порядку: «Для кого» (заголовок + «Цель») → «Программа дня» (мета «Сб, 14 ноября ·
   8 блоков · 11:00–14:00», 8 строк в 2 колонки) → «Ведущие» (карточки админ-состава Астаны либо
   «Ведущий будет объявлен») → «О Space School» (текст главной + карусель + полоса «Сб, 14 ноября ·
   11:00–14:00 / Участие бесплатное, по предварительной регистрации.» с кнопкой) → «Регистрация на Cambridge Day» (2 кнопки) → «Ближайшие события» (только
   Leader; черновика Skills нет) → футер.
3. `[data-feedback-origin]` на странице: `-hero`, `-reg` (×2), `-consult`, `-sticky`; нет
   `data-feedback-price`. Sticky CTA на десктопе `display: none`. Консоль чистая.

## E2. Day — мобильная 393

1. `mobile('/ru/astana/event/cambridge-day/')` → `sw === 393`.
2. Hero: бейдж, заголовок, лид, Date card, кнопка на всю ширину; sticky CTA не виден.
3. Прокрутить ниже hero → sticky «Зарегистрироваться бесплатно» + «Сб, 14 ноября · 11:00–14:00 ·
   Space School» снизу; программа — сплошной таймлайн в одну колонку.

## E3. Модалка Day → заявка «Мероприятие»

1. На Day клик «Зарегистрироваться бесплатно» в hero → модалка «Регистрация на Cambridge Day»,
   подзаголовок `form_lead` Day; строки цены и чекбокса нет.
2. Имя `Приёмка <ID> Day`, телефон `7000000001`, «Отправить» → «Заявка принята!», «Перезвоним вам
   в течение 2 часов» + «Участие бесплатное, по предварительной регистрации.».
3. БД/admin: `Lead` региона astana, `category = event` («Мероприятие»), `origin =
   event-cambridge-day-hero`, `title` «Регистрация на Cambridge Day», `extra` пусто;
   `/admin/feedback/lead/<pk>/change/` — поле «Доп. от пользователя»; `/backoffice/leads/` —
   заявка видна. Удалить тестовую заявку.

## E4. Skills — цена и чекбокс → `extra` (временная публикация)

1. Опубликовать `skills-xxi` (admin или shell). `/ru/astana/event/skills-xxi/` → 200, Date card
   «18 990 ₸», кнопки «Зарегистрироваться · 18 990 ₸», 9 строк программы, перерыв приглушён и с
   текстом «Короткий отдых.», ведущий — плейсхолдер «Ведущий будет объявлен», полоса «Школы» —
   «18 990 ₸ · родителям Space School бесплатно».
2. Клик в hero → модалка «Регистрация на воркшоп», строка «18 990 ₸ · оплата после
   подтверждения», чекбокс «Я родитель ученика Space School» (облик кита: золото + галочка).
3. Отметить чекбокс, отправить (`Приёмка <ID> Skills`, `7000000002`) → успех «Перезвоним…» +
   «Оплата после подтверждения участия.»; `Lead.extra` = «Я родитель ученика Space School»,
   `category = event`, `origin = event-skills-xxi-hero`.
4. Закрыть, открыть «Получить консультацию» → без цены и чекбокса (`extra` disabled), origin
   `event-skills-xxi-consult`.
5. `/kk/astana/event/skills-xxi/` → подпись чекбокса «Мен Space School оқушысының ата-анасымын»,
   цена «… · қатысуды растағаннан кейін төлем», а `value` чекбокса — русская строка.
6. **Вернуть в черновик** → `/ru/astana/event/skills-xxi/` 404. Удалить тестовую заявку.

## E5. Day — «прошло» (временный сдвиг даты)

1. Дату дня Day → 2026-10-31. `/ru/astana/event/cambridge-day/` → 200, вместо Date card и кнопок —
   плашка «Событие состоялось 31 октября»; «Ближайшие события» (Leader) сразу под hero; блок
   регистрации события и sticky отсутствуют; перед футером — общий блок с origin
   `event-cambridge-day-primary` / `-city`.
2. 393: то же, без горизонтального скролла.
3. `/ru/astana/events/` → карточка Day «31 октября 2026 · Состоялось»; у Leader в «Ближайших» Day нет.
4. **Вернуть дату 2026-11-14** → на Day снова есть `event-cambridge-day-hero`.

## E6. Leader — два дня, плитки, материалы

1. `/ru/astana/event/cambridge-programme-leader/` → Date card «21–22 / 09:30–17:00 | 50 000 ₸ / за
   участника за два дня»; «Для кого» — плитки «Язык» и «Группа»; программа — 2 колонки «День 1 · 21
   ноября» / «День 2 · 22 ноября», 20 строк, перерывы приглушены; «Материалы участника» — 7 пунктов.
2. «Ближайшие» — Day (пока не прошёл). Консоль чистая.

## E7. Лента `/events/`

1. `/ru/astana/events/` → лендинги и новости одной сеткой базовой `.article-card`, по убыванию даты
   (Leader 21.11 → Day 14.11 → новости); черновика Skills нет; у лендингов нет цены.
2. `/kk/astana/events/`, `/en/astana/events/` → 200, UI переведён.
3. `/ru/aktau/events/` → только новости (ни одной ссылки `/event/`).

## E8. Мультирегион и i18n

1. `/ru/aktau/event/cambridge-day/`, `/kk/aktau/event/cambridge-programme-leader/` → 404.
2. `/kk/astana/event/cambridge-day/` → 200, `<html lang="kk">`; UI на казахском (section-label
   «Кімге арналған / Бағдарлама / Жүргізушілер / Алдағы іс-шаралар», Date card «Бағасы / Тегін»,
   «Кеңес алу»); контент событий — RU (fallback, норма до заполнения менеджерами).
3. `/en/astana/event/cambridge-day/` → UI на английском («Who it is for», «Price / Free»).

## E9. Главная — карусель и модалка (регрессия)

1. `/ru/astana/` и `/kk/astana/`: у `.carousel-infinity` нет Alpine-атрибутов; трек —
   `animation: 40s linear infinite reverse carousel-scroll`, `playbackRate 1`; смещение за 1 с в
   покое и при активной прокрутке страницы одинаково (~73 px/с); в собранном CSS есть
   `@media (prefers-reduced-motion:reduce){.carousel-track{animation:none}}`. Консоль чистая.
2. Кнопка hero → модалка «Поступить сейчас», подзаголовок «Перезвоним в течение 2 часов и ответим
   на все вопросы о поступлении», без цены/чекбокса; origin главной — `hero-primary`,
   `hero-secondary`, `home-primary`, `home-city`.

## E10. Sitemap и admin

1. `/sitemap.xml` → 200, `application/xml`; есть `/{ru,kk,en}/astana/event/cambridge-day/` и
   `…/cambridge-programme-leader/`, `/{ru,kk,en}/{astana,aktau}/events/`; нет `skills-xxi` и лендингов
   Актау.
2. Admin (рендер под суперпользователем, см. README): `/admin/eventlandings/eventlanding/add/` —
   поля `_ru/_kk/_en`, inlines дней/материалов/плиток/галереи, `filter_horizontal` ведущих;
   change Day — в списке ведущих только команда Астаны; `/admin/eventlandings/eventlandingday/<pk>/
   change/` — inline строк программы; `/admin/feedback/lead/` — фильтр «Мероприятие».
