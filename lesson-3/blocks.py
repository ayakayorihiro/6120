import json
import sys

TERMINATORS = 'jmp', 'br', 'ret'

def form_blocks(body):
    cur_block = []
    for instr in body:
        if 'op' in instr:       # an actual implementation
            cur_block.append(instr)
            # check for terminator
            if instr['op'] in TERMINATORS:
                yield cur_block
                cur_block = []
        else:
            yield cur_block
            cur_block = [instr]
    yield cur_block
