#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys

#From nanometer to 1 byte:
def to_1by(nm):
    return int(round((nm - 375) * (255/300.)))

class Flog : pass

flog = Flog()
flog.control = {'nano': None, 'blue': None,'green': None, 'red': None}
flog.rule_order = ['nano','red', 'green', 'blue'] #Forced to index dic entries of flog.control to keep proper order of the rules
flog.MaxVal = 255
flog.sysin = ['nano']
flog.sysout = 'blue green red'.split()
flog.ZeroV = 0

sysio = dict()

#Fuzzy sets, lack a special entry for absolute at 255, one exist for value at 0, see IN
sysio_file = \
{
    'nano' :
    {
        'T1' : [0, 4, 4, 8],
        'T2' : [4, 13, 13, 22],
        'T3' : [13, 29, 29, 45],
        'T4' : [29, 45, 45, 55],
        'T5' : [45, 55, 55, 63],
        'T6' : [55, 70, 70, 81],
        'T7' : [70, 90, 90, 99],
        'T8' : [90, 105, 105, 111],
        'T9' : [105, 115, 115, 124],
        'T10' : [115, 124, 124, 133],
        'T11' : [124, 175, 175, 234],
        'T12' : [175, 234, 234, 255]
    },
    'blue' :
    {
        'IN' : [0, 1, 0, 1],
        'VW' : [1, 74, 74, 111],
        'W' : [74, 111, 111, 148],
        'A' : [111, 148, 148, 185],
        'S' : [148, 185, 185, 222],
        'VS' : [185, 222, 254, 255] },
    'green' :
    {
        'IN' : [0, 1, 0, 1],
        'VW' : [1, 74, 74, 111],
        'W' : [74, 111, 111, 148],
        'A' : [111, 148, 148, 185],
        'S' : [148, 185, 185, 222],
        'VS' : [185, 222, 254, 255] },
    'red' :
    {
        'IN' : [0, 1, 0, 1],
        'VW' : [1, 74, 74, 111],
        'W' : [74, 111, 111, 148],
        'A' : [111, 148, 148, 185],
        'S' : [148, 185, 185, 222],
        'VS' : [185, 222, 254, 255] } }


#Rules. Would need 6 more entries to accurately depict the absolute at 255

rule_file = \
[   ['T1', 'IN', 'IN', 'IN'],
    ['T2', 'VW', 'IN', 'W'],
    ['T3', 'W', 'IN', 'S'],
    ['T4', 'VW', 'IN', 'VS'],
    ['T5', 'IN', 'IN', 'VS'],
    ['T6', 'IN', 'VW', 'VS'],
    ['T7', 'IN', 'VS', 'VS'],
    ['T8', 'IN', 'VS', 'A'],
    ['T9', 'IN', 'VS', 'IN'],
    ['T10', 'VW', 'VS', 'IN'],
    ['T11', 'VS', 'VS', 'IN'],
    ['T12', 'VS', 'IN', 'IN']  ]



from pprint import pprint

def main(nm) :
    print 'initial value : %s' % nm
    global sysio
    sysio = dict()
    for var in flog.control :
        sysio[var] = setup_fuzzy_sets(var)
    rules = setup_rules(flog.rule_order) #Had to preserve rule order
    flog.control['nano'] = to_1by(nm) # nm from outside
    fuzzify(flog.sysin)
    evaluate(rules)
    for n, rule in enumerate(rules) :
        if rule[0]['value'] and rule[1]['value'] : show(n, rule)
    defuzzify(flog.sysout)
    print 'out -> red %i, green %i, blue %i' % (flog.control['red'],flog.control['green'], flog.control['blue'])


def show(n, clauses) :
    values = [clause['value'] for clause in clauses]
    print '%2i: %s = %s' % (n, rule_file[n], values)


def setup_fuzzy_sets(name) :
    D = dict()        # set up new dictionary
    data = sysio_file[name]    # point to file data
    for fset in data :    # loop on fuzzy set symbols
        a, b, c, d = data[fset]    # get original 4-point data
        D[fset] = {}    # set up 2nd order dictionary
        D[fset]['value'] = 0    # degree of membership
        D[fset]['base1'] = a    # leftmost x-axis point of memb. function
        D[fset]['base2'] = d    # rightmost x-axis point of memb. function
        D[fset]['slope1'] = flog.MaxVal / (b - a)    # slope of left side
        D[fset]['slope2'] = flog.MaxVal / (d - c)    # slope of right side
    return D

def setup_rules(vars) :    # fuzzy variable names
    rules = []        # set up new list
    for rule in rule_file :    # loop on rules
        clauses = []    # set up new clause list
        for n, symbol in enumerate(rule) :    # loop on clauses
            clauses.append(sysio[vars[n]][symbol])    # point to fuzzy set
        rules.append(clauses)    # set this rule
    return rules


def fuzzify(vars) :
    for var in vars :
        for fset in sysio[var] :
            eval_membership(sysio[var][fset], flog.control[var])

def eval_membership(fset, input) :
    delta_1 = input - fset['base1']
    delta_2 = fset['base2'] - input
    outside = delta_1 <= 0 or delta_2 <= 0
    if outside : fset['value'] = 0 ; return
    membership = min(fset['slope1'] * delta_1, fset['slope2'] * delta_2)
    fset['value'] = min(membership, flog.MaxVal) # enforce upper limit


def evaluate(rules) : # a list of fset dicts
    for rule in rules : # a dict
        strength = flog.MaxVal # max rule strength allowed
        for clause in rule[:1] : # get antecedent
            strength = min(strength, clause['value']) # determine strength
        for clause in rule[1:] : # get consequent
            clause['value'] = max(strength, clause['value']) # apply strength

def defuzzify(vars) :
    for var in vars :
        products = areas = 0 #Absolutely imperative to reset, if not, all outputs mingle
        for symbol in sysio[var] :
            fset = sysio[var][symbol]
            area = trapezoid(fset)
            products += area * (fset['base1'] + ((fset['base2'] - fset['base1']) / 2))
            areas += area
        if areas : flog.control[var] = products / areas
        else : no_rule(flog.control['nano']) # Important here since some of the spectrum has no rules

def trapezoid(fset) : # fset : membership descriptor
    base = fset['base2'] - fset['base1']
    top = base - ((fset['value'] / fset['slope1']) - (fset['value'] / fset['slope2']))
    return fset['value'] * ((base + top) / 2)

def no_rule(x) : exit('no rule for nano %i' % int(round(x*(300./255)+375))) #Bring back byte to nano, could have saved the entry value...


if len(sys.argv) < 2 : print 'Veuillez spécifier une longueur d\'ondes entre 376nm et 674nm'
else : main(int(sys.argv[1]))
