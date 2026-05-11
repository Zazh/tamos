"""
RU-контент для ProgramPage обоих регионов. Текст универсальный, в hero-badge
подставляется название города. Идемпотентно: повторный прогон обновляет
существующие записи (update_or_create по region и (page, order) для inline'ов).
"""
from django.db import migrations


# --- SVG-иконки взяты 1-в-1 из spaceschool/pages/landing.html ---
ICON_AUDIENCE_UNIVERSITY = (
    '<svg class="h-9" viewBox="0 0 37 32" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<path d="M25.9089 14.8703L29.4427 14.1878L26.8876 4.65381L11.243 10.4079L13.101 17.3419L13.5432 17.2569" stroke="currentColor" stroke-width="2.48939" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path fill-rule="evenodd" clip-rule="evenodd" d="M11.4332 11.1174L1.24493 14.6991L2.25853 18.482L12.8265 16.3176L11.4332 11.1174Z" stroke="currentColor" stroke-width="2.48939" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path fill-rule="evenodd" clip-rule="evenodd" d="M32.8177 2.51425C32.573 1.60085 31.6349 1.0592 30.7222 1.30389C29.864 1.53405 28.8185 1.81432 27.9602 2.04375C27.0476 2.28844 26.5059 3.22652 26.7499 4.13992C27.4651 6.8075 28.8656 12.0345 29.5801 14.7021C29.8248 15.6155 30.7636 16.1571 31.6763 15.9124C32.5345 15.6823 33.58 15.402 34.4375 15.1726C35.3509 14.9279 35.8926 13.9891 35.6479 13.0764C34.9327 10.4088 33.5328 5.18183 32.8177 2.51425Z" stroke="currentColor" stroke-width="2.48939" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path fill-rule="evenodd" clip-rule="evenodd" d="M16.5307 12.8061C18.5637 12.2609 20.6562 13.4698 21.2015 15.5028C21.7461 17.5358 20.5379 19.6283 18.5049 20.1736C16.4712 20.7181 14.3786 19.51 13.8341 17.477C13.2888 15.444 14.497 13.3507 16.5307 12.8061Z" stroke="currentColor" stroke-width="2.48939" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M18.2812 20.3355C17.0388 22.4883 14.1636 27.467 12.9213 29.6198C12.7645 29.8906 12.5074 30.0881 12.2047 30.1694C11.9026 30.25 11.581 30.2079 11.3094 30.0511C10.6995 29.6989 9.92626 29.2524 9.31564 28.9002C9.04481 28.7434 8.84732 28.4864 8.766 28.1836C8.68541 27.8816 8.72752 27.5599 8.88435 27.2891L14.1193 18.2212" stroke="currentColor" stroke-width="2.48939" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M21.0271 17.978C21.0329 17.9867 21.038 17.9962 21.0438 18.0049" stroke="currentColor" stroke-width="2.48939" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M21.0453 18.0049C22.2876 20.1577 25.1621 25.1363 26.4052 27.2891C26.5613 27.56 26.6041 27.8816 26.5228 28.1837C26.4422 28.4864 26.244 28.7435 25.9732 28.9003C25.3625 29.2524 24.59 29.699 23.9794 30.0511C23.7085 30.208 23.3862 30.2501 23.0841 30.1695C22.7821 30.0881 22.5243 29.8907 22.3682 29.6198C21.6581 28.3899 20.4144 26.2363 19.2476 24.215" stroke="currentColor" stroke-width="2.48939" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '</svg>'
)

ICON_AUDIENCE_CIS = (
    '<svg class="h-9" viewBox="0 0 35 36" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<path fill-rule="evenodd" clip-rule="evenodd" d="M23.1346 2.17704C24.6857 0.62596 28.0819 1.50266 30.7135 4.13426C33.3458 6.76662 34.2225 10.1628 32.6715 11.7139C31.1196 13.2649 27.7235 12.3882 25.0919 9.75663C22.4603 7.12427 21.5828 3.72811 23.1346 2.17704Z" stroke="currentColor" stroke-width="2.82352" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M24.2467 8.81326C23.2594 7.0682 24.3089 5.92554 24.3089 5.92554C25.1424 5.09204 26.9678 5.56334 28.3817 6.97727C28.8295 7.42509 29.1826 7.91383 29.4296 8.39878" stroke="currentColor" stroke-width="2.82352" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M23.1357 2.17688C23.1357 2.17688 16.9223 9.81633 13.0919 14.5256" stroke="currentColor" stroke-width="2.82352" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M7.7796 20.6603C6.19821 22.3402 4.14173 24.5255 2.63763 26.1235C1.40783 27.4299 1.06988 29.3409 1.77609 30.9897C2.17845 31.9293 2.90208 32.6953 3.8159 33.1515C3.91062 33.1992 4.00382 33.2455 4.09475 33.2909C5.93225 34.2093 8.15165 33.8494 9.60422 32.3968C10.9545 31.0465 12.6359 29.3643 14.0241 27.9762" stroke="currentColor" stroke-width="2.82352" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M20.6544 21.9416C25.3334 17.9688 32.5008 11.8834 32.5008 11.8834" stroke="currentColor" stroke-width="2.82352" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path fill-rule="evenodd" clip-rule="evenodd" d="M14.8575 24.1625C15.8448 23.1752 17.4474 23.1752 18.434 24.1625C19.4213 25.1491 19.4213 26.7517 18.434 27.739C17.4474 28.7256 15.8448 28.7256 14.8575 27.739C13.8709 26.7517 13.8709 25.1491 14.8575 24.1625Z" stroke="currentColor" stroke-width="2.82352" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M15.667 28.2831C15.5291 28.3111 15.3874 28.3225 15.2442 28.3179C14.7365 28.3013 14.2591 28.074 13.925 27.6921C12.2807 25.8114 9.47329 22.5993 7.96767 20.8763C7.37664 20.2004 7.36224 19.1948 7.93433 18.5023C8.2306 18.1431 8.56249 17.7415 8.88604 17.3498C9.2543 16.9042 9.81048 16.658 10.3879 16.686C10.9653 16.7133 11.4957 17.0118 11.8192 17.4907L13.8121 20.439" stroke="currentColor" stroke-width="2.82352" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M19.0881 25.2961C19.0881 25.2961 20.9794 28.1316 22.3805 30.232C22.7434 30.7761 23.3314 31.1284 23.9823 31.1928C24.6332 31.2572 25.2788 31.0269 25.741 30.5639C26.3358 29.9698 26.8405 29.4652 26.8405 29.4652" stroke="currentColor" stroke-width="2.82352" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M17.6011 28.5725L18.1967 34.5328" stroke="currentColor" stroke-width="2.82352" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '</svg>'
)

ICON_AUDIENCE_SCIENCE = (
    '<svg class="h-9" viewBox="0 0 32 39" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<path fill-rule="evenodd" clip-rule="evenodd" d="M23.0955 6.9973C27.7433 11.6451 27.7433 19.1928 23.0955 23.8406C18.4478 28.4884 10.9 28.4884 6.25224 23.8406C1.60448 19.1928 1.60448 11.6451 6.25224 6.9973C10.9 2.34953 18.4478 2.34953 23.0955 6.9973Z" stroke="currentColor" stroke-width="2.55208" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M28.8173 1.276L25.7274 4.36583C31.8282 10.4658 31.8282 20.3717 25.7274 26.4717C19.6274 32.5725 9.72153 32.5725 3.62153 26.4717L1.27606 28.8172" stroke="currentColor" stroke-width="2.55208" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M12.8136 31.0503V32.7698C12.8136 34.0523 12.3044 35.2812 11.3978 36.1878C10.9557 36.63 10.5805 37.0051 10.5805 37.0051" stroke="currentColor" stroke-width="2.55208" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M16.5353 31.0503V32.7698C16.5353 34.0523 17.0445 35.2812 17.9511 36.1878C18.3933 36.63 18.7684 37.0051 18.7684 37.0051" stroke="currentColor" stroke-width="2.55208" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M26.5847 5.29333L26.1356 5.74245" stroke="currentColor" stroke-width="2.55208" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M7.19188 24.6853L4.5509 27.3263" stroke="currentColor" stroke-width="2.55208" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M3.88129 10.9528C5.79503 11.6703 7.36637 13.0853 8.28044 14.9135C8.57074 15.4926 8.8521 16.0561 9.06797 16.4878C9.31807 16.9873 9.80562 17.323 10.3602 17.3795C10.3646 17.3393 10.3646 17.3393 10.3646 17.3393C11.4752 17.4964 12.3938 18.2854 12.7161 19.3603C13.0384 20.4351 12.7056 21.5993 11.8645 22.3414C11.3345 22.7873 10.7725 23.1379 10.2083 23.2346" stroke="currentColor" stroke-width="2.55208" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M20.63 9.46399V11.2579C20.63 11.5355 20.5035 11.7983 20.2869 11.9717H20.2861C19.4145 12.6692 19.186 13.8996 19.748 14.8643C20.0732 15.4218 20.4276 16.0285 20.7216 16.5331C21.1354 17.2418 21.8426 17.7301 22.6517 17.8648C23.9722 18.0851 25.8405 18.3963 25.8405 18.3963" stroke="currentColor" stroke-width="2.55208" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '</svg>'
)

ICON_AUDIENCE_AMBITION = (
    '<svg class="h-9" viewBox="0 0 27 40" fill="none" xmlns="http://www.w3.org/2000/svg">'
    '<path d="M16.2214 29.4671C15.013 29.7692 13.1128 30.244 11.5163 30.6436C10.8238 30.8163 10.0902 30.6611 9.5278 30.222C8.96543 29.7821 8.63668 29.1086 8.63668 28.3948V28.3918C8.63592 25.9658 7.5538 23.6661 5.68329 22.1205C3.00309 20.0004 1.30457 16.7144 1.30457 13.0351C1.30457 6.56058 6.56071 1.30444 13.0352 1.30444C19.5097 1.30444 24.7658 6.56058 24.7658 13.0351C24.7658 16.8141 22.9744 20.1785 20.1953 22.3244C19.3111 23.0192 18.617 23.9027 18.1521 24.8951" stroke="currentColor" stroke-width="2.6091" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M17.508 32.6138L10.7983 34.4774" stroke="currentColor" stroke-width="2.6091" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M17.508 35.9683L10.7983 37.8319" stroke="currentColor" stroke-width="2.6091" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '<path d="M13.7964 24.8952C13.7964 24.8952 12.4259 23.9363 11.33 23.1692C11.0835 22.9957 10.9571 22.6967 11.0066 22.3991C11.0553 22.1016 11.2707 21.8588 11.5606 21.7743C12.4076 21.527 13.5019 21.2082 14.5924 20.8893C14.9607 20.782 15.1974 20.4243 15.1517 20.0439C15.1061 19.6634 14.7918 19.3711 14.409 19.3536C12.5065 19.2676 10.7524 19.1877 10.7524 19.1877" stroke="currentColor" stroke-width="2.6091" stroke-miterlimit="2" stroke-linecap="round" stroke-linejoin="round"/>'
    '</svg>'
)

ICON_CERT_ACCREDITED = (
    '<svg class="block w-full h-full" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M4 14 16 5l12 9"/>'
    '<path d="M3 14h26"/>'
    '<path d="M6 14v10M12 14v10M20 14v10M26 14v10"/>'
    '<path d="M4 28h24"/>'
    '</svg>'
)

ICON_CERT_COUNTRIES = (
    '<svg class="block w-full h-full" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M20 3H8a2 2 0 0 0-2 2v22a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9l-6-6z"/>'
    '<path d="M20 3v6h6"/>'
    '<path d="M12 17h8M12 22h8"/>'
    '</svg>'
)

ICON_CERT_KZ = (
    '<svg class="block w-full h-full" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<path d="M16 4 2 12l14 8 14-8L16 4z"/>'
    '<path d="M7 15v7c0 2.5 4 4 9 4s9-1.5 9-4v-7"/>'
    '<path d="M28 12v8"/>'
    '</svg>'
)

ICON_CERT_GLOBAL = (
    '<svg class="block w-full h-full" viewBox="0 0 32 32" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
    '<circle cx="16" cy="16" r="12"/>'
    '<path d="M4 16h24"/>'
    '<path d="M16 4a18 18 0 0 1 0 24M16 4a18 18 0 0 0 0 24"/>'
    '</svg>'
)


# --- ProgramPage поля по регионам ---
BASE_PAGE_FIELDS = {
    # Hero
    'hero_title_ru': 'Школа для детей\nкоторые поступят\nв TOP-100 вузов',
    'hero_subtitle_ru': (
        'Space School — международная школа нового поколения, где дети учатся '
        'думать глобально, готовятся к поступлению в ведущие университеты мира '
        'и получают двойной сертификат с правом сдачи SAT'
    ),
    'hero_cta_primary_text_ru': 'Поступить сейчас',
    'hero_cta_secondary_text_ru': 'Получить консультацию',

    # Audience
    'audience_label_ru': 'Кому подходит',
    'audience_title_ru': 'Ваш ребёнок — наш ученик, если он...',
    'audience_subtitle_ru': (
        'Space School создана для амбициозных детей, готовых выйти за рамки '
        'стандартной программы.'
    ),

    # Benefits
    'benefits_label_ru': 'Результаты обучения',
    'benefits_title_ru': 'Что получает ваш ребёнок',
    'benefits_subtitle_ru': (
        'Измеримые результаты, которые открывают двери в лучшие университеты мира.'
    ),

    # Programs
    'programs_label_ru': 'Программы обучения',
    'programs_title_ru': 'Две сильные программы — один результат',
    'programs_subtitle_ru': (
        'Выберите траекторию, которая подходит вашему ребёнку. Обе ведут '
        'к международному аттестату и лучшим университетам мира.'
    ),
    'programs_cta_text_ru': 'Получить консультацию',

    # Team
    'team_label_ru': 'Подход и забота',
    'team_title_ru': 'Команда профессионалов, которая заботится о вашем ребёнке',
    'team_subtitle_ru': (
        'Каждый педагог — практик с опытом в международных школах и университетах. '
        'Мы отвечаем за развитие каждого ученика'
    ),

    # Certificate
    'certificate_label_ru': 'Двойной сертификат',
    'certificate_title_ru': 'Аттестат, который открывает мир',
    'certificate_subtitle_ru': (
        'Выпускники Space School получают двойной сертификат: Казахстанский '
        'аттестат + международный Cambridge-документ. Без IELTS и SAT — '
        'поступление наравне с носителями языка.'
    ),
    'certificate_cta_text_ru': 'Посмотреть образец сертификата',

    # Activities
    'activities_label_ru': 'Внеклассные занятия',
    'activities_title_ru': 'После уроков — жизнь не останавливается',
    'activities_subtitle_ru': (
        'Секции, кружки и события, которые развивают личность, а не только оценки'
    ),
    'activities_cta_text_ru': 'Смотреть все активности',

    # Stats
    'stats_label_ru': 'О нас',
    'stats_title_ru': 'Space School в цифрах',
    'stats_intro_text_ru': (
        'Space School основана в 2013 году с миссией: дать каждому ребёнку '
        'в Казахстане образование мирового уровня. Мы объединяем лучшие практики '
        'финской, британской и казахстанской систем образования — в одной школе.'
    ),

    # FAQ
    'faq_label_ru': 'Частые вопросы',
    'faq_title_ru': 'FAQ',
}

REGION_PAGE_FIELDS = {
    'astana': {'hero_badge_text_ru': 'Международная школа в Астане'},
    'aktau':  {'hero_badge_text_ru': 'Международная школа в Актау'},
}


# --- Inline-данные (общие для всех регионов) ---
AUDIENCE_ITEMS = [
    (10, ICON_AUDIENCE_UNIVERSITY,
     'Планирует поступать в зарубежный ВУЗ',
     'Нужна глубокая подготовка по физике, математике и международным языкам — '
     'именно это мы даём с первых классов.'),
    (20, ICON_AUDIENCE_CIS,
     'Хочет международный аттестат CIS',
     'Наши выпускники получают аттестат, признанный международными '
     'университетами по всему миру.'),
    (30, ICON_AUDIENCE_SCIENCE,
     'Увлекается космосом и наукой',
     'Астрофизика, робототехника, программирование — мы строим образование '
     'вокруг страсти к исследованиям.'),
    (40, ICON_AUDIENCE_AMBITION,
     'Хочет большего, чем обычная школа',
     'Если стандартная программа скучна — Space School откроет настоящий '
     'потенциал вашего ребёнка.'),
]


BENEFIT_ITEMS = [
    (10, 'Физ-мат уклон мирового уровня',
     'Углублённая математика, физика и информатика — программа сопоставима '
     'с лучшими израильскими школами.'),
    (20, 'Международные языки',
     'Казахский, русский, английский — полноценное трёхъязычное образование '
     'с носителями языка.'),
    (30, 'Готовность к SAT и международным экзаменам',
     'Системная подготовка к экзаменам, необходимым для поступления '
     'в университеты США, UK, EU.'),
    (40, 'Космическая тема как контекст',
     'Астрофизика, проектирование, исследования — всё это не клуб, '
     'а часть основной программы.'),
]


VARIANT_CARDS = [
    {
        'order': 10,
        'badge_text_ru': '1–4 класс',
        'badge_style': 'gold',
        'title_ru': 'Начальная школа',
        'tags_ru': 'Cambridge Primary\nLaverick\nФинская методика',
        'features_ru': (
            'Развитие через игру и исследование\n'
            'Билингвальное обучение\n'
            'Математика, грамотность, естественные науки\n'
            'Soft skills: критическое мышление и EQ'
        ),
        'footer_label_ru': 'Выпускник получает:',
        'footer_value_ru': 'Cambridge Primary Certificate',
    },
    {
        'order': 20,
        'badge_text_ru': '5–11 класс',
        'badge_style': 'secondary',
        'title_ru': 'Средняя и старшая школа',
        'tags_ru': 'Cambridge Lower Secondary\nIGCSE\nAS-Level\nA-Level',
        'features_ru': (
            'Cambridge Lower Secondary (5–6 класс)\n'
            'IGCSE (9–10 класс)\n'
            'AS-Level и A-Level (11–12 класс)\n'
            'Подготовка к поступлению в лучшие университеты мира'
        ),
        'footer_label_ru': 'Выпускник получает:',
        'footer_value_ru': 'Cambridge A-Level + Аттестат КЗ',
    },
]


TEAM_MEMBERS = [
    (10, 'Айгерим Нурланова', 'Основатель и директор',
     'PhD в педагогике · 20 лет в международном образовании',
     '«Каждый ребёнок рождён исследователем. Моя задача — создать среду, '
     'где этот огонь не гаснет, а разгорается сильнее с каждым годом.»'),
    (20, 'Айгерим Нурланова', 'Основатель и директор',
     'PhD в педагогике · 20 лет в международном образовании',
     '«Каждый ребёнок рождён исследователем. Моя задача — создать среду, '
     'где этот огонь не гаснет, а разгорается сильнее с каждым годом.»'),
    (30, 'Айгерим Нурланова', 'Основатель и директор',
     'PhD в педагогике · 20 лет в международном образовании',
     '«Каждый ребёнок рождён исследователем. Моя задача — создать среду, '
     'где этот огонь не гаснет, а разгорается сильнее с каждым годом.»'),
    (40, 'Айгерим Нурланова', 'Основатель и директор',
     'PhD в педагогике · 20 лет в международном образовании',
     '«Каждый ребёнок рождён исследователем. Моя задача — создать среду, '
     'где этот огонь не гаснет, а разгорается сильнее с каждым годом.»'),
]


CERTIFICATE_FEATURES = [
    (10, ICON_CERT_ACCREDITED, 'Аккредитован: Cambridge Lower Secondary, IGCSE, A-Level'),
    (20, ICON_CERT_COUNTRIES,  'Поступление в 160+ стран без вступительных экзаменов'),
    (30, ICON_CERT_KZ,         'Признаётся казахстанскими вузами как государственный аттестат'),
    (40, ICON_CERT_GLOBAL,     'Наравне с носителями языка — без AP или Foundation курсов'),
]


ACTIVITY_ITEMS = [
    (10, '09:00 – 10:30', 'Робототехника', 'Технологии', 'indigo',
     'Конструируем роботов и пишем программы. Учимся решать инженерные задачи '
     'и работать в команде.'),
    (20, '10:30 – 12:00', 'Шахматный клуб', 'Наука', 'red',
     'Развиваем стратегическое мышление и концентрацию через игру в шахматы. '
     'Подходит как новичкам, так и опытным игрокам.'),
    (30, '10:00 – 13:30', 'Дебаты на английском', 'Риторика', 'green',
     'Учимся аргументировать позицию, слушать оппонента и выступать публично — '
     'на английском языке.'),
    (40, '13:30 – 15:00', 'Английский клуб', 'Спорт', 'orange',
     'Разговорная практика с носителями языка в неформальной обстановке. '
     'Игры, дискуссии и проекты на английском.'),
]


STATS = [
    (10, '94%',  'Поступают в ТОП-вузы'),
    (20, '3',    'Языка обучения'),
    (30, '12',   'Лет опыта'),
    (40, '100%', 'Получают аттестат CIS'),
]


FAQ_ITEMS = [
    (10, 'Что такое Space School?',
     'Space School — это международная школа в Казахстане, где дети '
     'получают глубокую подготовку по физике, математике и языкам и '
     'двойной аттестат (КЗ + Cambridge).'),
    (20, 'Для какого возраста подходят программы?',
     'Наши программы рассчитаны на детей с 1 по 11 класс — от 6 до 17 лет. '
     'Программа адаптируется под возраст и уровень подготовки каждого ученика.'),
    (30, 'Как проходят занятия?',
     'Занятия проходят в формате интерактивных уроков с практическими заданиями. '
     'Каждый урок включает теоретическую часть и hands-on проект.'),
    (40, 'Нужна ли предварительная подготовка?',
     'Нет, предварительная подготовка не требуется. Мы начинаем с основ '
     'и постепенно усложняем программу с учётом возможностей ребёнка.'),
]


def _with_base(ru_fields: dict) -> dict:
    """Скопировать `*_ru` значения в base-колонки (modeltranslation fallback)."""
    base = {key.removesuffix('_ru'): value
            for key, value in ru_fields.items()
            if key.endswith('_ru')}
    return {**base, **ru_fields}


def seed_program_pages(apps, schema_editor):
    Region = apps.get_model('regions', 'Region')
    ProgramPage = apps.get_model('programs', 'ProgramPage')
    ProgramAudienceItem = apps.get_model('programs', 'ProgramAudienceItem')
    ProgramBenefitItem = apps.get_model('programs', 'ProgramBenefitItem')
    ProgramVariantCard = apps.get_model('programs', 'ProgramVariantCard')
    ProgramTeamMember = apps.get_model('programs', 'ProgramTeamMember')
    ProgramCertificateFeature = apps.get_model('programs', 'ProgramCertificateFeature')
    ProgramActivityItem = apps.get_model('programs', 'ProgramActivityItem')
    ProgramStat = apps.get_model('programs', 'ProgramStat')
    ProgramFaqItem = apps.get_model('programs', 'ProgramFaqItem')

    for region_slug, region_fields in REGION_PAGE_FIELDS.items():
        try:
            region = Region.objects.get(slug=region_slug)
        except Region.DoesNotExist:
            continue

        defaults = _with_base({**BASE_PAGE_FIELDS, **region_fields})
        page, _ = ProgramPage.objects.update_or_create(
            region=region,
            defaults=defaults,
        )

        for order, icon_svg, title_ru, description_ru in AUDIENCE_ITEMS:
            ProgramAudienceItem.objects.update_or_create(
                program_page=page, order=order,
                defaults={
                    **_with_base({'title_ru': title_ru, 'description_ru': description_ru}),
                    'icon_svg': icon_svg,
                },
            )

        for order, title_ru, description_ru in BENEFIT_ITEMS:
            ProgramBenefitItem.objects.update_or_create(
                program_page=page, order=order,
                defaults=_with_base({'title_ru': title_ru, 'description_ru': description_ru}),
            )

        for card in VARIANT_CARDS:
            ProgramVariantCard.objects.update_or_create(
                program_page=page, order=card['order'],
                defaults={
                    **_with_base({k: v for k, v in card.items() if k.endswith('_ru')}),
                    'badge_style': card['badge_style'],
                },
            )

        for order, name, role, meta, quote in TEAM_MEMBERS:
            ProgramTeamMember.objects.update_or_create(
                program_page=page, order=order,
                defaults=_with_base({
                    'name_ru': name, 'role_ru': role,
                    'meta_ru': meta, 'quote_ru': quote,
                }),
            )

        for order, icon_svg, title_ru in CERTIFICATE_FEATURES:
            ProgramCertificateFeature.objects.update_or_create(
                program_page=page, order=order,
                defaults={
                    **_with_base({'title_ru': title_ru}),
                    'icon_svg': icon_svg,
                },
            )

        for order, time_label, title, category, color, description in ACTIVITY_ITEMS:
            ProgramActivityItem.objects.update_or_create(
                program_page=page, order=order,
                defaults={
                    **_with_base({
                        'time_label_ru': time_label,
                        'title_ru': title,
                        'category_ru': category,
                        'description_ru': description,
                    }),
                    'category_color': color,
                },
            )

        for order, value, label in STATS:
            ProgramStat.objects.update_or_create(
                program_page=page, order=order,
                defaults=_with_base({'value_ru': value, 'label_ru': label}),
            )

        for order, question, answer in FAQ_ITEMS:
            ProgramFaqItem.objects.update_or_create(
                program_page=page, order=order,
                defaults=_with_base({'question_ru': question, 'answer_ru': answer}),
            )


def unseed_program_pages(apps, schema_editor):
    ProgramPage = apps.get_model('programs', 'ProgramPage')
    ProgramPage.objects.filter(
        region__slug__in=list(REGION_PAGE_FIELDS.keys())
    ).delete()  # CASCADE снесёт inline'ы


class Migration(migrations.Migration):
    dependencies = [
        ('programs', '0001_initial'),
        ('regions', '0005_seed_inactive_cities'),
    ]
    operations = [
        migrations.RunPython(seed_program_pages, unseed_program_pages),
    ]
