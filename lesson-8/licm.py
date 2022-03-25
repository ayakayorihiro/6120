from data_flow import *
from dom import *
from make_cfg import *
import copy
import json

preheader_acc=0

"""
delete h from the flow graph
find nodes that can reach t
"""
def find_natural_loop_from_backedge(graph, h, t):
    loop = set()                # set of vertices that are in the loop
    # slow way of figuring out which nodes can reach t
    for node in graph:
        if node == h or node == t:
            continue
        # BFS from node
        q = [node]
        seent = set()
        while len(q) > 0:
            v = q.pop(0)
            if v == t:
                loop.add(node)
                break
            for succ in graph[v].successors:
                if succ != h and (not succ in seent): # we "erased" h
                    seent.add(succ)
                    q.append(succ)
    loop.add(h)
    loop.add(t)
    # print(loop)
    return {"entry" : h, "loop": loop}

def get_reaching_defs_immediately_before_loop(graph, label2block, reaching_defs, loop):
    loop_entry = loop["entry"]
    loop_reaching_defs = {}
    for pred in graph[loop_entry].predecessors:
        if pred in loop["loop"]:
            continue
        # Get all of the reaching definitions to the block before the loop entry block
        for var in reaching_defs[pred]:
            if var in loop_reaching_defs:
                loop_reaching_defs[var].union(reaching_defs[pred][var])
            else:
                loop_reaching_defs[var] = reaching_defs[pred][var]
        # Get all of the definitions within each block before the loop entry block
        for var, defn in get_var_defs(label2block[pred]).items():
            op = defn["op"]
            type = defn["type"]
            val = " {}".format(defn["value"]) if "value" in defn else ""
            args = "".join(" " + a for a in defn["args"]) if "args" in defn else ""
            funcs = "".join(" @" + f for f in defn["funcs"]) if "funcs" in defn else ""
            labels = "".join(" ." + l for l in defn["labels"]) if "labels" in defn else ""
            def_str = {"{}: {} = {}{}{}{}{};".format(var, type, op, funcs, args, labels, val)}
            if not var in loop_reaching_defs:
                loop_reaching_defs[var] = def_str
            else:
                loop_reaching_defs[var].union(def_str)
    return loop_reaching_defs

def is_all_reachdefs_outside(var, before_loop_defs, block_reaching_defs):
    if not var in before_loop_defs:
        return False
    # if not block_reaching_defs[var] == before_loop_defs[var]:
    #     print("chucking var " + var)
    #     print("blocks' reaching def: " + str(block_reaching_defs[var]))
    #     print("before loop defs: " + str(before_loop_defs[var]))
    # else:
    #     print("not chucking var " + var)
    return block_reaching_defs[var] == before_loop_defs[var]

def find_loop_invariant_instrs(graph, label2block, reaching_defs, loop):
    before_loop_defs = get_reaching_defs_immediately_before_loop(graph, label2block, reaching_defs, loop)
    loop_invariants = {}        # mapping from variables whose definitions are loop invariants to their definitions
    # print("LOOP HERE: " + str(loop))
    while True:
        # print("looping to find LIs")
        prev_loop_invariants = copy.deepcopy(loop_invariants)
        for lblock in loop["loop"]:     # basic block within loop
            # print()
            # print("traversing block " + lblock)
            for instr in label2block[lblock]:
                if (not "args" in instr) or (not "dest" in instr):
                    continue
                add_to_li = True
                for arg in instr["args"]:
                    if arg in loop_invariants:
                        add_to_li = True
                    elif not is_all_reachdefs_outside(arg, before_loop_defs, reaching_defs[lblock]): # this is LI bc all reaching defs of var are outside of the loop
                        add_to_li = False
                        break
                    #continue    # check if reaching definitions of the arg is inside the loop or not
                if add_to_li:
                    loop_invariants[instr["dest"]] = { "instr": instr, "block" : lblock }
        if prev_loop_invariants == loop_invariants:
            break

    # print(loop_invariants)
    return loop_invariants

def get_loop_exits(graph, loop):
    # print(graph)
    # print("=======================")
    # print(loop)
    exits = set()
    for lblock in loop["loop"]:
        for succ in graph[lblock].successors:
            if not succ in loop["loop"]:
                exits.add(lblock)
    # print("Exits: " + str(exits))
    return exits

# def get_loop_blocks_that_define_var(label2block, var, vardef, loop):
def is_var_defined_elsewhere(label2block, var, vardef, loop):
    for lblock in loop["loop"]:
        # print(lblock)
        for defvar, defn in get_var_defs(label2block[lblock]).items():
            if var == defvar and vardef != defn:
                return True
    return False

def get_loop_blocks_that_use_var(label2block, var, loop):
    using_blocks = set()
    for lblock in loop["loop"]:
        for instr in label2block[lblock]:
            if (not "args" in instr): #  or (not "dest" in instr)
                continue
            if var in instr["args"]:
                using_blocks.add(lblock)
    return using_blocks

"""
Does the loop invariant satisfy:
- the assigned-to variable is dead after the loop
- instruction can't have side effect (is the op not a div)
"""
def sat_relaxed_cond_3(graph, label2block, exits, li_var, loop_invariants, loop):
    side_effect_ops = ["div", "print"]
    # ruling out division
    if "op" in loop_invariants[li_var]["instr"] and loop_invariants[li_var]["instr"]["op"] in side_effect_ops:
        return False
    # the assigned-to variable is dead after the loop
    li_block = loop_invariants[li_var]["block"]
    for lexit in exits:         # for every loop exit
        for succ in graph[lexit].successors: # want to perform BFS/DFS from every successor to see if there are any future uses of the variable
            if succ in loop["loop"]:
                continue
            seent = set()
            q = [succ]
            while len(q) > 0:
                curr_block = q.pop(0)
                for instr in label2block[curr_block]:
                    if "args" in instr and li_var in instr["args"]: # used in a future block
                        # print("found use in block " + curr_block)
                        return False
                    for further_succ in graph[curr_block].successors:
                        if not further_succ in seent:
                            seent.add(further_succ)
                            q.append(further_succ)

    return True

def can_move(graph, label2block, dominators, loop_invariants, li_var, loop, exits):
    li_block = loop_invariants[li_var]["block"]
    # no other definitions of the same variable exist in the loop
    if is_var_defined_elsewhere(label2block, li_var, loop_invariants[li_var]["instr"], loop):
        # print(li_var + " is defined elsewhere in the loop, can't move")
        return False
    # the definition dominates all of its uses
    for use_block in get_loop_blocks_that_use_var(label2block, li_var, loop):
        if not li_block in dominators[use_block]:
            # print(li_block + " does not dominate use: " + use_block)
            return False
    # the instruction dominates all loop exits
    for lexit in exits:
        if (not li_block in dominators[lexit]) and (not sat_relaxed_cond_3(graph, label2block, exits, li_var, loop_invariants, loop)): # there exists an exit not dominated by li block
            # print(li_block + " does not dominate loop exit: " + lexit + " and does not satisfy the relaxed condition")
            return False

    return True

"""
Returns new version of the graph, label2block, instrs for future computation
"""
def make_preloop_header(graph, label2block, dominators, loop_invariants, loop, instrs):
    global preheader_acc
    preheader_label = "preheader" + str(preheader_acc)
    loop_entry = loop["entry"]
    preloop_header = [ {"label" : preheader_label} ]
    if not loop_invariants:
        return instrs
    new_instrs = [] # instrs.copy()
    new_graph = copy.deepcopy(graph)
    new_label2block = copy.deepcopy(label2block)
    exits = get_loop_exits(graph, loop)
    for li_var in loop_invariants:
        if can_move(graph, label2block, dominators, loop_invariants, li_var, loop, exits):
            # print("can move " + str(loop_invariants[li_var]))
            preloop_header.append(loop_invariants[li_var]["instr"])
            # new_instrs.remove(loop_invariants[li_var]["instr"])
        # else:
        #     print("can NOT move " + str(loop_invariants[li_var]))
    preheader_acc += 1
    # stitching together the new set of instructions...
    for instr in instrs:
        if instr == { "label" : loop_entry }:
            new_instrs += preloop_header # add the new stuff in before the loop
        if instr in preloop_header: # things that we have moved to before the loop
            continue                # don't copy over
        new_instrs.append(instr)    # copy over
    new_label2block[preheader_label] = preloop_header
    for vertex in graph:
        if (not vertex in loop["loop"]) and (loop_entry in graph[vertex].successors):
            graph[vertex].successors.remove(loop_entry)
            graph[vertex].successors.add(preheader_label)
    new_graph[preheader_label] = GraphNode([loop_entry])
    new_graph[preheader_label].predecessors = graph[loop_entry].predecessors
    # print(graph)
    # print("=========================")
    # print(new_graph)
    return new_instrs, new_graph, new_label2block

def find_loops(graph, initial_node, dominator_map):
    loops = []
    for vertex in graph:        # current node
        successors = graph[vertex].successors
        v_dominators = dominator_map[vertex]
        for succ in successors:
            if succ in v_dominators:
                # print("back edge! " + vertex + " -> " + succ)
                natural_loop = find_natural_loop_from_backedge(graph, succ, vertex)
                loops.append(natural_loop)

    return loops

def main():
    preheader_acc = 0
    # Load the program JSON
    prog = json.load(sys.stdin)
    new_prog = copy.deepcopy(prog)
    for func in prog['functions']:
        new_instrs = func['instrs'].copy()
        # Get the basic block and CFG for this function
        blocks = form_blocks(func['instrs'])
        label2block = label_blocks(blocks)
        graph, new_label2block = get_cfg(label2block)
        initial_node = label2block[0][0]
        dominators = find_dominators(graph, initial_node)
        analysis = REACHING_DEFS
        reaching_defs, _ = data_flow_analysis(graph, new_label2block, *analysis)
        loops = find_loops(graph, initial_node, dominators)
        # print(new_label2block["then"])
        # for r in reaching_defs:
        #     print(r + ":\n" + str(reaching_defs[r]) + "\n")
        for loop in loops:
            loop_invariants = find_loop_invariant_instrs(graph, new_label2block, reaching_defs, loop)
            new_instrs, graph, new_label2block = make_preloop_header(graph, new_label2block, dominators, loop_invariants, loop, new_instrs)
            func['instrs'] = new_instrs # replace with inserted version of instructions
            # print(preloop_header_code)

    print(json.dumps(prog, indent = 4))

if __name__ == '__main__':
    main()
