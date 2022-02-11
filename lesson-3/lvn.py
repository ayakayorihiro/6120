import copy
import json
import sys

from blocks import form_blocks
from freshen import freshen
from dce import dead_code_elimination

TERMINATORS = 'jmp', 'br', 'ret'

def get_args_tuple(args, var2num):
    meta_args=[]
    for arg in args:
        if arg in var2num:
            meta_args.append(var2num[arg])
        else:                   # free variable/argument
            meta_args.append(arg)
    return meta_args

def local_value_numbering(block, function_args):
    table = {}                  # values --> canonical variable
    var2num = {}
    num_to_canonical_var = {}

    table_number=0
    new_instrs=[]
    for instr in block:
        new_instr={}
        if 'dest' in instr:
            value = ()
            curr_dest=instr['dest']
            operation = instr['op']
            if operation == 'const':
                value = ('const', instr['value'])
            else:
                value = (operation, tuple(get_args_tuple(instr['args'], var2num)))
            if value in table:
                num, var = table[value]
                var2num[curr_dest] = num
                new_instr={"dest" : curr_dest, "type" : instr["type"], "op" : "id", "args" : [ var ]}
            else:
                num_to_canonical_var[table_number] = curr_dest
                var2num[curr_dest] = table_number
                table[value] = (table_number, curr_dest)
                table_number += 1
                new_instr = copy.deepcopy(instr)
        else:
            new_instr=instr
        if 'args' in new_instr:
            new_args=[]
            for arg in new_instr['args']:
                if arg not in var2num:
                    new_args.append(arg) # argument to function
                else:
                    new_args.append(num_to_canonical_var[var2num[arg]])
            new_instr['args'] = new_args

        new_instrs.append(new_instr)
        # print("var2num: " + str(var2num))
        # print("table:  " + str(table))
        # print()

    return new_instrs

def local_value_numbering_wrapper(blocks, function_args):
    blocks_in_fun = []
    for block in blocks:
        blocks_in_fun.extend(local_value_numbering(block, function_args))
    return {"instrs" : blocks_in_fun}

def main():
    prog = json.load(sys.stdin)
    for i in range(len(prog['functions'])):
        fun = prog['functions'][i]
        freshen(fun)            # rename all variables to fresh names
        if 'args' in 'functions':
            function_args = prog['functions']['args']
        else:
            function_args = []
        new_instrs = local_value_numbering_wrapper(form_blocks(fun['instrs']), function_args)
        prog['functions'][i].update(new_instrs)
        dead_code_elimination(fun)
    print(json.dumps(prog, indent=4))

if __name__ == '__main__':
    main()
