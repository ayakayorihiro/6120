from make_cfg import *
from dom import *
import copy
import json


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
    print(loop)
    return loop

def find_loops(graph, initial_node, dominator_map):
    for vertex in graph:        # current node
        successors = graph[vertex].successors
        v_dominators = dominator_map[vertex]
        for succ in successors:
            if succ in v_dominators:
                print("back edge! " + vertex + " -> " + succ)
                find_natural_loop_from_backedge(graph, succ, vertex)

def main():
    # Load the program JSON
    prog = json.load(sys.stdin)
    for func in prog['functions']:
        # Get the basic block and CFG for this function
        blocks = form_blocks(func['instrs'])
        label2block = label_blocks(blocks)
        graph, new_label2block = get_cfg(label2block)
        initial_node = label2block[0][0]
        dominators = find_dominators(graph, initial_node)
        find_loops(graph, initial_node, dominators)


if __name__ == '__main__':
    main()
