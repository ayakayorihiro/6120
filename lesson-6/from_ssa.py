from dom import *
from make_cfg import *
import copy
import json

def remove_phi(label2block):
    no_phi_label2block = {label : [] for label in label2block}
    instrs_to_add = {label : [] for label in label2block}
    # first, let's get rid of all of the phi nodes
    for label in label2block:
        # print("in label " + label)
        no_phi_block = []
        for instr in label2block[label]:
            if ('op' in instr) and (instr['op'] == "phi"):
                # add instructions
                labels = instr["labels"]
                args = instr["args"]
                for i in range(len(labels)):
                    phi_label = labels[i]
                    arg = args[i]
                    id_instr = {"op" : "id", "dest" : instr["dest"], "args" : [arg], "type" : instr["type"]}
                    instrs_to_add[phi_label].append(id_instr)
            else:
                no_phi_block.append(instr)
        no_phi_label2block[label] += no_phi_block
    # print(no_phi_label2block)
    # next, let's add the new instructions to the end of the other blocks
    for label in instrs_to_add:
        last = no_phi_label2block[label][-1]
        if ('op' in last) and (last['op'] == 'br' or last['op'] == 'jmp'):
            new_block = no_phi_label2block[label][:-1]
            new_block += instrs_to_add[label]
            new_block.append(last)
            no_phi_label2block[label] = new_block
        else:
            no_phi_label2block[label] += instrs_to_add[label]
    new_instrs = []
    # make sure that we have sth in the form of instructions
    for blockname in no_phi_label2block:
        # print(blockname + ": " + str(no_phi_label2block[blockname]))
        new_instrs += no_phi_label2block[blockname]
    return new_instrs

def main():
    # Load the program JSON
    prog = json.load(sys.stdin)

    # Do this for each function
    for func in prog['functions']:
        # Get the basic block and CFG for this function
        blocks = form_blocks(func['instrs'])
        label2block = label_blocks(blocks)
        graph, new_label2block = get_cfg(label2block)
        no_phi_instrs = remove_phi(new_label2block)
        func['instrs'] = no_phi_instrs
    print(json.dumps(prog, indent=2))

if __name__ == '__main__':
    main()

