#!/usr/bin/python3
import os
import sys
import struct
import logging
import threading
import queue
import traceback
import logging.handlers as handlers
import pickle

memory = logging.getLogger()
fileHandler = logging.FileHandler('instructions.log')
memoryHandler = handlers.MemoryHandler(1024*1000, logging.DEBUG, target=fileHandler)
memory.addHandler(memoryHandler)
memory.setLevel(logging.DEBUG)
'''The vm'''
class Vm(object):
    MAX_VALUE = 32768


    '''Vm takes a file_name to read and start executing'''
    def __init__(self, file_name, q):
        self.names = {
            0: 'halt',
            1: 'set',
            2: 'push',
            3: 'pop',
            4: 'eq',
            5: 'gt',
            6: 'jmp',
            7: 'jt',
            8: 'jf',
            9: 'add',
            10: 'mult',
            11: 'mod',
            12: 'and_fn',
            13: 'or_fn',
            14: 'not_fn',
            15: 'rmem',
            16: 'wmem',
            17: 'call',
            18: 'ret',
            19: 'out_fn',
            20: 'in_fn',
            21: 'noop'
            }
        self.address = 0;
        self.stack = []
        self.registers = {
                0: 0,
                1: 0,
                2: 0,
                3: 0,
                4: 0,
                5: 0,
                6: 0,
                7: 0,
                }
        self.memory = {}
        self.q = q

        if os.path.isfile('save.pickle'):
            self.import_state()
        else:
            fd = open(file_name, 'rb')
            word = fd.read(2)
            i = 0
            while word:
                data = struct.unpack("H", word)[0]
                self.memory[i] = data
                word = fd.read(2)
                i = i + 1

    '''start begins reading the file'''
    def start(self):
        (data, data_val) = self.read()
        while data:

            self.execute(data)
            (data, data_val) = self.read()

    '''read reads 16 bits (2 bytes) at a time and returns the data'''
    def read(self):
        if self.address == 5511:
            # Jump to return value
            self.address = 5513
            self.registers[7] = 25734 # calculated by algo.go
            self.registers[0] = 6 # r0 check after 6049 sub routine in the vm
        value = self.memory[self.address]
        self.address = self.address + 1
        return (value, self.deref(value))

    '''execute takes whatever data read and executes the appropriate instruction'''
    def execute(self, data):
        dispatch = {
            0: self.halt,
            1: self.set,
            2: self.push,
            3: self.pop,
            4: self.eq,
            5: self.gt,
            6: self.jmp,
            7: self.jt,
            8: self.jf,
            9: self.add,
            10: self.mult,
            11: self.mod,
            12: self.and_fn,
            13: self.or_fn,
            14: self.not_fn,
            15: self.rmem,
            16: self.wmem,
            17: self.call,
            18: self.ret,
            19: self.out_fn,
            20: self.in_fn,
            21: self.noop
            }

        try:
            memory.debug("%s: Op Code %s" % (self.address - 1, self.names.get(data)))
            dispatch.get(int(data))()
        except TypeError as e:
            memory.debug("Tried executing %s" % data)
            memory.debug(e)
            exit()

    '''imports the state of a machine'''
    def import_state(self):
        with open('save.pickle', 'rb') as fd:
            state = pickle.load(fd)
            self.address = state[0]
            self.registers = state[1]
            self.stack = state[2]
            self.memory = state[3]

    '''exports the state of the machine'''
    def export_state(self):
        with open('save.pickle', 'wb') as fd:
            pickle.dump((self.address, self.registers, self.stack, self.memory), fd)

    def set_stack(self, ind, val):
        self.stack[ind] = val

    '''send a debug message'''
    def debug(self, message):
        memory.debug("%s" % message)

    ''' jumps to address number, address is converted to the byte number by multiplying by 2 since values are 16bit'''
    def jump(self, address):
        self.address = address

    ''' if returns value of reg if looking for register'''
    def deref(self, value):
        if value >= self.MAX_VALUE:
            return self.get_reg(value)
        return value

    '''returns the value in a register for a given value'''
    def get_reg(self, reg):
        reg = reg - self.MAX_VALUE
        return self.registers.get(reg)

    '''sets the register to the value'''
    def set_reg(self, reg, value):
        reg = reg - self.MAX_VALUE
        self.registers[reg] = value

    '''halt, exit'''
    def halt(self):
        self.debug("halt")
        exit()

    '''set register <a> to the value of <b>'''
    def set(self):
        (a, a_val) = self.read()
        (b, b_val) = self.read()
        self.debug("set %s<%s> %s<%s>" % (a, a_val, b, b_val))
        self.set_reg(a, b_val)

    '''push <a> onto the stack'''
    def push(self):
        (a, a_val) = self.read()
        self.stack.append(a_val);
        self.debug("push %s<%s>" % (a, a_val))
        self.debug(self.stack);

    '''remove the top element from the stack and write it into <a>; empty stack = error'''
    def pop(self):
        (a, a_val) = self.read()
        value = self.stack.pop();
        self.set_reg(a, value)
        self.debug("pop %s (value popped %s))" % (a, value))
        self.debug(self.stack);

    '''set <a> to 1 if <b> is equal to <c>; set it to 0 otherwise'''
    def eq(self):
        (a, a_val) = self.read()
        (b, b_val) = self.read()
        (c, c_val) = self.read()
        eq = b_val == c_val
        self.set_reg(a, int(eq))
        self.debug("eq %s %s<%s> %s<%s>" % (a, b, b_val, c, c_val))

    '''set <a> to 1 if <b> is greater than <c>; set it to 0 otherwise'''
    def gt(self):
        (a, a_val) = self.read()
        (b, b_val) = self.read()
        (c, c_val) = self.read()
        self.set_reg(a, int(b_val > c_val))
        self.debug("gt %s %s<%s> %s<%s>" % (a, b, b_val, c, c_val))

    '''jump to <a>'''
    def jmp(self):
        (a, a_val) = self.read()
        self.debug("jmp %s<%s>" % (a, a_val))
        self.jump(a_val)

    '''if <a> is nonzero, jump to <b>'''
    def jt(self):
        (a, a_val) = self.read()
        (b, b_val) = self.read()
        self.debug("jt %s<%s> %s<%s>" % (a, a_val, b, b_val))
        if a_val != 0:
            self.jump(b_val)

    '''if <a> is zero, jump to <b>'''
    def jf(self):
        (a, a_val) = self.read()
        (b, b_val) = self.read()
        self.debug("jf %s<%s> %s<%s>" % (a, a_val, b, b_val))
        if a_val == 0:
            self.jump(b_val)

    '''assign into <a> the sum of <b> and <c> (modulo 32768) '''
    def add(self):
        (a, a_val) = self.read()
        (b, b_val) = self.read()
        (c, c_val) = self.read()
        sum = (b_val + c_val) % self.MAX_VALUE
        self.set_reg(a, sum)
        self.debug("add %s %s<%s> %s<%s>" % (a, b, b_val, c, c_val))

    '''store into <a> the product of <b> and <c> (modulo 32768)   '''
    def mult(self):
        (a, a_val) = self.read()
        (b, b_val) = self.read()
        (c, c_val) = self.read()
        product = (b_val * c_val) % self.MAX_VALUE
        self.set_reg(a, product)
        self.debug("mult %s %s<%s> %s<%s> (product %s)" % (a, b, b_val, c, c_val, product))

    '''store into <a> the remainder of <b> divided by <c>'''
    def mod(self):
        (a, a_val) = self.read()
        (b, b_val) = self.read()
        (c, c_val) = self.read()
        mod = b_val % c_val
        self.set_reg(a, mod)
        self.debug("mod %s %s<%s> %s<%s>" % (a, b, b_val, c, c_val))

    '''stores into <a> the bitwise and of <b> and <c>'''
    def and_fn(self):
        (a, a_val) = self.read()
        (b, b_val) = self.read()
        (c, c_val) = self.read()
        self.set_reg(a, (b_val & c_val) % self.MAX_VALUE)
        self.debug("and %s %s<%s> %s<%s>" % (a, b, b_val, c, c_val))

    '''stores into <a> the bitwise or of <b> and <c>'''
    def or_fn(self):
        (a, a_val) = self.read()
        (b, b_val) = self.read()
        (c, c_val) = self.read()
        self.set_reg(a, (b_val | c_val) % self.MAX_VALUE)
        self.debug("or %s %s<%s> %s<%s>" % (a, b, b_val, c, c_val))

    '''stores 15-bit bitwise inverse of <b> in <a>'''
    def not_fn(self):
        (a, a_val) = self.read()
        (b, b_val) = self.read()

        not_val = (~b_val & 0xFFFF) % self.MAX_VALUE
        self.set_reg(a, not_val)
        self.debug("not %s %s<%s>" % (a, b, b_val))

    '''read memory at address <b> and write it to <a>'''
    def rmem(self):
        (a, a_val) = self.read()
        (b, b_val) = self.read()
        self.set_reg(a, self.memory[b_val])

        self.debug("rmem %s %s<%s>" % (a, b, b_val))

    '''write the value from <b> into memory at address <a>'''
    def wmem(self):
        (a, a_val) = self.read()
        (b, b_val) = self.read()
        self.memory[a_val] = b_val
        self.debug("wmem %s<%s> %s<%s>" % (a, a_val, b, b_val))

    '''write the address of the next instruction to the stack and jump to <a>'''
    def call(self):
        (a, a_val) = self.read()
        self.stack.append(self.address)

        self.debug("call %s<%s>" % (a, a_val))

        self.jump(a_val)

    '''remove the top element from the stack and jump to it; empty stack = halt'''
    def ret(self):
        if len(self.stack) == 0:
            self.debug("exiting due to empty stack in ret")
            exit()
        el = self.stack.pop()
        self.debug("ret %s" % el)
        self.jump(el)

    '''write the character represented by ascii code <a> to the terminal'''
    def out_fn(self):
        (a, a_val) = self.read()
        self.debug("out %s<%s>" % (a, chr(a_val)));
        sys.stdout.write(chr(a_val))
        sys.stdout.flush()

    '''read a character from the terminal and write its ascii code to <a>; it can be assumed that once input starts, it will continue until a newline is encountered; this means that you can safely read whole lines from the keyboard and trust that they will be fully read'''
    def in_fn(self):
        (a, a_val) = self.read()
        user_input = self.q.get()
        self.set_reg(a, ord(user_input))
        self.debug("in %s" % a);

    '''no operation'''
    def noop(self):
        self.debug("noop")
        pass

class tooling(object):
    def __init__(self):
        self.q = queue.Queue()
        self.vm = None
        self.vm_thread = None
        self.commands = {
                'help': self.help,
                'start': self.start,
                'save': self.save,
                'exit': self.exit,
                'status': self.status,
                'send': self.send,
                'hack': self.hack,
                'registers': self.registers,
                'jump': self.jump,
                'exec': self.exec,
                }

    def welcome(self):
        print("Welcome to the Synacor Challenge tool. Type help or enter command.")

    def help(self, c=None):
        print("""Available commands:
    help: This dialog
    start: Start the VM.
    save: Save the state of the VM.
    status: Is the VM running or not
    send: send the string following to the vm. e.g. send take tablet
    hack: set a register to a value. e.g. hack 8 1337
    registers: print out the registers
    jump: jump to a code line
    exec: execute arbitrary code
    exit: Exit.""")

    def start(self, c):
        if self.vm:
            print("Already started")
        else:
            print("Starting Vm")
            self.vm = Vm("challenge.bin", self.q)
            self.vm_thread = threading.Thread(target=self.vm.start)
            self.vm_thread.start()

    def save(self, c):
        self.vm.export_state()

    def status(self, c):
        if self.vm:
            print ("VM is running")
        else:
            print("No VM running. Type start to start one")

    def exit(self, c):
        print("Goodbye")
        exit()

    def running(self, c):
        if self.vm:
            return True
        return False

    def send(self, command):
        command = command + "\n"
        for i in command:
            self.q.put(i)

    def hack(self, command):
        try:
            reg, val = command.split(' ')
            if self.vm:
                self.vm.set_reg(int(reg)+self.vm.MAX_VALUE, int(val))
        except ValueError:
            return

    def registers(self, command):
        if self.vm:
            print(self.vm.registers)
            print(self.vm.stack)

    def jump(self, command):
        if self.vm:
            print("Jumping to %s" % command)
            self.vm.jump(int(command))

    def exec(self, command):
        try:
            eval(command)
        except Exception as e:
            print(e)
            print(traceback.format_exc())


    def loop(self):
        command = input(">")
        try:
            separator = command.index(' ')
            instruction = command[:separator]
            rest = command[separator + 1:]
        except ValueError:
            instruction = command
            rest = None
        while command:
            try:
                separator = command.index(' ')
                instruction = command[:separator]
                rest = command[separator + 1:]
            except ValueError:
                instruction = command
                rest = None
            try:
                self.commands.get(instruction)(rest)
            except TypeError as e:
                print("Beware of grues")
                self.help()
            try:
                command = input(">")
            except ValueError as e:
                print(e)
                print(traceback.format_exc())
        self.exit(None)

tool = tooling()
tool.welcome()
tool.loop()
