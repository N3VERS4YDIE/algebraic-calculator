import re

DECIMALS = 2
POLY_OPERATORS = ('+', '-', '/')


def evaluate(exp: str, format_result=True) -> str:
    exp = exp.replace(' ', '')
    exp = simplify(exp)
    exp = mul(exp)
    exp = div(exp)
    exp = sum(exp)
    exp = clean(exp)
    return format(exp) if format_result else exp


def prepare(poly: str) -> str:
    poly = poly.replace('--', '+')
    poly = poly.replace('++', '+')
    poly = poly.replace('+-', '-')

    poly = poly[:1] + re.sub(r'(?<!\^)-', '+-', poly[1:])
    return poly


def clean(exp: str) -> str:
    exp = exp.replace(' ', '')
    exp = exp.replace('+-', '-')
    exp = re.sub(r'[\(\)]', '', exp)
    if exp.startswith('++'):
        exp = exp[2:]
    if exp.startswith('+'):
        exp = exp[1:]
    return exp


def format(exp: str) -> str:
    if '^0' in exp:
        exp = re.sub(r'[a-zA-Z]\^0', '', exp)

    degrees_map = {'-': '⁻' , '0': '⁰', '1': '¹', '2': '²', '3': '³',
                   '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'}
    exp = re.sub(r'\^(-?\d+)', lambda match: ''.join(degrees_map[n] for n in match.group(1)), exp)
    exp = exp.replace('+', ' + ')
    if exp == '':
        return '0'
    exp = exp[0] + re.sub(r'(?<!\^)-', ' - ', exp[1:])
    return exp

# region individual polynomials


def internal_simplify(poly: str) -> str:
    poly = prepare(poly)
    if '*' in poly:
        poly = internal_mul(poly)
    if '+' in poly:
        poly = internal_sum(poly)
    if poly.startswith('+'):
        poly = poly[1:]
    return poly if poly else '0'


def internal_mul(poly: str) -> str:
    result = ''

    while True:
        mul_index = poly.index('*') if '*' in poly else -1

        if mul_index == -1:
            break

        left = poly[:mul_index]
        right = poly[mul_index + 1:]

        left_index = left.rindex('+') if '+' in left else -1
        right_index = right.index('+') if '+' in right else -1

        if left_index != -1:
            left = left[left_index + 1:]
        if right_index != -1:
            right = right[:right_index]

        result += mul_terms(left, right)
        poly = poly.replace(left + '*' + right, '', 1)

    result = poly + result
    result = result.replace('++', '+')
    return result


def internal_div(poly: str) -> str:
    result = ''

    while True:
        div_index = poly.index('/') if '/' in poly else -1

        if div_index == -1:
            break

        left = poly[:div_index]
        right = poly[div_index + 1:]

        left_index = left.rindex('+') if '+' in left else -1
        right_index = right.index('+') if '+' in right else -1

        if left_index != -1:
            left = left[left_index + 1:]
        if right_index != -1:
            right = right[:right_index]

        result += div_terms(left, right)
        poly = poly.replace(left + '/' + right, '', 1)

    result = poly + result
    result = result.replace('++', '+')
    return result


def mul_terms(term1: str, term2: str) -> str:
    coefficient1, var1 = split_term(term1)
    coefficient2, var2 = split_term(term2)

    coefficient = coefficient1 * coefficient2

    degrees_map = {}
    variables = var1 + var2
    for i, char in enumerate(variables):
        if char.isalpha():
            if i + 2 <= len(variables) and variables[i + 1] == '^':
                next_var_index = i + 2
                degree = ''
                while next_var_index < len(variables) and (num := variables[next_var_index]).isdigit() or num in ('-', '+'):
                    degree += num
                    next_var_index += 1
                degree = int(degree)
                if char not in degrees_map:
                    degrees_map[char] = degree
                else:
                    degrees_map[char] += degree
            else:
                if char not in degrees_map:
                    degrees_map[char] = 1
                else:
                    degrees_map[char] += 1

    variables = ''
    for v in degrees_map:
        variables += v
        if degrees_map[v] != 1:
            variables += f'^{degrees_map[v]}'

    return to_term(coefficient, variables)


def div_terms(numerator: str, denominator: str) -> str:
    coefficient1, var1 = split_term(numerator)
    coefficient2, var2 = split_term(denominator)

    coefficient = coefficient1 / coefficient2
    numerator = to_term(coefficient, var1)

    inv_var2 = ''
    while True:
        next_var_index = -1
        for i, char in enumerate(var2[1:], 1):
            if char.isalpha():
                next_var_index = i
                break
        degree_index = var2.index('^') if '^' in var2 else -1
        if degree_index > next_var_index and next_var_index > -1:
            degree_index = -1
        if next_var_index == -1:
            inv_degree = to_num(var2[degree_index + 1:]) * -1 if degree_index > -1 else -1
            inv_var2 += f'{var2[:degree_index] if degree_index > -1 else var2}^{inv_degree}' if var2 else ''
            break
        inv_degree = to_num(var2[degree_index + 1:next_var_index]) * -1 if degree_index > -1 else -1
        inv_var2 += f'{var2[:degree_index] if degree_index > -1 else var2[:next_var_index]}^{inv_degree}' if var2 else ''
        var2 = var2[next_var_index:]

    denominator = to_term(1, inv_var2)
    return mul_terms(numerator, denominator)


def sum_terms(terms: list[str]) -> dict[str, float | int]:
    variables = {}
    for term in terms:
        coefficient, var = split_term(term)
        if var not in variables:
            variables[var] = coefficient
        else:
            variables[var] += coefficient
    return variables


def internal_sum(poly: str) -> str:
    result = ''
    terms = poly.split('+')
    terms = [term for term in terms if term]
    if len(terms) < 2:
        return poly

    variables = sum_terms(terms)

    for var in variables:
        coefficient = variables[var]
        term = to_term(coefficient, var)
        result += term

    return result


def split_term(term: str) -> tuple[float | int, str]:
    var_index = -1
    for i, char in enumerate(term):
        if char.isalpha():
            var_index = i
            break
    if var_index == -1:
        return to_num(term), ''
    coefficient = to_num(term[:var_index]) if term else 0
    var = term[var_index:]
    return coefficient, var


def to_num(term: str) -> float | int:
    match term:
        case '':
            return 1
        case '-':
            return -1
        case '+':
            return 1
        case _:
            num = float(term)
            return int(num) if num % 1 == 0 else num


def to_term(coefficient: float | int, var: str):
    coefficient = round(coefficient, DECIMALS)
    if var == '':
        sign = '+' if coefficient > 0 else ''
        return f'{sign}{coefficient}'

    match coefficient:
        case 0:
            return ''
        case 1:
            return f'+{var}'
        case -1:
            return f'-{var}'
        case _:
            sign = '+' if coefficient > 0 else ''
            return f'{sign}{coefficient}{var}'
# endregion

# region multiple polynomials


def simplify(exp: str) -> str:
    if not exp.__contains__('('):
        exp = internal_simplify(exp)
        return exp

    result = ''

    while True:
        open_index = exp.index('(') if '(' in exp else -1
        close_index = exp.index(')') if ')' in exp else -1
        if open_index == -1 or close_index == -1:
            break

        poly = exp[open_index + 1:close_index]
        sign = exp[open_index - 1] if open_index - 1 >= 0 else ''
        sign = sign if sign in POLY_OPERATORS else ''
        exp = exp.replace(f'{sign}({poly})', '', 1)
        simplified_poly = internal_simplify(poly)
        result += f'{sign}({simplified_poly})'

    return result


def mul(exp: str) -> str:
    if not exp.__contains__(')('):
        exp = internal_mul(exp)
        return exp

    result = ''

    while True:
        mul_index = exp.index(')(') if ')(' in exp else -1

        if mul_index == -1:
            break

        left = exp[:mul_index]
        right = exp[mul_index + 2:]

        left_index = left.rindex('(') if '(' in left else -1
        right_index = right.index(')') if ')' in right else -1

        if left_index != -1:
            left = left[left_index + 1:]
        if right_index != -1:
            right = right[:right_index]

        result = mul_polys(left, right)
        if result.startswith('+'):
            result = result[1:]
        exp = exp.replace(f'({left})({right})', f'({result})', 1)

    result = exp
    return result


def mul_polys(poly1: str, poly2: str) -> str:
    result = ''
    polynomials = [prepare(poly1), prepare(poly2)]

    poly_accumulator = re.split(r'(?<!\^)\+', polynomials[0])
    for poly in polynomials[1:]:
        terms = re.split(r'(?<!\^)\+', poly)
        aux = poly_accumulator.copy()
        poly_accumulator.clear()
        for term1 in aux:
            for term2 in terms:
                poly_accumulator.append(mul_terms(term1, term2))

    result = ''.join(poly_accumulator)
    return result


def div(exp: str) -> str:
    if not exp.__contains__(')/('):
        exp = internal_div(exp)
        return exp

    result = ''

    while True:
        div_index = exp.index(')/(') if ')/(' in exp else -1

        if div_index == -1:
            break

        left = exp[:div_index]
        right = exp[div_index + 3:]

        left_index = left.rindex('(') if '(' in left else -1
        right_index = right.index(')') if ')' in right else -1

        if left_index != -1:
            left = left[left_index + 1:]
        if right_index != -1:
            right = right[:right_index]

        result = div_polys(left, right)
        if result.startswith('+'):
            result = result[1:]
        exp = exp.replace(f'({left})/({right})', f'({result})', 1)

    result = exp
    return result


def div_polys(poly1: str, poly2: str) -> str:
    if poly2 == '0':
        raise ZeroDivisionError('division by zero')
    poly1, poly2 = prepare(poly1), prepare(poly2)
    terms2 = re.split(r'(?<!\^)\+', poly2)
    if len(terms2) > 1:
        raise NotImplementedError('long division is not implemented yet')

    result = ''
    for term in re.split(r'(?<!\^)\+', poly1):
        result += div_terms(term, terms2[0])
    return result

# def get_highest_term(poly: str) -> str:
#     terms = re.split(r'(?<!\^)\+', poly)
#     highest_term = terms[0]
#     for term in terms:
#         if '^' in term:
#             if to_num(term[term.index('^') + 1:]) > to_num(highest_term[highest_term.index('^') + 1:]):
#                 highest_term = term
#         elif highest_term == '':
#             highest_term = term


def sum(exp: str) -> str:
    if not exp.__contains__(')+(') and not exp.__contains__(')-('):
        exp = re.sub(r'[\(\)]', '', exp)
        exp = internal_sum(exp)
        return exp

    if exp.__contains__('-('):
        while True:
            open_index = exp.index('-(') if '-(' in exp else -1
            if open_index == -1:
                break
            right_exp = exp[open_index:]
            close_index = right_exp.index(')') if ')' in right_exp else -1
            if close_index == -1:
                break

            poly = exp[open_index + 2:open_index + close_index]
            # break if don't have sign
            if re.search(r'(?<!\^)\+|\-', poly) == None:
                break

            # invert the sign of the terms
            inv_poly = re.sub(r'(?<!\^)\-', '{SUBTRACT}', poly)
            inv_poly = re.sub(r'(?<!\^)\+', '-', inv_poly)
            inv_poly = inv_poly.replace('{SUBTRACT}', '+')

            result = internal_simplify(inv_poly)
            exp = exp.replace(f'-({poly})', f'+({result})', 1)

    exp = re.sub(r'[\(\)]', '', exp)
    exp = prepare(exp)
    return internal_sum(exp)
# endregion
