from os import *
import sys
import struct
import logging
import threading
import queue
import traceback
import logging.handlers as handlers
memory = logging.getLogger()
fileHandler = logging.FileHandler('instructions.log')
memoryHandler = handlers.MemoryHandler(1024*100, logging.DEBUG, target=fileHandler)
memory.addHandler(memoryHandler)
memory.setLevel(logging.DEBUG)
'''The vm'''
class Vm(object):
    MAX_VALUE = 32768

    '''Vm takes a file_name to read and start executing'''
    def __init__(self, file_name, q):
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

        if path.isfile('save.pickle'):
            self.import_state()
        else:
            fd = open(file_name, "rb")
            word = fd.read(2)
            i = 0
            while word:
                data = struct.unpack("H", word)[0]
                self.memory[i] = data
                word = fd.read(2)
                i = i + 1

    '''start begins reading the file'''
    def start(self):
        data = self.read()
        while data:
            self.execute(data)
            data = self.read()

    '''read reads 16 bits (2 bytes) at a time and returns the data'''
    def read(self, raw=False):
        value = self.memory[self.address]
        self.address = self.address + 1
        if raw:
            return value
        else:
            return self.deref(value)

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
        loggin.debug("halt")
        exit()

    '''set register <a> to the value of <b>'''
    def set(self):
        a = self.read(raw=True)
        b = self.read()
        memory.debug("set %s %s" % (a, b))
        self.set_reg(a, b)

    '''push <a> onto the stack'''
    def push(self):
        a = self.read()
        self.stack.append(a);
        memory.debug("push %s" % a)

    '''remove the top element from the stack and write it into <a>; empty stack = error'''
    def pop(self):
        a = self.read(raw=True)
        value = self.stack.pop();
        self.set_reg(a, value)
        memory.debug("pop %s" % a)

    '''set <a> to 1 if <b> is equal to <c>; set it to 0 otherwise'''
    def eq(self):
        a = self.read(raw=True)
        b = self.read()
        c = self.read()
        eq = b == c
        self.set_reg(a, int(eq))
        memory.debug("eq %s %s %s" % (a, b, c))

    '''set <a> to 1 if <b> is greater than <c>; set it to 0 otherwise'''
    def gt(self):
        a = self.read(raw=True)
        b = self.read()
        c = self.read()
        self.set_reg(a, int(b > c))
        memory.debug("gt %s %s %s" % (a, b, c))

    '''jump to <a>'''
    def jmp(self):
        a = self.read()
        self.jump(a)

    '''if <a> is nonzero, jump to <b>'''
    def jt(self):
        a = self.read()
        b = self.read()
        memory.debug("jt %s %s" % (a, b))
        if a != 0:
            self.jump(b)

    '''if <a> is zero, jump to <b>'''
    def jf(self):
        a = self.read()
        b = self.read()
        memory.debug("jf %s %s" % (a, b))
        if a == 0:
            self.jump(b)

    '''assign into <a> the sum of <b> and <c> (modulo 32768) '''
    def add(self):
        a = self.read(raw=True)
        b = self.read()
        c = self.read()
        sum = (b + c) % self.MAX_VALUE
        self.set_reg(a, sum)
        memory.debug("add %s %s %s" % (a, b, c))

    '''store into <a> the product of <b> and <c> (modulo 32768)   '''
    def mult(self):
        a = self.read(raw=True)
        b = self.read()
        c = self.read()
        product = (b * c) % self.MAX_VALUE
        self.set_reg(a, product)
        memory.debug("mult %s, %s, %s" % (a, b, c))
        memory.debug("product %s" % product)

    '''store into <a> the remainder of <b> divided by <c>'''
    def mod(self):
        a = self.read(raw=True)
        b = self.read()
        c = self.read()
        mod = b % c
        self.set_reg(a, mod)
        memory.debug("mod %s %s %s" % (a, b, c))

    '''stores into <a> the bitwise and of <b> and <c>'''
    def and_fn(self):
        a = self.read(raw=True)
        b = self.read()
        c = self.read()
        self.set_reg(a, (b & c) % self.MAX_VALUE)
        memory.debug("and %s %s %s" % (a, b, c))

    '''stores into <a> the bitwise or of <b> and <c>'''
    def or_fn(self):
        a = self.read(raw=True)
        b = self.read()
        c = self.read()
        self.set_reg(a, (b | c) % self.MAX_VALUE)
        memory.debug("or %s %s %s" % (a, b, c))

    '''stores 15-bit bitwise inverse of <b> in <a>'''
    def not_fn(self):
        a = self.read(raw=True)
        b = self.read()

        not_val = (~b & 0xFFFF) % self.MAX_VALUE
        self.set_reg(a, not_val)
        memory.debug("not %s %s" % (a, b))

    '''read memory at address <b> and write it to <a>'''
    def rmem(self):
        a = self.read(raw=True)
        b = self.read()
        self.set_reg(a, self.memory[b])

        memory.debug("rmem %s %s" % (a, b))

    '''write the value from <b> into memory at address <a>'''
    def wmem(self):
        a = self.read()
        b = self.read()
        self.memory[a] = b
        memory.debug("wmem %s %s" % (a, b))

    '''write the address of the next instruction to the stack and jump to <a>'''
    def call(self):
        a = self.read()
        self.stack.append(self.address)

        self.jump(a)
        memory.debug("call %s" % a)

    '''remove the top element from the stack and jump to it; empty stack = halt'''
    def ret(self):
        if len(self.stack) == 0:
            exit()
        el = self.stack.pop()
        self.jump(el)
        memory.debug("ret")

    '''write the character represented by ascii code <a> to the terminal'''
    def out_fn(self):
        a = self.read()
        sys.stdout.write(chr(a))
        sys.stdout.flush()

    '''read a character from the terminal and write its ascii code to <a>; it can be assumed that once input starts, it will continue until a newline is encountered; this means that you can safely read whole lines from the keyboard and trust that they will be fully read'''
    def in_fn(self):
        a = self.read(raw=True)
        user_input = self.q.get()
        self.set_reg(a, ord(user_input))
        memory.debug("in %s" % a);

    '''no operation'''
    def noop(self):
        memory.debug("noop")
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
                }

    def welcome(self):
        print("Welcome to the Synacor Challenge tool. Type help or enter command.")

    def help(self, c):
        print("""Available commands:
    help: This dialog
    start: Start the VM.
    save: Save the state of the VM.
    put: Send data to the VM, everything after put is sent
    status: Is the VM running or not
    exit: Exit.""")

    def start(self, c):
        print("Starting VM")
        if self.vm:
            print("Starting existing")
            self.vm_thread = threading.Thread(target=self.vm.start)
        else:
            print("Starting new")
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
        if self.vm_thread:
            self.q.task_done()
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
                print(e)
                print(traceback.format_exc())
                print("Beware of grues")
            command = input(">")
        self.exit(None)

tool = tooling()
tool.welcome()
tool.loop()
