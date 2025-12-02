import sys

# === Ключові слова ===
keywords = {
    'var', 'final', 'const', 'dynamic', 'void', 'int', 'double', 'bool', 'string',
    'list', 'map', 'if', 'else', 'for', 'while', 'do', 'break', 'continue',
    'return', 'class', 'extends', 'with', 'new', 'this', 'import',
    'async', 'await', 'try', 'catch', 'throw',
    'true', 'false', 'null', 'read', 'write', 'to', 'downto'
}

# === Оператори ===
operators = {
    '=': 'assign_op', '+=': 'assign_op', '-=': 'assign_op', '*=': 'assign_op',
    '/=': 'assign_op', '??=': 'assign_op',
    '+': 'arith_op', '-': 'arith_op', '*': 'arith_op', '/': 'arith_op', '%': 'arith_op',
    '==': 'rel_op', '!=': 'rel_op', '<': 'rel_op', '>': 'rel_op', '<=': 'rel_op', '>=': 'rel_op',
    '&&': 'logical_op', '||': 'logical_op', '!': 'logical_op',
    '?.': 'special_op', '??': 'special_op',
    '(': 'bracket', ')': 'bracket', '{': 'bracket', '}': 'bracket',
    '[': 'bracket', ']': 'bracket',
    ';': 'punct', ',': 'punct', ':': 'punct', '.': 'punct',
    '@': 'special', '#': 'special', '$': 'special'
}

# Глобальні змінні для стану (щоб можна було обнулити при виклику функції)
source = ""
pos = -1
line_num = 1
table_id = {}
table_const = {}
table_symb = []


def init_lexer(src_code):
    global source, pos, line_num, table_id, table_const, table_symb
    source = src_code + '\0'
    pos = -1
    line_num = 1
    table_id = {}
    table_const = {}
    table_symb = []


def get_char():
    global pos
    pos += 1
    return source[pos] if pos < len(source) else '\0'


def unget_char():
    global pos
    if pos > 0:
        pos -= 1


def get_char_class(c):
    if c in ' \t\r\n': return 'ws' if c != '\n' else 'nl'
    if c.isalpha() or c == '_': return 'Letter'
    if c.isdigit(): return 'Digit'
    return c if c in "+-*/%=!<>&|?.\"'\\()[]{};,.:@#$" else 'other'


def skip_spaces_and_comments():
    global line_num
    while True:
        c = get_char()
        if c == '\0':
            unget_char()
            return False
        if c in ' \t\r':
            continue
        if c == '\n':
            line_num += 1
            continue

        # Коментарі
        if c == '/':
            next_c = source[pos + 1] if pos + 1 < len(source) else '\0'
            if next_c == '/':  # //
                get_char()
                while (c := get_char()) not in '\n\0':
                    pass
                if c == '\n': line_num += 1
                unget_char()
                continue
            elif next_c == '*':  # /* */
                get_char()
                while True:
                    c = get_char()
                    if c == '\n': line_num += 1
                    if c == '\0':
                        print(f"Lexer Error: Unclosed comment at line {line_num}")
                        sys.exit(1)
                    if c == '*' and source[pos + 1] == '/':
                        get_char()
                        break
                continue
        unget_char()
        return True


def process_token(lexeme, token_type, idx=None):
    # Додаємо в таблицю
    table_symb.append((line_num, lexeme, token_type, idx))


def run_lexer_analysis():
    while skip_spaces_and_comments():
        c = get_char()
        if c == '\0': break

        lexeme = ""
        cls = get_char_class(c)

        if cls == 'Letter':
            lexeme = c
            while True:
                c = get_char()
                if get_char_class(c) in ('Letter', 'Digit'):
                    lexeme += c
                else:
                    unget_char()
                    break
            if lexeme in keywords:
                t = 'keyword'
                if lexeme in ('true', 'false'): t = 'boolval'
                if lexeme == 'null': t = 'nullval'
                process_token(lexeme, t)
            else:
                if lexeme not in table_id:
                    table_id[lexeme] = len(table_id) + 1
                process_token(lexeme, 'id', table_id[lexeme])

        elif cls == 'Digit':
            lexeme = c
            is_real = False
            while True:
                c = get_char()
                if get_char_class(c) == 'Digit':
                    lexeme += c
                elif c == '.' and not is_real:
                    is_real = True
                    lexeme += c
                else:
                    unget_char()
                    break
            token_type = 'realnum' if is_real else 'intnum'
            if lexeme not in table_const:
                table_const[lexeme] = (token_type, len(table_const) + 1)
            process_token(lexeme, token_type, table_const[lexeme][1])

        elif c in '"\'':
            quote = c
            lexeme = c
            while True:
                c = get_char()
                if c == '\\':
                    lexeme += c + get_char()
                elif c == quote:
                    lexeme += c
                    break
                elif c == '\0':
                    print(f"Lexer Error: Unclosed string at line {line_num}")
                    sys.exit(1)
                else:
                    lexeme += c
            if lexeme not in table_const:
                table_const[lexeme] = ('stringval', len(table_const) + 1)
            process_token(lexeme, 'stringval', table_const[lexeme][1])

        else:
            lexeme = c
            next_c = source[pos + 1] if pos + 1 < len(source) else '\0'
            if (c + next_c) in operators:
                lexeme += next_c
                get_char()

            if lexeme in operators:
                process_token(lexeme, operators[lexeme])
            else:
                print(f"Lexer Error: Unknown symbol '{lexeme}' at line {line_num}")
                sys.exit(1)

    return table_symb


# === Головна функція для виклику з парсера ===
def lex(file_content):
    init_lexer(file_content)
    return run_lexer_analysis()


# === Для запуску як окремого скрипта ===
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python dartwader_lexer.py <filename>")
        sys.exit(1)

    try:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            content = f.read()
            result = lex(content)
            # Вивід для демонстрації (якщо запущено напряму)
            print(f"{'Ln':<3} {'Lexeme':<20} {'Token':<14} {'Idx'}")
            print("-" * 50)
            for row in result:
                print(f"{row[0]:<3} {row[1]:<20} {row[2]:<14} {row[3] if row[3] is not None else ''}")
    except FileNotFoundError:
        print(f"File not found: {sys.argv[1]}")