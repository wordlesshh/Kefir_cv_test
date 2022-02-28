import dateparser
from dateparser.search import search_dates


def find_date(str_date):
    year_flag = False
    for index in range(4):
        if not str_date[index].isdecimal():
            year_flag = False
            break
        elif index > 1:
            year_flag = True
    if year_flag:
        date = dateparser.parse(str_date, settings={'DATE_ORDER': 'YMD'})
    else:
        date = dateparser.parse(str_date, settings={'DATE_ORDER': 'DMY'})
    if not date:
        day_list = {
            'перво': 1,
            'второ': 2,
            'третье': 3,
            'четвёрто': 4,
            'пято': 5,
            'шесто': 6,
            'седьмо': 7,
            'восьмо': 8,
            'девято': 9,
            'десято': 10,
            'одиннадцато': 11,
            'двенадцато': 12,
            'тринадцато': 13,
            'четырнадцато': 14,
            'пятнадцато': 15,
            'шестнадцато': 16,
            'семнадцато': 17,
            'восемнадцато': 18,
            'девятнадцато': 19,
            'двадцато': 20,
            'двадцать перво': 21,
            'двадцать второ': 22,
            'двадцать третье': 23,
            'двадацать четвёрто': 24,
            'двадцать пято': 25,
            'двадцать шесто': 26,
            'двадцать седьмо': 27,
            'двадцать восьмо': 28,
            'двадцать девято': 29,
            'тридцато': 30,
            'тридцать перво': 31,
        }

        date_raw = search_dates(str_date)
        date = None
        check_num = is_number(str_date)
        if date_raw and not check_num:
            for k, v in day_list.items():
                if k in str_date:
                    digit = v
                    date_raw = str(digit) + date_raw[0][0]
                    date = dateparser.parse(date_raw, settings={'DATE_ORDER': 'DMY'})
        elif date_raw and check_num:
            date_raw = check_num + date_raw[0][0]
            date = dateparser.parse(date_raw, settings={'DATE_ORDER': 'DMY'})
    return date


def is_number(txt: str):
    string = ''
    for char in txt:
        try:
            string += str(int(char))
        except Exception:
            pass
    if string == '':
        return None
    return string
