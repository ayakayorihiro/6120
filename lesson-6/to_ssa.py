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
                varz[instr["dest"]].add((label, instr["type"]))

    return varz

def insert_phi(graph, label2block, df): # df is dominance frontier
    # print(graph)
    # print(json.dumps(label2block, indent=2))
    defs = get_all_vars(label2block)
    old_defs = {}
    phi_var_to_blocks = {v : set() for v in defs }
    
    while not (old_defs == defs):
        old_defs = copy.deepcopy(defs)
        for v in old_defs:
            for def_block, var_type in old_defs[v]:
                for blockname in df[def_block]:
                    # add phi node to block if we haven't done so already
                    if not (blockname in phi_var_to_blocks[v]):
                        phi = { "op" : "phi", "type" : var_type, "args" : [], "dest" : v, "labels" : [] }
                        label2block[blockname].append(phi)
                        phi_var_to_blocks[v].add(blockname)
                        # add block to defs[v] unless we have already
                        defs[v].add((blockname, var_type))
    # print("reaching defs: " + str(reaching_defs))

    print(label2block)
    # print(json.dumps(label2block, indent=2))

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
        df = compute_dominance_frontier(graph, strict_dominators)
        print("dominators map:\n" + str(dominators) + "\n")
        print("strict dominators map:\n" + str(strict_dominators) + "\n")
        print("dominance frontier:\n" + str(df) + "\n")
        analysis = REACHING_DEFS
        reaching_defs, _ = data_flow_analysis(graph, new_label2block, *analysis)
        insert_phi(graph, new_label2block, df)

if __name__ == '__main__':
    main()
