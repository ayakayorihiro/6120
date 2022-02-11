import copy
import json
import sys

TERMINATORS = 'jmp', 'br', 'ret'

def dead_code_elimination_helper(fun):
    used_vars=set()
    for instr in fun["instrs"]:
        if 'args' in instr:
            used_vars.update(instr['args'])
    for instr in fun["instrs"]:
        if ('dest' in instr and instr['dest'] not in used_vars):
            fun["instrs"].remove(instr)

def dead_code_elimination(fun):
    old_fun=copy.deepcopy(fun)
    dead_code_elimination_helper(fun)
    while old_fun != fun:
        # print("========oldfun")
        # print(json.dumps(old_fun, indent=4))
        # print("========newfun")
        # print(json.dumps(fun, indent=4))
        old_fun=copy.deepcopy(fun)
        dead_code_elimination_helper(fun)

def main():
    prog = json.load(sys.stdin)
    for fun in prog['functions']:
        dead_code_elimination(fun)
    print(json.dumps(prog, indent=4))

if __name__ == '__main__':
    main()
