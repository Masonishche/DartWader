import sys
# Імпортуємо тільки функцію lex, щоб уникнути автозапуску коду
from dartwader_lexer import lex

# Глобальні змінні парсера
table_symb = []
numRow = 0
len_tableOfSymb = 0
stepIndt = 2
indt = 0


def nextIndt():
    global indt
    indt += stepIndt
    return ' ' * indt


def predIndt():
    global indt
    indt -= stepIndt
    return ' ' * indt


# === Допоміжні функції ===

def getSymb():
    if numRow < len_tableOfSymb:
        return table_symb[numRow]
    return (0, 'EOP', 'End of Program', 0)


def parseToken(expected_lexeme, expected_token):
    global numRow
    indent = nextIndt()

    if numRow >= len_tableOfSymb:
        failParse('неочікуваний кінець програми', (expected_lexeme, expected_token, numRow))

    numLine, lex_val, tok, _ = getSymb()

    match = False
    if expected_lexeme == '*':  # Wildcard для значення (наприклад, будь-який id)
        if tok == expected_token:
            match = True
    else:
        if lex_val == expected_lexeme and tok == expected_token:
            match = True

    if match:
        print(f"{indent}parseToken: В рядку {numLine} токен ({lex_val}, {tok})")
        numRow += 1
        res = True
    else:
        failParse('невідповідність токенів', (numLine, lex_val, tok, expected_lexeme, expected_token))
        res = False

    predIndt()
    return res


def failParse(error_type, params):
    if error_type == 'неочікуваний кінець програми':
        print(f'Parser ERROR: Неочікуваний кінець програми. Очікувалось: {params[0]}')
    elif error_type == 'невідповідність токенів':
        (line, lex, tok, exp_lex, exp_tok) = params
        print(f'Parser ERROR: [Рядок {line}] Отримано ({lex},{tok}), очікувалось ({exp_lex},{exp_tok})')
    elif error_type == 'невідповідність інструкцій':
        print(f'Parser ERROR: [Рядок {params[0]}] Неочікувана інструкція: {params[1]}')

    sys.exit(100)


# === Реалізація граматики DartWader ===

def parseProgram():
    print("Parser: Початок аналізу")
    try:
        parseImportSection()

        # TopLevelDecl або MainFunction
        while True:
            _, lex_val, tok, _ = getSymb()

            if tok == 'End of Program':
                failParse('неочікуваний кінець програми', ('void main', 'keyword', 0))

            # Перевірка на MainFunction: void main ( )
            if lex_val == 'void':
                if numRow + 1 < len_tableOfSymb:
                    if table_symb[numRow + 1][1] == 'main':
                        parseMainFunction()
                        break

            parseTopLevelDecl()

        print("Parser: Синтаксичний аналіз завершився успішно!")
        return True
    except SystemExit:
        pass


# ImportSection = { ImportDecl }
# ImportDecl = 'import' String ';'
def parseImportSection():
    indent = nextIndt()
    print(indent + 'parseImportSection():')
    while True:
        _, lex_val, _, _ = getSymb()
        if lex_val == 'import':
            parseToken('import', 'keyword')
            parseToken('*', 'stringval')
            parseToken(';', 'punct')
        else:
            break
    predIndt()


# TopLevelDecl = VarDecl | FunctionDecl | ClassDecl
def parseTopLevelDecl():
    indent = nextIndt()
    print(indent + 'parseTopLevelDecl():')
    _, lex_val, _, _ = getSymb()

    if lex_val == 'class':
        parseClassDecl()
    elif lex_val in ('var', 'final', 'const') or lex_val in ('int', 'double', 'bool', 'string', 'void', 'dynamic'):
        # Щоб розрізнити змінну і функцію, дивимось наперед
        # Var: Type id = ... ;
        # Func: Type id ( ...
        lookahead_idx = 2 if lex_val in ('var', 'final', 'const') else 1
        # Спрощена евристика для КП
        if numRow + lookahead_idx < len_tableOfSymb:
            token_after_id = table_symb[numRow + lookahead_idx][1]
            if token_after_id == '(':
                parseFunctionDecl()
            else:
                parseVarDecl()
        else:
            parseVarDecl()
    else:
        failParse('невідповідність інструкцій', (*getSymb()[:3], 'TopLevelDecl'))
    predIndt()


# ClassDecl = 'class' Ident ... '{' ... '}'
def parseClassDecl():
    indent = nextIndt()
    print(indent + 'parseClassDecl():')
    parseToken('class', 'keyword')
    parseToken('*', 'id')
    # Пропускаємо extends/with для спрощення, шукаємо тіло
    _, lex_val, _, _ = getSymb()
    if lex_val == 'extends':
        parseToken('extends', 'keyword')
        parseToken('*', 'id')
    parseToken('{', 'bracket')
    # Пропускаємо члени класу до }
    while True:
        _, lex_val, _, _ = getSymb()
        if lex_val == '}': break
        # Тут мав би бути розбір методів/полів
        numRow += 1
    parseToken('}', 'bracket')
    predIndt()


# MainFunction = 'void' 'main' '(' ')' Block
def parseMainFunction():
    indent = nextIndt()
    print(indent + 'parseMainFunction():')
    parseToken('void', 'keyword')
    parseToken('main', 'keyword')
    parseToken('(', 'bracket')
    parseToken(')', 'bracket')
    parseBlock()
    predIndt()


# Block = '{' StatementList '}'
def parseBlock():
    indent = nextIndt()
    print(indent + 'parseBlock():')
    parseToken('{', 'bracket')
    parseStatementList()
    parseToken('}', 'bracket')
    predIndt()


# StatementList = Statement { ';' Statement }
# Примітка: Враховуючи специфікацію і приклади, де Assign сам має ';',
# ми просто читаємо Statements, поки не зустрінемо '}'
def parseStatementList():
    indent = nextIndt()
    print(indent + 'parseStatementList():')
    while True:
        _, lex_val, _, _ = getSymb()
        if lex_val == '}':
            break
        parseStatement()
    predIndt()


def parseStatement():
    indent = nextIndt()
    print(indent + 'parseStatement():')
    _, lex_val, tok, _ = getSymb()

    if lex_val == 'if':
        parseIfStatement()
    elif lex_val == 'for':
        parseForStatement()
    elif lex_val == 'while':
        parseWhileStatement()
    elif lex_val == 'read':
        parseInp()
    elif lex_val == 'write':
        parseOut()
    elif lex_val == 'return':
        parseReturn()
    elif lex_val in ('var', 'final', 'const', 'int', 'double', 'bool', 'string', 'dynamic'):
        parseVarDecl()  # Локальні змінні
    elif tok == 'id':
        # Присвоєння або виклик функції
        if numRow + 1 < len_tableOfSymb and table_symb[numRow + 1][1] == '(':
            parseFunctionCall()
        else:
            parseAssign()
    elif lex_val == ';':
        parseToken(';', 'punct')  # Порожній оператор
    else:
        failParse('невідповідність інструкцій', (*getSymb()[:3], 'Statement'))
    predIndt()


# VarDecl = [Modifier] [Type] Ident [ '=' Expression ] ';'
def parseVarDecl():
    indent = nextIndt()
    print(indent + 'parseVarDecl():')
    _, lex_val, _, _ = getSymb()
    if lex_val in ('var', 'final', 'const'):
        parseToken(lex_val, 'keyword')
        _, lex_val, _, _ = getSymb()

    if lex_val in ('int', 'double', 'bool', 'string', 'list', 'map', 'dynamic', 'void'):
        parseToken(lex_val, 'keyword')

    parseToken('*', 'id')
    _, lex_val, _, _ = getSymb()
    if lex_val == '=':
        parseToken('=', 'assign_op')
        parseExpression()
    parseToken(';', 'punct')
    predIndt()


# FunctionDecl = ... (спрощено)
def parseFunctionDecl():
    indent = nextIndt()
    print(indent + 'parseFunctionDecl():')
    # Пропускаємо тип і ім'я
    if table_symb[numRow][2] == 'keyword': numRow += 1
    parseToken('*', 'id')
    parseToken('(', 'bracket')
    # Params loop...
    while table_symb[numRow][1] != ')':
        numRow += 1
    parseToken(')', 'bracket')
    parseBlock()
    predIndt()


# Assign = Ident '=' Expression ';'
def parseAssign():
    indent = nextIndt()
    print(indent + 'parseAssign():')
    parseToken('*', 'id')
    parseToken('=', 'assign_op')  # Спрощено, можна додати +=, -=
    parseExpression()
    parseToken(';', 'punct')
    predIndt()


# ForStatement = 'for' '(' Ident '=' Expression ('to'|'downto') Expression ')' DoBlock
def parseForStatement():
    indent = nextIndt()
    print(indent + 'parseForStatement():')
    parseToken('for', 'keyword')
    parseToken('(', 'bracket')
    parseToken('*', 'id')
    parseToken('=', 'assign_op')
    parseExpression()

    _, lex_val, _, _ = getSymb()
    if lex_val in ('to', 'downto'):
        parseToken(lex_val, 'keyword')
    else:
        failParse('невідповідність токенів', (*getSymb()[:3], 'to/downto', 'keyword'))

    parseExpression()
    parseToken(')', 'bracket')
    parseDoBlock()
    predIndt()


def parseDoBlock():
    _, lex_val, _, _ = getSymb()
    if lex_val == '{':
        parseBlock()
    else:
        parseStatement()


# IfStatement = 'if' '(' Expression ')' Block [ 'else' Block ]
def parseIfStatement():
    indent = nextIndt()
    print(indent + 'parseIfStatement():')
    parseToken('if', 'keyword')
    parseToken('(', 'bracket')
    parseExpression()
    parseToken(')', 'bracket')
    parseBlock()
    _, lex_val, _, _ = getSymb()
    if lex_val == 'else':
        parseToken('else', 'keyword')
        parseBlock()
    predIndt()


def parseWhileStatement():
    indent = nextIndt()
    print(indent + 'parseWhileStatement():')
    parseToken('while', 'keyword')
    parseToken('(', 'bracket')
    parseExpression()
    parseToken(')', 'bracket')
    parseBlock()
    predIndt()


def parseInp():
    indent = nextIndt()
    print(indent + 'parseInp():')
    parseToken('read', 'keyword')
    parseToken('(', 'bracket')
    # IdentList
    while True:
        parseToken('*', 'id')
        if table_symb[numRow][1] == ',':
            parseToken(',', 'punct')
        else:
            break
    parseToken(')', 'bracket')
    parseToken(';', 'punct')
    predIndt()


def parseOut():
    indent = nextIndt()
    print(indent + 'parseOut():')
    parseToken('write', 'keyword')
    parseToken('(', 'bracket')
    # IdentList (у специфікації IdentList, але часто дозволяють вирази)
    # Тут реалізуємо вирази для зручності
    while True:
        parseExpression()
        if table_symb[numRow][1] == ',':
            parseToken(',', 'punct')
        else:
            break
    parseToken(')', 'bracket')
    parseToken(';', 'punct')
    predIndt()


def parseReturn():
    indent = nextIndt()
    print(indent + 'parseReturn():')
    parseToken('return', 'keyword')
    if table_symb[numRow][1] != ';':
        parseExpression()
    parseToken(';', 'punct')
    predIndt()


def parseFunctionCall():
    indent = nextIndt()
    print(indent + 'parseFunctionCall():')
    parseToken('*', 'id')
    parseToken('(', 'bracket')
    if table_symb[numRow][1] != ')':
        while True:
            parseExpression()
            if table_symb[numRow][1] == ',':
                parseToken(',', 'punct')
            else:
                break
    parseToken(')', 'bracket')
    parseToken(';', 'punct')
    predIndt()


# === Вирази (Пріоритети) ===

def parseExpression():
    indent = nextIndt()
    print(indent + 'parseExpression():')
    parseLogicalExpr()
    # Ternary check could be here
    predIndt()


def parseLogicalExpr():
    indent = nextIndt()
    print(indent + 'parseLogicalExpr():')
    parseComparisonExpr()
    while table_symb[numRow][1] in ('&&', '||'):
        parseToken(table_symb[numRow][1], 'logical_op')
        parseComparisonExpr()
    predIndt()


def parseComparisonExpr():
    indent = nextIndt()
    print(indent + 'parseComparisonExpr():')
    parseAdditiveExpr()
    while table_symb[numRow][1] in ('==', '!=', '<', '>', '<=', '>='):
        parseToken(table_symb[numRow][1], 'rel_op')
        parseAdditiveExpr()
    predIndt()


def parseAdditiveExpr():
    indent = nextIndt()
    print(indent + 'parseAdditiveExpr():')
    parseMultiplicativeExpr()
    while table_symb[numRow][1] in ('+', '-'):
        parseToken(table_symb[numRow][1], 'arith_op')
        parseMultiplicativeExpr()
    predIndt()


def parseMultiplicativeExpr():
    indent = nextIndt()
    print(indent + 'parseMultiplicativeExpr():')
    parsePrimaryExpr()
    while table_symb[numRow][1] in ('*', '/', '%'):
        parseToken(table_symb[numRow][1], 'arith_op')
        parsePrimaryExpr()
    predIndt()


def parsePrimaryExpr():
    indent = nextIndt()
    print(indent + 'parsePrimaryExpr():')
    _, lex_val, tok, _ = getSymb()

    if tok in ('intnum', 'realnum', 'stringval', 'boolval', 'nullval', 'id'):
        parseToken(lex_val, tok)
        # Check for function call inside expr
        if table_symb[numRow][1] == '(':
            parseToken('(', 'bracket')
            # args...
            while table_symb[numRow][1] != ')':
                parseExpression()  # Простий пропуск аргументів для рекурсії
                if table_symb[numRow][1] == ',':
                    numRow += 1
                else:
                    break
            parseToken(')', 'bracket')
    elif lex_val == '(':
        parseToken('(', 'bracket')
        parseExpression()
        parseToken(')', 'bracket')
    else:
        failParse('невідповідність інструкцій', (*getSymb()[:3], 'PrimaryExpr'))
    predIndt()


# === ENTRY POINT ===
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Помилка: вкажіть шлях до файлу (txt, dartwader, etc.)")
        sys.exit(1)

    filename = sys.argv[1]
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            source_code = f.read()

        # 1. Лексичний аналіз
        table_symb = lex(source_code)
        len_tableOfSymb = len(table_symb)

        # 2. Синтаксичний аналіз
        parseProgram()

    except FileNotFoundError:
        print(f"Файл не знайдено: {filename}")