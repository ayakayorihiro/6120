from data_flow import *
from dom import *
from make_cfg import *
import copy
import json

def get_all_vars(label2block):
    varz = {}
    for label in label2block:
        block = label2block[label]
        for instr in block:
            if "dest" in instr:
                if not instr["dest"] in varz:
                    varz[instr["dest"]] = set()
                varz[instr["dest"]].add(label)

    return varz

def insert_phi(graph, label2block, df): # df is dominance frontier
    # print(graph)
    # print(json.dumps(label2block, indent=2))
    varz = get_all_vars(label2block)
    for v in varz:
        for d in varz[v]:
            for block in df:
    # print("reaching defs: " + str(reaching_defs))

def main():
    # Load the program JSON
    prog = json.load(sys.stdin)

    # Do this for each function
    for func in prog['functions']:
        # Get the basic block and CFG for this function
        blocks = form_blocks(func['instrs'])
        label2block = label_blocks(blocks)
        graph, new_label2block = get_cfg(label2block)
        # print("====" + func)
        dominators = find_dominators(graph, label2block[0][0])
        strict_dominators = find_strict_dominators(dominators)
        df = compute_dominance_frontier(graph, strict_dominators_dict)
        analysis = REACHING_DEFS
        reaching_defs, _ = data_flow_analysis(graph, new_label2block, *analysis)
        insert_phi(graph, new_label2block, df)

if __name__ == '__main__':
    main()
