import json
import sys

TERMINATORS = 'jmp', 'br', 'ret'

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
        swap_add_and_subtract(fun['instrs'])

    print(json.dumps(prog, indent=4))

if __name__ == '__main__':
    main()
