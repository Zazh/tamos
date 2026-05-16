"""Инструкции для полей CMS.

Каждая запись — HTML-строка (mark_safe в template tag). Включает:
- 📝 Назначение поля
- 📐 Технические ограничения (длина, формат, размер)
- ✨ Описание текущего/референсного контента
- 🤖 AI-prompt для генерации (передаётся в Gemini/GPT)

Ключ — `'<model>.<field>'` (без суффикса языка для translatable полей).

Эта инструкция видна менеджеру в backoffice через раскрывающийся блок
«📖 Инструкция» под полем. Также её можно скопировать и передать в Gemini —
формат и язык подстроены под AI-prompt'инг.

При добавлении нового CMS-поля — добавь сюда запись с теми же 4 секциями,
менеджеру и AI всегда будет понятно что писать и какие ограничения.
"""


HOMEPAGE_HERO_IMAGE = """
<h4>📝 Назначение</h4>
<p>Полупрозрачный кинематографический снимок здания школы или окружения. Картинка ложится поверх синего градиента — <strong>прозрачность критична</strong>, иначе утратится атмосфера.</p>

<h4>✨ Текущий референс</h4>
<p>Здание школы на закате, экспозиция плавно нарастает снизу вверх (тёмный низ → светлый верх). Композиция кинематографическая, без людей в кадре.</p>

<h4>📐 Технические ограничения</h4>
<ul>
  <li>Формат: <strong>PNG</strong> (с альфа-каналом) или WebP с прозрачностью</li>
  <li>Размер: минимум 1920×1080, рекомендуется 2400×1350</li>
  <li>Соотношение: 16:9 (горизонтальное), без жёстких краёв — фотография «втапливается» в фон</li>
  <li>Вес исходника: <strong>до 5 MB</strong> (server-side validation отклонит больше)</li>
</ul>

<h4>🤖 Автоматическая обработка</h4>
<p>Картинка автоматически конвертируется в две версии:</p>
<ul>
  <li><code>image_webp</code> — WebP с качеством <strong>95</strong> (минимальная компрессия — hero крупный, важна детализация)</li>
  <li><code>image_compressed</code> — оптимизированный JPEG/PNG, качество 95</li>
</ul>
<p>На сайте через <code>&lt;picture&gt;</code> отдаётся самая лёгкая версия, которую поддерживает браузер. Resize до 800×800 <strong>не применяется</strong> (в отличие от галереи) — hero рендерится в полном размере.</p>

<h4>✨ AI-prompt для генерации</h4>
<blockquote>cinematic transparent PNG of modern school building at golden hour, soft sunset light fading from dark bottom to bright top, ultra-detailed architectural photograph, alpha channel, 16:9, no people, atmospheric haze</blockquote>
"""


HOMEPAGE_HERO_BADGE = """
<h4>📝 Назначение</h4>
<p>Маленький ярлычок-лейбл над основным заголовком hero. Задаёт позиционирование школы для конкретного региона.</p>

<h4>✨ Текущий референс</h4>
<ul>
  <li>Астана: «Международная школа в Астане»</li>
  <li>Актау: «Международная школа в Актау»</li>
</ul>

<h4>📐 Ограничения</h4>
<ul>
  <li>Максимум <strong>40 символов</strong> (визуально вмещается в одну строку)</li>
  <li>Без иконок, без HTML</li>
  <li>Упоминание города — обязательно (это региональный baseline)</li>
</ul>

<h4>🤖 AI-prompt</h4>
<blockquote>Напиши короткий бадж-лейбл (до 40 символов) над hero-заголовком главной школы в городе [ГОРОД]. Формат: «[Тип школы] в [Городе]». Лаконично, без воды.</blockquote>
"""


HOMEPAGE_HERO_TITLE = """
<h4>📝 Назначение</h4>
<p>Главный заголовок (h1) на hero-блоке. Эмоциональное обещание школы. Состоит из 2–4 визуальных строк, каждая обёрнута тегами — ниже подробно про каждый.</p>

<h4>🎨 Теги-обёртки (КАЖДУЮ строку обязательно)</h4>

<p><code>&lt;span class="hero-fit"&gt;...&lt;/span&gt;</code> — <strong>каждая визуальная строка заголовка</strong> должна быть в отдельной такой обёртке. На мобиле JS-библиотека <em>fitty</em> подгоняет размер шрифта так, чтобы строка вписалась в ширину контейнера; без <code>hero-fit</code> длинные слова съезжают за край или растягивают hero. На десктопе обёртка ничего визуально не делает — просто разметка.</p>

<p><code>&lt;span class="hero-break"&gt;...&lt;/span&gt;</code> — <strong>внутри</strong> <code>hero-fit</code>. Помечает фразу, которая на десктопе должна быть на отдельной строке (через CSS рендерится как принудительный перенос). <strong>На мобиле игнорируется</strong> — там <code>hero-fit</code> уже сам разбивает по строкам. Используется когда на широком экране хочется явно разнести смысловые куски, а на узком — пусть подгоняется автоматически.</p>

<p><code>&lt;span class="text-gold"&gt;...&lt;/span&gt;</code> — золотой акцент на одно-два слова. Применять <strong>не больше двух раз</strong> в заголовке — иначе акцент перестаёт работать.</p>

<h4>✨ Пример (текущий референс)</h4>
<blockquote>&lt;span class="hero-fit"&gt;Лучшее образование&lt;/span&gt;
&lt;span class="hero-fit"&gt;&lt;span class="hero-break"&gt;для будущего вашего&lt;/span&gt;&lt;/span&gt;
&lt;span class="hero-fit"&gt;ребёнка&lt;/span&gt;</blockquote>
<p>Три визуальные строки. Вторая на десктопе остаётся одной строкой за счёт <code>hero-break</code>, а на мобиле fitty подгонит её под ширину.</p>

<h4>📐 Ограничения</h4>
<ul>
  <li>Оптимум — <strong>3 строки</strong> (3 <code>hero-fit</code>). Допустимо 2. 4+ поломает hero на мобиле и десктопе.</li>
  <li>Каждая строка — <strong>12–22 символа</strong> (НЕ считая теги). Длиннее — fitty сильно зажмёт шрифт.</li>
  <li><code>hero-break</code> только <strong>внутри</strong> <code>hero-fit</code>, не наоборот.</li>
  <li>HTML рендерится через <code>|safe</code> — не вставляй внешний контент, скрипты и атрибуты вне перечисленных классов.</li>
</ul>

<h4>🤖 AI-prompt</h4>
<blockquote>Напиши emotional h1 для главной страницы международной школы. Обещание для родителя, 2–4 визуальные строки, каждая 12–22 символа.

Формат вывода — HTML по правилам:
1. Каждую визуальную строку оберни в &lt;span class="hero-fit"&gt;...&lt;/span&gt;.
2. Если внутри строки на десктопе хочется явный перенос — оберни этот кусок в &lt;span class="hero-break"&gt;...&lt;/span&gt; ВНУТРИ hero-fit (не наоборот).
3. Один-два самых важных слова оберни в &lt;span class="text-gold"&gt;...&lt;/span&gt; для акцента.
4. Никаких &lt;br&gt;, &lt;p&gt;, других классов и атрибутов.</blockquote>
"""


HOMEPAGE_HERO_SUBTITLE = """
<h4>📝 Назначение</h4>
<p>Подзаголовок (h2) под основным h1. Раскрывает позиционирование одним коротким предложением.</p>

<h4>✨ Текущий референс</h4>
<blockquote>Международное образование мирового уровня.<br>Диплом, признаваемый в 125 странах мира</blockquote>

<h4>📐 Ограничения</h4>
<ul>
  <li>1–2 строки, до <strong>120 символов</strong> суммарно</li>
  <li>Перенос строки (Enter) рендерится как <code>&lt;br class="hidden md:block"&gt;</code> — виден только на десктопе</li>
  <li>Без HTML</li>
</ul>

<h4>🤖 AI-prompt</h4>
<blockquote>Напиши h2-подзаголовок для главной школы. Раскрой ключевую выгоду одним предложением до 120 символов. Если хочется разбить на две строки — поставь явный перенос строки (Enter), это будет работать только на десктопе.</blockquote>
"""


HOMEPAGE_HERO_CTA_PRIMARY = """
<h4>📝 Назначение</h4>
<p>Основная кнопка hero — призыв к действию №1. Открывает модалку с формой заявки.</p>

<h4>✨ Текущий референс</h4>
<ul>
  <li>Текст кнопки: «Поступить сейчас»</li>
  <li>Заголовок модалки: «Поступить в [Тип программы]»</li>
</ul>

<h4>📐 Ограничения</h4>
<ul>
  <li>Текст кнопки: <strong>до 20 символов</strong>, глагол в настоящем времени</li>
  <li>Заголовок модалки: до 40 символов. Если пусто — будет использоваться текст кнопки.</li>
</ul>

<h4>🤖 AI-prompt</h4>
<blockquote>Напиши primary-CTA для hero главной школы. Текст кнопки: глагол призыва (до 20 симв). Заголовок модалки: фраза которая раскрывает что произойдёт после клика (до 40 симв).</blockquote>
"""


HOMEPAGE_HERO_CTA_SECONDARY = """
<h4>📝 Назначение</h4>
<p>Вторичная кнопка hero — мягкий призыв «узнать больше», открывает модалку обратного звонка.</p>

<h4>✨ Текущий референс</h4>
<ul>
  <li>Текст кнопки: «Получить консультацию»</li>
  <li>Заголовок модалки: «Заказать звонок»</li>
</ul>

<h4>📐 Ограничения</h4>
<ul>
  <li>Текст: <strong>до 25 символов</strong>, мягче чем primary</li>
  <li>Заголовок модалки: до 40 символов. Если пусто — fallback на текст кнопки.</li>
</ul>
"""


HOMEPAGE_ABOUT_LABEL = """
<h4>📝 Назначение</h4>
<p>Маленькая надпись-лейбл над заголовком секции «О нас».</p>

<h4>✨ Текущий референс</h4>
<blockquote>Кому подходит</blockquote>

<h4>📐 Ограничения</h4>
<ul><li>До 30 символов, без HTML</li></ul>
"""


HOMEPAGE_ABOUT_TITLE = """
<h4>📝 Назначение</h4>
<p>Заголовок секции «О нас». Многострочный, переносы рендерятся как <code>&lt;br&gt;</code>.</p>

<h4>✨ Текущий референс</h4>
<blockquote>Создаём образовательную<br>среду мирового уровня<br>в Казахстане</blockquote>

<h4>📐 Ограничения</h4>
<ul>
  <li>2–4 строки, каждая 18–28 символов</li>
  <li>Перенос строки (Enter) = <code>&lt;br&gt;</code></li>
</ul>
"""


HOMEPAGE_ABOUT_BODY = """
<h4>📝 Назначение</h4>
<p>Развёрнутое описание школы — 2–3 параграфа. Пустая строка между параграфами = новый <code>&lt;p&gt;</code>.</p>

<h4>📐 Ограничения</h4>
<ul>
  <li>200–500 символов суммарно</li>
  <li>Без HTML — только plain text с пустыми строками между параграфами</li>
  <li>Упоминание города в первом параграфе — обязательно</li>
</ul>

<h4>🤖 AI-prompt</h4>
<blockquote>Напиши описание школы [НАЗВАНИЕ] в городе [ГОРОД] для секции «О нас» главной страницы. 2–3 параграфа, 200–500 символов. Первый параграф — позиционирование (что за школа, для кого). Второй — миссия и подход. Без маркетинговых клише.</blockquote>
"""


HOMEPAGE_VIDEO = """
<h4>📝 Назначение</h4>
<p>Шоурил-видео под секцией «О нас». Без звука по умолчанию, разблокировка по клику. Демонстрирует жизнь школы (учеников, занятия, мероприятия) в концепции «space school».</p>

<h4>✨ Текущий референс</h4>
<p>20–40-секундный монтаж с воздуха + ученики + педагоги, цветокор холодный (синий/космический).</p>

<h4>📐 Технические ограничения</h4>
<ul>
  <li>Формат: <strong>MP4 (H.264)</strong>, без аудио или с приглушённым</li>
  <li>Размер: <strong>до 35 MB</strong> (client-side check + server-side validation)</li>
  <li>Разрешение: 1920×1080 (Full HD), допустимо 1280×720</li>
  <li>Длительность: 20–40 секунд</li>
  <li>FPS: 24–30</li>
  <li>Bitrate: ~3 Mbps (target для 1080p в 35 MB на 30-секундный ролик)</li>
</ul>

<h4>🤖 Автоматическая обработка</h4>
<p>Видео отдаётся как есть — без транскодирования. <strong>Перед загрузкой обязательно сожми</strong> через HandBrake (preset «Web Optimized», bitrate ~3 Mbps) или CloudConvert — иначе 1080p ролик легко выходит за 35 MB.</p>

<h4>⚠️ Если файл больше 35 MB</h4>
<p>Загрузка будет отклонена ещё в браузере с подсказкой. Сожми видео — обычно после HandBrake 20–40-секундный 1080p ролик умещается в 20–30 MB без видимой потери качества. Если нужно длиннее — уменьши разрешение до 1280×720.</p>
"""


HOMEPAGE_SEO_TITLE = """
<h4>📝 Назначение</h4>
<p>Тег <code>&lt;title&gt;</code> в head — отображается во вкладке браузера и в поисковой выдаче Google.</p>

<h4>📐 Ограничения (SEO best practices)</h4>
<ul>
  <li><strong>50–60 символов</strong> (Google обрезает после 600px ≈ 60 симв)</li>
  <li>Главное ключевое слово в первой трети</li>
  <li>Бренд в конце: «Что-то ключевое — Space School»</li>
  <li>Уникальный для каждой страницы</li>
</ul>

<h4>🔄 Fallback</h4>
<p>Если пусто — на сайте используется <code>hero_title</code> (без HTML-разметки).</p>

<h4>🤖 AI-prompt</h4>
<blockquote>Напиши SEO-title для главной страницы международной школы [НАЗВАНИЕ] в городе [ГОРОД]. 50–60 символов. Главное ключевое слово в первой трети. Закончи брендом: «— Space School». Уникально, не клише.</blockquote>
"""


HOMEPAGE_SEO_DESCRIPTION = """
<h4>📝 Назначение</h4>
<p>Тег <code>&lt;meta name="description"&gt;</code> — описание в поисковой выдаче под заголовком.</p>

<h4>📐 Ограничения</h4>
<ul>
  <li><strong>150–160 символов</strong> (Google обрезает после 920px ≈ 160 симв)</li>
  <li>2–3 ключевых слова естественно вписаны</li>
  <li>Содержит призыв или ценностное предложение</li>
  <li>Не дублирует <code>title</code></li>
</ul>

<h4>🔄 Fallback</h4>
<p>Если пусто — используется <code>hero_subtitle</code>.</p>

<h4>🤖 AI-prompt</h4>
<blockquote>Напиши SEO meta description для главной школы [НАЗВАНИЕ] в [ГОРОД]. 150–160 символов. Раскрой ценностное предложение, добавь 2–3 ключевых слова (Cambridge, IB, международная школа, [город]). Закончи мягким призывом.</blockquote>
"""


HOMEPAGE_OG_IMAGE = """
<h4>📝 Назначение</h4>
<p>Картинка, которая показывается при шеринге ссылки в социальных сетях (Telegram, WhatsApp, Facebook, LinkedIn).</p>

<h4>📐 Ограничения</h4>
<ul>
  <li>Размер: <strong>1200×630</strong> (соотношение 1.91:1)</li>
  <li>Формат: JPEG или PNG (не WebP — соцсети плохо поддерживают)</li>
  <li>Вес: <strong>до 5 MB</strong> (server-side validation отклонит больше)</li>
  <li>На картинке: логотип + название школы + краткий месседж (мобильные мессенджеры обрезают по бокам, ставь важное по центру)</li>
</ul>

<h4>🔄 Fallback</h4>
<p>Если пусто — используется <code>hero_image</code> (но он прозрачный, поэтому в соцсетях будет некрасиво — лучше загрузить отдельный OG).</p>
"""


HOMEPAGE_OG_TITLE = """
<h4>📝 Назначение</h4>
<p>Заголовок, который видит пользователь при шеринге ссылки в соцсетях. Может отличаться от SEO-title — соцсети любят более «человеческие» формулировки.</p>

<h4>📐 Ограничения</h4>
<ul>
  <li>До 60 символов</li>
  <li>Без эмодзи (рендерится не везде)</li>
</ul>

<h4>🔄 Fallback</h4>
<p>Если пусто — используется <code>seo_title</code>, либо <code>hero_title</code>.</p>
"""


HOMEPAGE_OG_DESCRIPTION = """
<h4>📝 Назначение</h4>
<p>Описание под заголовком в превью соцсетей.</p>

<h4>📐 Ограничения</h4>
<ul>
  <li>До 200 символов (мессенджеры показывают первые 60–100)</li>
  <li>Главное в первых 60 символах</li>
</ul>

<h4>🔄 Fallback</h4>
<p>Если пусто — используется <code>seo_description</code> либо <code>hero_subtitle</code>.</p>
"""


CONTACTSPAGE_INTRO_TITLE = """
<h4>📝 Назначение</h4>
<p>Главный заголовок страницы «Контакты». Видится первым.</p>

<h4>✨ Текущий референс</h4>
<blockquote>Свяжитесь с нами</blockquote>

<h4>📐 Ограничения</h4>
<ul>
  <li>До <strong>120 символов</strong>, без HTML</li>
  <li>1 строка, не вопрос (вопрос звучит мягче в подзаголовке)</li>
</ul>

<h4>🤖 AI-prompt</h4>
<blockquote>Напиши h1 для страницы «Контакты» международной школы [НАЗВАНИЕ] в городе [ГОРОД]. До 120 символов, утвердительное обещание (не вопрос).</blockquote>
"""


CONTACTSPAGE_INTRO_TEXT = """
<h4>📝 Назначение</h4>
<p>Параграф под заголовком — что школа предлагает посетителю на этой странице (адрес, телефон, формы связи).</p>

<h4>✨ Текущий референс</h4>
<blockquote>Мы готовы ответить на любые вопросы о школе, поступлении и образовательных программах. Выберите удобный способ связи.</blockquote>

<h4>📐 Ограничения</h4>
<ul>
  <li>1–2 предложения, <strong>120–250 символов</strong></li>
  <li>Без HTML, без списков</li>
  <li>Упоминание города НЕ обязательно (фильтр городов уже на странице)</li>
</ul>

<h4>🤖 AI-prompt</h4>
<blockquote>Напиши краткий intro для страницы «Контакты». 1–2 предложения (120–250 симв) — школа готова ответить, варианты связи раскрывает страница. Без воды.</blockquote>
"""


CONTACTSPAGE_OFFICE_NAME = """
<h4>📝 Назначение</h4>
<p>Название точки на overlay-карточке над картой. Если у школы один кампус — это его имя; если два — название района.</p>

<h4>✨ Текущий референс</h4>
<ul>
  <li>Астана: «Главный офис»</li>
  <li>Актау: «Школа Space School в Актау»</li>
</ul>

<h4>📐 Ограничения</h4>
<ul><li>До <strong>120 символов</strong>, 1 строка</li></ul>
"""


CONTACTSPAGE_OFFICE_ADDRESS = """
<h4>📝 Назначение</h4>
<p>Полный адрес офиса под названием. Рендерится одной строкой.</p>

<h4>📐 Ограничения</h4>
<ul>
  <li>До <strong>255 символов</strong>, без HTML</li>
  <li>Формат: «улица, дом, индекс, город»</li>
</ul>
"""


CONTACTSPAGE_OFFICE_HOURS = """
<h4>📝 Назначение</h4>
<p>Часы работы офиса под адресом. Это часы main desk, не каждого отдела отдельно — отделы задают свои часы внутри карточек.</p>

<h4>✨ Референс</h4>
<blockquote>Пн–Пт, 09:00–18:00</blockquote>

<h4>📐 Ограничения</h4>
<ul><li>До <strong>120 символов</strong>, 1 строка</li></ul>
"""


CONTACTSPAGE_MAP = """
<h4>📝 Назначение</h4>
<p>Точка маркера на интерактивной карте Leaflet (CartoDB light_nolabels). Координаты — десятичные градусы (формат WGS84), zoom — целое 1–19.</p>

<h4>📐 Технические ограничения</h4>
<ul>
  <li><strong>Широта (latitude)</strong>: число от -90 до 90, 6 знаков после точки (точность ~10 см). Пример: <code>51.093900</code></li>
  <li><strong>Долгота (longitude)</strong>: число от -180 до 180, 6 знаков. Пример: <code>71.401100</code></li>
  <li><strong>Zoom</strong>: целое 1–19. 16 — улица + здание, 13 — район, 10 — город</li>
</ul>

<h4>✨ Как найти координаты</h4>
<p>Открой Google Maps → ПКМ на здании → клик по координатам в первой строке (скопирует в clipboard в формате «51.093900, 71.401100»). Первое число — широта, второе — долгота.</p>

<h4>⚠️ Если поля пусты</h4>
<p>Карта не отрисуется, на сайте будет серая заглушка с текстом «координаты не заданы».</p>
"""


CONTACTSPAGE_SEO_TITLE = """
<h4>📝 Назначение</h4>
<p>Тег <code>&lt;title&gt;</code> в head — отображается во вкладке браузера и в поисковой выдаче Google.</p>

<h4>📐 Ограничения</h4>
<ul>
  <li><strong>50–60 символов</strong></li>
  <li>Структура: «Контакты — [Город], адрес и телефон — Space School»</li>
</ul>

<h4>🔄 Fallback</h4>
<p>Если пусто — на сайте используется <code>intro_title</code>.</p>

<h4>🤖 AI-prompt</h4>
<blockquote>Напиши SEO-title для страницы «Контакты» школы [НАЗВАНИЕ] в [ГОРОД]. 50–60 символов. Включи слова «контакты» / «адрес» / «телефон» + бренд в конце.</blockquote>
"""


CONTACTSPAGE_SEO_DESCRIPTION = """
<h4>📝 Назначение</h4>
<p>Тег <code>&lt;meta name="description"&gt;</code> — описание в поисковой выдаче под заголовком.</p>

<h4>📐 Ограничения</h4>
<ul>
  <li><strong>150–160 символов</strong></li>
  <li>Содержит: адрес/район + способы связи (телефон, email, форма)</li>
</ul>

<h4>🔄 Fallback</h4>
<p>Если пусто — используется <code>intro_text</code>.</p>

<h4>🤖 AI-prompt</h4>
<blockquote>Напиши meta description для страницы «Контакты» школы [НАЗВАНИЕ] в [ГОРОД]. 150–160 симв. Адрес/район + перечень способов связи (телефон, email, форма). Без воды.</blockquote>
"""


CONTACTSPAGE_OG_IMAGE = """
<h4>📝 Назначение</h4>
<p>Картинка, которая показывается при шеринге ссылки на страницу контактов в соцсетях/мессенджерах.</p>

<h4>📐 Ограничения</h4>
<ul>
  <li>Размер: <strong>1200×630</strong> (1.91:1)</li>
  <li>Формат: JPEG или PNG, до <strong>5 MB</strong></li>
  <li>На картинке: фото фасада / интерьера ресепшна / схема проезда</li>
</ul>

<h4>🔄 Fallback</h4>
<p>Если пусто — на сайте OG-картинки не будет (страница контактов редко шерится, это OK). На главной — отдельная og_image.</p>
"""


CONTACTSPAGE_OG_TITLE = """
<h4>📝 Назначение</h4>
<p>Заголовок в превью соцсетей при шеринге ссылки на «Контакты».</p>

<h4>📐 Ограничения</h4>
<ul><li>До 60 символов, без эмодзи</li></ul>

<h4>🔄 Fallback</h4>
<p>Если пусто — <code>seo_title</code>, затем <code>intro_title</code>.</p>
"""


CONTACTSPAGE_OG_DESCRIPTION = """
<h4>📝 Назначение</h4>
<p>Описание под заголовком в превью соцсетей.</p>

<h4>📐 Ограничения</h4>
<ul>
  <li>До 200 символов</li>
  <li>Главное в первых 60</li>
</ul>

<h4>🔄 Fallback</h4>
<p>Если пусто — <code>seo_description</code>, затем <code>intro_text</code>.</p>
"""


CONTACTSDEPARTMENT_TITLE = """
<h4>📝 Назначение</h4>
<p>Название отдела (Поступление, Партнёрство, Вакансии, Пресса, Жалобы и т.д.). Видится первым в карточке.</p>

<h4>✨ Текущий референс</h4>
<ul>
  <li>«Поступление»</li>
  <li>«Партнёрство»</li>
  <li>«Вакансии»</li>
</ul>

<h4>📐 Ограничения</h4>
<ul><li>До <strong>120 символов</strong>, 1 строка, без HTML</li></ul>
"""


CONTACTSDEPARTMENT_DESCRIPTION = """
<h4>📝 Назначение</h4>
<p>Краткое описание под названием отдела — за что отвечает и куда обращаться.</p>

<h4>✨ Референс</h4>
<blockquote>Запись на тур, тестирование, документы для поступления.</blockquote>

<h4>📐 Ограничения</h4>
<ul>
  <li>1–2 предложения, <strong>80–200 символов</strong></li>
  <li>Без HTML</li>
</ul>

<h4>🤖 AI-prompt</h4>
<blockquote>Напиши описание для отдела «[НАЗВАНИЕ]» школы. 1–2 предложения (80–200 симв) — за что отвечает, кого приглашают обращаться.</blockquote>
"""


CONTACTSDEPARTMENT_HOURS = """
<h4>📝 Назначение</h4>
<p>Часы работы конкретного отдела (если отличаются от main desk).</p>

<h4>✨ Референс</h4>
<blockquote>Пн–Пт, 09:00–18:00</blockquote>

<h4>📐 Ограничения</h4>
<ul>
  <li>До 120 символов, 1 строка</li>
  <li>Если пусто — строка с часами в карточке не покажется на сайте</li>
</ul>
"""


CONTACTSDEPARTMENT_PHONE = """
<h4>📝 Назначение</h4>
<p>Телефон для звонка в отдел. Рендерится как кликабельная <code>tel:</code>-ссылка.</p>

<h4>📐 Ограничения</h4>
<ul>
  <li>До 40 символов</li>
  <li>Формат: «+7 (000) 000-00-00» или E.164 «+70000000000»</li>
  <li>Если пусто — строка не отрисуется в карточке</li>
</ul>
"""


CONTACTSDEPARTMENT_EMAIL = """
<h4>📝 Назначение</h4>
<p>Email отдела. Рендерится как кликабельная <code>mailto:</code>-ссылка.</p>

<h4>📐 Ограничения</h4>
<ul>
  <li>Валидный email-адрес</li>
  <li>Если пусто — строка не отрисуется</li>
</ul>
"""


def _h(html, ai_processable=True):
    """Конструктор записи в FIELD_HELP.

    - `html` — текст инструкции (показывается менеджеру в раскрывающемся блоке).
    - `ai_processable` — True если AI-помощник (Gemini/GPT) может сгенерировать
      содержимое этого поля по AI-prompt из инструкции. False для бинарных полей
      (image, video) — LLM не умеет генерировать файлы; такие поля менеджер
      заполняет вручную или использует отдельный инструмент (Midjourney, HandBrake).
    """
    return {'html': html, 'ai_processable': ai_processable}


FIELD_HELP = {
    # Image / Video — AI-pipeline скипает (LLM не генерирует бинарные файлы).
    'homepage.hero_image': _h(HOMEPAGE_HERO_IMAGE, ai_processable=False),
    'homepage.video_file': _h(HOMEPAGE_VIDEO, ai_processable=False),
    'homepage.og_image': _h(HOMEPAGE_OG_IMAGE, ai_processable=False),

    # Текстовые поля — AI обрабатывает.
    'homepage.hero_badge_text': _h(HOMEPAGE_HERO_BADGE),
    'homepage.hero_title': _h(HOMEPAGE_HERO_TITLE),
    'homepage.hero_subtitle': _h(HOMEPAGE_HERO_SUBTITLE),
    'homepage.hero_cta_primary': _h(HOMEPAGE_HERO_CTA_PRIMARY),
    'homepage.hero_cta_secondary': _h(HOMEPAGE_HERO_CTA_SECONDARY),
    'homepage.about_label': _h(HOMEPAGE_ABOUT_LABEL),
    'homepage.about_title': _h(HOMEPAGE_ABOUT_TITLE),
    'homepage.about_body': _h(HOMEPAGE_ABOUT_BODY),
    'homepage.seo_title': _h(HOMEPAGE_SEO_TITLE),
    'homepage.seo_description': _h(HOMEPAGE_SEO_DESCRIPTION),
    'homepage.og_title': _h(HOMEPAGE_OG_TITLE),
    'homepage.og_description': _h(HOMEPAGE_OG_DESCRIPTION),

    # ContactsPage
    'contactspage.intro_title': _h(CONTACTSPAGE_INTRO_TITLE),
    'contactspage.intro_text': _h(CONTACTSPAGE_INTRO_TEXT),
    'contactspage.office_name': _h(CONTACTSPAGE_OFFICE_NAME),
    'contactspage.office_address': _h(CONTACTSPAGE_OFFICE_ADDRESS),
    'contactspage.office_hours': _h(CONTACTSPAGE_OFFICE_HOURS),
    'contactspage.map': _h(CONTACTSPAGE_MAP, ai_processable=False),
    'contactspage.seo_title': _h(CONTACTSPAGE_SEO_TITLE),
    'contactspage.seo_description': _h(CONTACTSPAGE_SEO_DESCRIPTION),
    'contactspage.og_image': _h(CONTACTSPAGE_OG_IMAGE, ai_processable=False),
    'contactspage.og_title': _h(CONTACTSPAGE_OG_TITLE),
    'contactspage.og_description': _h(CONTACTSPAGE_OG_DESCRIPTION),

    # ContactsDepartment (inline)
    'contactsdepartment.title': _h(CONTACTSDEPARTMENT_TITLE),
    'contactsdepartment.description': _h(CONTACTSDEPARTMENT_DESCRIPTION),
    'contactsdepartment.hours': _h(CONTACTSDEPARTMENT_HOURS),
    'contactsdepartment.phone': _h(CONTACTSDEPARTMENT_PHONE, ai_processable=False),
    'contactsdepartment.email': _h(CONTACTSDEPARTMENT_EMAIL, ai_processable=False),
}


def get_help(key):
    """Возвращает dict записи `{'html': ..., 'ai_processable': bool}` или None."""
    return FIELD_HELP.get(key)


def is_ai_processable(key):
    """Проверить, может ли AI-помощник заполнить это поле.

    Используется будущим AI-pipeline для скипа image/video — LLM не генерирует
    бинарные файлы, для них нужен Midjourney/HandBrake.
    """
    entry = FIELD_HELP.get(key)
    return bool(entry and entry.get('ai_processable', True))


def ai_processable_keys():
    """Список всех ключей, доступных AI-pipeline'у."""
    return [k for k, v in FIELD_HELP.items() if v.get('ai_processable', True)]
