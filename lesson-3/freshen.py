import copy
import json
import sys

def freshen(fun):
    block=fun["instrs"]
    fresh_name_num=0
    old_to_new={}

    if 'args' in fun:
        for arg in fun['args']:
            arg_name = arg['name']
            old_to_new[arg_name] = arg_name
    for instr in block:
        if 'dest' in instr:
            dest = instr['dest']
            new_name="var" + str(fresh_name_num)
            fresh_name_num+=1
            old_to_new[dest] = new_name
            instr['dest'] = new_name
        if 'args' in instr:
            for i in range(len(instr['args'])):
                if instr['args'][i] not in old_to_new.keys():
                    raise ValueError("Program has a free variable")
                instr['args'][i] = old_to_new[instr['args'][i]]

def main():
    prog = json.load(sys.stdin)
    for fun in prog['functions']:
        freshen(fun)
    print(json.dumps(prog, indent=4))

if __name__ == '__main__':
    main()
