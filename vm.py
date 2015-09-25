from os import *
import sys
import struct

'''The vm'''
class Vm(object):
    MAX_VALUE = 32768
    '''Vm takes a file_name to read and start executing'''
    def __init__(self, file_name):
        self.address = -1;
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

        self.fd = open(file_name, "rb")

    '''start begins reading the file'''
    def start(self):
        data = self.read()
        while data:
            self.execute(data)
            data = self.read()

    '''read reads 16 bits (2 bytes) at a time and returns the data'''
    def read(self, raw=False):
        self.address = self.address + 1
        data = self.fd.read(2)
        value = struct.unpack('H', data)[0]
        if raw:
            return value
        else:
            return self.deref(value)

    '''execute takes whatever data read and executes the appropriate instruction'''
    def execute(self, data):
        dispatch = {
            0: exit,
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
            print("Tried executing %s" % data)
            print(e)
            exit()

    ''' jumps to address number, address is converted to the byte number by multiplying by 2 since values are 16bit'''
    def jump(self, address):
        print("Old address %s new address %s" % (self.address, address))
        self.fd.seek(address * 2)
        self.address = address

    ''' if returns value of reg if looking for register'''
    def deref(self, value):
        if value >= self.MAX_VALUE:
            print("Dereferencing %s" % value)
            return self.get_reg(value)
        return value

    '''returns the value in a register for a given value'''
    def get_reg(self, reg):
        reg = reg - self.MAX_VALUE
        print("register %s" % reg)
        return self.registers.get(reg)

    '''sets the register to the value'''
    def set_reg(self, reg, value):
        reg = reg - self.MAX_VALUE
        print("setting register %s to %s" % (reg, value))
        self.registers[reg] = value

    '''stack_pop pops a value off the stack'''
    def stack_pop(self):
        return self.stack.pop()

    '''stack_push pushes a value onto the stack'''
    def stack_push(self, value):
        self.stack.append(value)

    '''set register <a> to the value of <b>'''
    def set(self):
        a = self.read(raw=True)
        b = self.read()
        print("set %s %s" % (a, b))
        self.set_reg(a, b)

    '''push <a> onto the stack'''
    def push(self):
        a = self.read()
        self.stack_push(a);
        print("push %s" % a)

    '''remove the top element from the stack and write it into <a>; empty stack = error'''
    def pop(self):
        a = self.read(raw=True)
        value = self.stack_pop();
        self.set_reg(a, value)
        print("pop %s" % a)

    '''set <a> to 1 if <b> is equal to <c>; set it to 0 otherwise'''
    def eq(self):
        a = self.read(raw=True)
        b = self.read()
        c = self.read()
        eq = b == c
        self.set_reg(a, int(eq))
        print("eq %s %s %s" % (a, b, c))

    '''set <a> to 1 if <b> is greater than <c>; set it to 0 otherwise'''
    def gt(self):
        a = self.read(raw=True)
        b = self.read()
        c = self.read()
        self.set_reg(a, int(b > c))
        print("gt %s %s %s" % (a, b, c))

    '''jump to <a>'''
    def jmp(self):
        a = self.read()
        self.jump(a)

    '''if <a> is nonzero, jump to <b>'''
    def jt(self):
        a = self.read()
        b = self.read()
        print("jt %s %s" % (a, b))
        if a != 0:
            self.jump(b)

    '''if <a> is zero, jump to <b>'''
    def jf(self):
        a = self.read()
        b = self.read()
        print("jf %s %s" % (a, b))
        if a == 0:
            self.jump(b)

    '''assign into <a> the sum of <b> and <c> (modulo 32768) '''
    def add(self):
        a = self.read(raw=True)
        b = self.read()
        c = self.read()
        sum = b + c % self.MAX_VALUE
        self.set_reg(a, sum)
        print("add %s %s %s" % (a, b, c))

    '''store into <a> the product of <b> and <c> (modulo 32768)   '''
    def mult(self):
        a = self.read()
        b = self.read()
        c = self.read()
        print("mult %s, %s, %s" % (a, b, c))

    '''store into <a> the remainder of <b> divided by <c>'''
    def mod(self):
        a = self.read()
        b = self.read()
        c = self.read()
        print("mod %s %s %s" % (a, b, c))

    '''stores into <a> the bitwise and of <b> and <c>'''
    def and_fn(self):
        a = self.read(raw=True)
        b = self.read()
        c = self.read()
        self.set_reg(a, (b & c) % self.MAX_VALUE)
        print("and %s %s %s" % (a, b, c))

    '''stores into <a> the bitwise or of <b> and <c>'''
    def or_fn(self):
        a = self.read(raw=True)
        b = self.read()
        c = self.read()
        self.set_reg(a, (b | c) % self.MAX_VALUE)
        print("or %s %s %s" % (a, b, c))

    '''stores 15-bit bitwise inverse of <b> in <a>'''
    def not_fn(self):
        a = self.read(raw=True)
        b = self.read()

        not_val = (~b & 0xFFFF) % self.MAX_VALUE
        self.set_reg(a, not_val)
        print("not %s %s" % (a, b))

    '''read memory at address <b> and write it to <a>'''
    def rmem(self):
        a = self.read()
        b = self.read()
        print("rmem %s %s" % (a, b))

    '''write the value from <b> into memory at address <a>'''
    def wmem(self):
        a = self.read()
        b = self.read()
        print("wmem %s %s" % (a, b))

    '''write the address of the next instruction to the stack and jump to <a>'''
    def call(self):
        a = self.read()
        self.stack_push(self.address + 1)

        self.jump(a)
        print("call %s" % a)

    '''remove the top element from the stack and jump to it; empty stack = halt'''
    def ret(self):
        if len(self.stack) == 0:
            exit()
        el = self.stack_pop()
        self.jump(el)
        print("ret")

    '''write the character represented by ascii code <a> to the terminal'''
    def out_fn(self):
        a = self.read()
        sys.stdout.write(chr(a))
        sys.stdout.flush()

    '''read a character from the terminal and write its ascii code to <a>; it can be assumed that once input starts, it will continue until a newline is encountered; this means that you can safely read whole lines from the keyboard and trust that they will be fully read'''
    def in_fn(self):
        a = self.read()
        print("in %s" % a);

    '''no operation'''
    def noop(self):
        print("noop")
        pass

vm = Vm("challenge.bin")
vm.start()


