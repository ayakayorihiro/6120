import json
import sys
from collections import OrderedDict

TERMINATORS = 'jmp', 'br', 'ret'

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
                    raise ValueError("Program has a non-defined variable")
                instr['args'][i] = old_to_new[instr['args'][i]]


# def local_value_numbering(block):
#     table = {}                  # values --> canonical variable
#     var2num = {}

#     for instr in block:
#         value = ()
#         if value in table:
            

# def dead_code_elimination(block):
    

def swap_add_and_subtract(body):
    for instr in body:
        if 'op' in instr:
            if instr['op'] == "add":
                instr['op'] = "sub"
            elif instr['op'] == "sub":
                instr['op'] = "add"
            elif instr['op'] == "mul":
                instr['op'] = "div"
            elif instr['op'] == "div":
                instr['op'] = "mul"
    return body

def main():
    prog = json.load(sys.stdin)
    for fun in prog['functions']:
        freshen(fun)

    print(json.dumps(prog, indent=4))

if __name__ == '__main__':
    main()
