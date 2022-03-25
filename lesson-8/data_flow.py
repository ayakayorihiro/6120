"""
This file contains code to perform data flow analysis on a Bril program.
"""

import copy
import json
import sys
from make_cfg import *


def data_flow_analysis(graph, label2block, forward, init, merge_fn, transfer_fn):
    """
    The worklist algorithm for data flow analysis.

    graph:       the input CFG.
    label2block: a dict from labels to a basic block.
    forward:     a boolean of whether the analysis is forward.
    init:        the initial value of the analysis
    merge_fn:    a function to merge the outputs of the previous analysis
    transfer_fn: a function to calculate the output given the input value and basic block

    returns: two dicts from label to the value before the block
             and after the block.
    """

    # Initialise the algorithm
    worklist = set(graph.keys())
    ins = {}
    outs = {label: copy.deepcopy(init) for label in graph}

    # Iterate until the worklist is empty
    while worklist:
        # Get a block label from the worklist
        b = worklist.pop()

        # Calculate the input value
        if forward:
            ins[b] = merge_fn([outs[x] for x in graph[b].predecessors])
        else:
            ins[b] = merge_fn([outs[x] for x in graph[b].successors])

        # Calculate the output value
        new_outs = transfer_fn(label2block[b], ins[b])

        # If the newly calculated value has changed
        # then update the value in the map and
        # recompute for it's children
        if outs[b] != new_outs:
            outs[b] = new_outs

            if forward:
                worklist.update(graph[b].successors)
            else:
                worklist.update(graph[b].predecessors)

    if forward:
        return ins, outs
    else:
        return outs, ins


def union_sets(l):
    """
    Returns a union of the sets in the given list.
    """

    return {v for vs in l for v in vs}


def merge_dicts(l):
    """
    This merges together two dicts.
    """

    # Create the output dict
    out = {}

    # Iterate over each map in the list
    # and union the maps together by keys
    for m in l:
        for k, vs in m.items():
            if k not in out:
                out[k] = set()
            out[k].update(vs)

    # Return the result
    return out


def merge_consts(l):
    """
    Merge together a list constaining
    dicts from variable to their constant
    value and None if they don't have a const.
    """

    # Create the output dict
    out = {}

    # Iterate over each map in the list
    # and join the constants if they are the same
    for m in l:
        for k, const in m.items():
            if k not in out:
                out[k] = const
            else:
                if out[k] != const:
                    out[k] = None

    # Return the result
    return out


def get_var_defs(instrs):
    """
    Returns a dict from variable to it's definition
    that occur in this block.
    """

    return {instr["dest"]: instr for instr in instrs if "dest" in instr}


def reaching_defs(instrs, inv):
    """
    Transfer function for reaching definitions is
    out(in) = def(b) U (in - kills(b))

    This returns a set of reaching definitions
    updated with those defined in this block.
    """

    # Copy the existing value
    outv = copy.deepcopy(inv)

    # Replace the defs in the input dict
    for var, defn in get_var_defs(instrs).items():
        op = defn["op"]
        type = defn["type"]
        val = " {}".format(defn["value"]) if "value" in defn else ""
        args = "".join(" " + a for a in defn["args"]) if "args" in defn else ""
        funcs = "".join(" @" + f for f in defn["funcs"]) if "funcs" in defn else ""
        labels = "".join(" ." + l for l in defn["labels"]) if "labels" in defn else ""
        outv[var] = {"{}: {} = {}{}{}{}{};".format(var, type, op, funcs, args, labels, val)}

    # Return the updated defs
    return outv


def const_prop(instrs, inv):
    """
    Transfer function for constant propagation is
    out(in) = consts(b) U (in - kills(b))

    This returns a set of const values
    defined in this block.
    """

    # Copy the existing value
    outv = copy.deepcopy(inv)

    # Replace the defs in the input dict
    # with a constant if it's defined
    # else remove it if it's clobbered
    for instr in instrs:
        if "dest" in instr:
            dest = instr["dest"]
            if instr["op"] == "const":
                outv[dest] = instr["value"]
            else:
                outv[dest] = None

    # Return the updated defs
    return outv


def live_vars(instrs, inv):
    """
    Transfer function for live variables is
    in(out) = uses(b) U (out - kills(b))

    This returns a set of live variables
    updated with those defined in this block.
    """

    # Copy the existing value
    outv = copy.deepcopy(inv)

    # Replace the defs in the input set
    for instr in reversed(instrs):
        # If this instruction defines a variable
        # then we remove it from the live defs
        if "dest" in instr:
            outv.discard(instr["dest"])

        # We add to the defs all the variables
        # this instruction uses
        outv.update(instr["args"] if "args" in instr else [])

    # Return the updated defs
    return outv


# This tuple defines the reaching definitions analysis
REACHING_DEFS = (True, dict(), merge_dicts, reaching_defs)

# This tuple defines the constant propagation analysis
CONST_PROP = (True, dict(), merge_consts, const_prop)

# This tuple defines the live variables analysis
LIVE_VARS = (False, set(), union_sets, live_vars)


def pretty_print_defs(dicts):
    """
    Pretty print a dictionary with variables
    as keys and sets of definitions as values.
    """

    # Print the all definitions of each variable
    ds = []
    for var, defs in dicts.items():
        for defn in defs:
            ds.append(defn)

    # Return empty if the set if list is empty
    if not ds:
        return "∅"
    else:
        return "".join(sorted("\n      " + d for d in ds))


def pretty_print_set(sets):
    """
    Pretty print a dictionary with variables
    as keys and sets of definitions as values.
    """

    # Print the all definitions of each variable
    if not sets:
        return "∅"
    else:
        return ", ".join(sorted(str(x) for x in sets))


def pretty_print_consts(dicts):
    """
    Pretty print a dictionary with variables
    as keys and sets of constants.
    """

    # Print the all definitions of each variable
    if not dicts:
        return "∅"
    else:
        return ", ".join(sorted("{} = {}".format(v, "?" if c is None else c) for v, c in dicts.items()))


def main():
    # Load the program JSON
    prog = json.load(sys.stdin)

    # Read the argument and determine the relevant analysis
    analysis = "live"
    if len(sys.argv) > 1:
        analysis = sys.argv[1]

    # Choose the analysis
    if analysis == "defs":
        analysis = REACHING_DEFS
        print_fn = pretty_print_defs
    elif analysis == "const":
        analysis = CONST_PROP
        print_fn = pretty_print_consts
    else:
        analysis = LIVE_VARS
        print_fn = pretty_print_set

    # Do this for each function
    for func in prog['functions']:
        # Get the basic block and CFG for this function
        name = func["name"]
        blocks = form_blocks(func['instrs'])
        label2block = label_blocks(blocks)
        graph, label2block = get_cfg(label2block)

        # Get the results from the analysis
        before, after = data_flow_analysis(graph, label2block, *analysis)

        # Print the results
        print(f"{name}:")
        for block in graph.keys():
            print(f"  {block}:")
            print("    in: {}".format(print_fn(before[block])))
            print("    out: {}".format(print_fn(after[block])))


if __name__ == '__main__':
    main()
