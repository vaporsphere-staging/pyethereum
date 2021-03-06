import re

# Parse the statement-level structure, including if and while statements
print "da war ich"

def parse_block(block):
    global ast
    inner_block = []
    blocks_opened = 1
    block_concat = 'append'

    
    i = 0
    while i < len(block):
            
        if block[i][0] in ['if', 'else', 'elseif', 'while', 'repeat']:
            block_concat = 'append'
            blocks_opened += 1
            nxt_block  = parse_block(block[i+1:])
            statements = nxt_block[0]
            statements_counter = nxt_block[1]
            
            if len(statements) > 1 : statements = ['seq'] + statements
            if len(statements) == 1 : statements = statements[0]
            block[i].append(statements) 
            inner_block.append(block[i])
            
            if block[i][0] == 'elseif':
                u = inner_block[:-1]
                u.append(['if'] + block[i][1:])
                inner_block = u
                block_concat = 'add'
            if block[i][0] == 'else':
                u = inner_block[:-1]
                u.append(block[i][1:])
                inner_block = u
                block_concat = 'add'
            i += statements_counter
            
        elif block[i][0] in ['end']:
            blocks_opened -= 1
            if blocks_opened == 0:
                return inner_block, i+1, block_concat
                
        elif block[i][0] in ['until']:
            blocks_opened -= 1
            if blocks_opened == 0:
                return inner_block, i+1, block_concat
                
        else:
            inner_block.append(block[i])
            i += 1
            

def parse_lines(lns):
    global ast
    lines = []
    child_block = []
    ast = []
    i = 0
    while i < len(lns):
        lines.append(parse_line(lns[i]))
        
        i += 1
    
    i = 0
    while i < len(lines): 
        if lines[i][0] in ['if', 'else', 'elseif', 'while', 'repeat']:
            inner_block = parse_block(lines[i+1:])
            statements = inner_block[0]
            statements_counter = inner_block[1]
            
            if len(statements) > 1 : statements = ['seq'] + statements
            if len(statements) == 1 : statements = statements[0]

            if inner_block[2] == 'append' : lines[i].append(statements)  
            if inner_block[2] == 'add' : lines[i] = lines[i] + (statements[1:])  
            
            if lines[i][0] == 'else':
                u = ast[-1]
                u.append(lines[i][1:])
            elif lines[i][0] == 'elseif':
                u = ast[-1]
                u.append(['if'] + lines[i][1:])
            
            else:
                ast.append(lines[i])
                
            i += statements_counter

            
        elif lines[i][0]in ['end']:
            i += 1
    
        else:
            ast.append(lines[i])
            i += 1  
        
           
        
    return ast[0] if len(ast) == 1 else ['seq'] + ast
      
        


# Converts something like "b[4] = x+2 > y*-3" to
# [ 'b', '[', '4', ']', '=', 'x', '+', '2', '>', 'y', '*', '-', '3' ]
def chartype(c):
    if c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.':
        return 'alphanum'
    elif c in '\t ': return 'space'
    elif c in '()[]': return 'brack'
    else: return 'symb'

def tokenize(ln):
    tp = 'space'
    i = 0
    o = []
    global cur
    cur = ''
    def nxt():
        global cur
        if len(cur) >= 2 and cur[-1] == '-':
            o.extend([cur[:-1],'-'])
        elif len(cur.strip()) >= 1:
            o.append(cur)
        cur = ''
    while i < len(ln):
        c = chartype(ln[i])
        if c == 'brack' or tp == 'brack': nxt()
        elif c == 'space': nxt()
        elif c == 'end': nxt()
        elif c != 'space' and tp == 'space': nxt()
        elif c == 'symb' and tp != 'symb': nxt()
        elif c == 'alphanum' and tp == 'symb': nxt()
        cur += ln[i]
        tp = c
        i += 1
    nxt()
    if o[-1] in ['then','then\n','do','do\n','\n'] : o.pop()
    return o

# This is the part where we turn a token list into an abstract syntax tree
precedence = {
    '^': 1,
    'not': 1,
    '*': 2,
    '/': 3,
    '%': 4,
    '#/': 2,
    '#%': 2,
    '+': 3,
    '-': 3,
    '<': 4,
    '<=': 4,
    '>': 4,
    '>=': 4,
    '==': 5,
    '~=': 5,
    'and': 6,
    '&&': 6,
    'or': 7,
    '||': 7,
}

def toktype(token):
    print "TOKEN"
    print token
    print
    if token is None: return None
    elif token in ['(','[']: return 'lparen'
    elif token in [')',']']: return 'rparen'
    elif token == ',': return 'comma'
    elif token in ['!']: return 'monop'
    #elif token in ['not']: return 'monop'
    elif token in ['~=']: return 'noeq'
    elif not isinstance(token,str): return 'compound'
    elif token in precedence: return 'op'
    elif re.match('^[0-9a-z\-\.]*$',token): return 'alphanum'
    else: raise Exception("Invalid token: "+token)

# https://en.wikipedia.org/wiki/Shunting-yard_algorithm
def shunting_yard(tokens):
    iq = [x for x in tokens]
    oq = []
    stack = []
    prev,tok = None,None
    # The normal Shunting-Yard algorithm simply converts expressions into
    # reverse polish notation. Here, we try to be slightly more ambitious
    # and build up the AST directly on the output queue
    # eg. say oq = [ 2, 5, 3 ] and we add "+" then "*"
    # we get first [ 2, [ +, 5, 3 ] ] then [ *, 2, [ +, 5, 3 ] ]
    def popstack(stack,oq):
        tok = stack.pop()
        typ = toktype(tok)
        if typ == 'op':
            a,b = oq.pop(), oq.pop()
            oq.append([ tok, b, a])
        elif typ == 'noeq':
            a,b = oq.pop(), oq.pop()
            print "TYP A B TOK"
            print a, b, tok
            print
            oq.append([ b, tok, a])
        elif typ == 'monop':
            a = oq.pop()
            oq.append([ tok, a ])
        elif typ == 'rparen':
            args = []
            while toktype(oq[-1]) != 'lparen': args.insert(0,oq.pop())
            oq.pop()
            if tok == ']':
                oq.append(['access'] + args)
            elif tok == ')' and len(args) and args[0] != 'id':
                oq.append(['fun'] + args)
            else:
                oq.append(args[1])
    # The main loop
    while len(iq) > 0:
        prev = tok
        tok = iq.pop(0)
        typ = toktype(tok)
        if typ == 'alphanum':
            oq.append(tok)
        elif typ == 'lparen':
            if toktype(prev) != 'alphanum': oq.append('id')
            stack.append(oq.pop())
            oq.append(tok)
            oq.append(stack.pop())
            stack.append(tok)
        elif typ == 'rparen':
            while len(stack) and toktype(stack[-1]) != 'lparen':
                popstack(stack,oq)
            if len(stack):
                stack.pop()
            stack.append(tok)
            popstack(stack,oq)
        elif typ == 'monop' or typ == 'op':
            if tok == '-' and toktype(prev) not in [ 'alphanum', 'rparen' ]:
                oq.append('0')
            prec = precedence[tok]
            while len(stack) and toktype(stack[-1]) == 'op' and precedence[stack[-1]] < prec:
                popstack(stack,oq)
            stack.append(tok)
        elif typ == 'noeq':
            oq.append(oq.pop())
            oq.append('is')
            oq.append('not')
        elif typ == 'comma':
            while len(stack) and stack[-1] != 'lparen': popstack(stack,oq)
        #print 'iq',iq,'stack',stack,'oq',oq
    while len(stack):
        popstack(stack,oq)
    if len(oq) == 1:
        return oq[0]
    else:
        return [ 'multi' ] + oq

def parse_line(ln):
    tokens = tokenize(ln.strip())
    if tokens[0] == 'if' or tokens[0] == 'while' or tokens[0] == 'until':
        return [ tokens[0], shunting_yard(tokens[1:]) ]
    elif len(tokens) >= 1 and tokens[0] == 'elseif':
        return [ 'elseif', shunting_yard(tokens[1:]) ]
    elif len(tokens) == 1 and tokens[0] == 'else':
        return [ 'else' ]
    elif len(tokens) == 1 and tokens[0] == 'repeat':
        return [ 'repeat' ]
    elif len(tokens) == 1 and tokens[0] == 'end':
        return [ 'end' ]
    elif tokens[0] in ['mktx','suicide','stop']:
        return shunting_yard(tokens)
    else:
        eqplace = tokens.index('=')
        pre = 0
        i = 0
        while i < eqplace:
            try: nextcomma = i + tokens[i:].index(',')
            except: nextcomma = eqplace
            pre += 1
            i = nextcomma+1
        if pre == 1:
            return [ 'set', shunting_yard(tokens[:eqplace]), shunting_yard(tokens[eqplace+1:]) ]
        else:
            return [ 'mset', shunting_yard(tokens[:eqplace]), shunting_yard(tokens[eqplace+1:]) ]