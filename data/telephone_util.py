def seq_check(number):
    a = b = False
    for i in range(len(number)):
        if number[i] == '(':
            if a:
                return False
            a = True
        elif number[i] == ')':
            if not a or b:
                return False
            b = True
    return (a and b) or (not a and not b)


def country_check(number):
    c = ['+7', '+359', '+55', '+1']
    for i in range(len(c)):
        if number.startswith(c[i]):
            return True
    return False


def line_check(number):
    if number.startswith('-') or number.endswith('-'):
        return False
    for i in range(1, len(number) - 1):
        if number[i] == '-' and number[i + 1] == '-':
            return False
    return True


def good_view(number):
    if number.startswith('8'):
        b = '+7'
    else:
        b = '+'
    a = ''
    for i in range(1, len(number)):
        if number[i].isdigit():
            a += number[i]
        else:
            if number[i] not in ['-', '(', ')']:
                return False
    return b + a


def operator_check(number):
    a = int(number[2:5])
    r1 = range(910, 940)
    r2 = range(902, 907)
    r3 = range(960, 970)
    r4 = range(980, 990)
    if a in r1 or a in r2 or a in r3 or a in r4:
        return True


def starts_check(number):
    if number.startswith('+') or number.startswith('8'):
        return True
    return False


def check_number(number):
    try:
        number = ''.join(number.split())
        if not seq_check(number):
            return 'неверный формат'
        if not line_check(number):
            return 'неверный формат'
        if not starts_check(number):
            return 'неверный формат'
        a = good_view(number)
        if a:
            if len(a) != 12:
                return 'неверное количество цифр'
            if not country_check(a):
                return 'не определяется код страны'
            if a[:2] == '+7':
                if not operator_check(a):
                    return 'не определяется оператор сотовой связи'
            return a
        else:
            return 'неверный формат'
    except Exception:
        return 'неверный формат'
