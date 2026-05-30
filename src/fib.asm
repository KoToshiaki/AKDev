# fib.asm — Fibonacci sequence (first 8 terms) stored to RAM
# Demonstrates: ADD / ST / ADDI / BEQ / JMP
#
# Register usage:
#   r1 = a (fib[n-2])
#   r2 = b (fib[n-1])
#   r3 = tmp
#   r4 = write ptr (byte address into RAM data area)
#   r5 = count
#   r6 = limit (8)
#
# RAM layout (base 0x0000, size 256 bytes):
#   0x0000-0x0037  program (14 instructions)
#   0x0040-0x005F  data: fib[0..7] as 32-bit little-endian words
#
# After HALT: RAM[0x0040..0x005C] = 0, 1, 1, 2, 3, 5, 8, 13

    LDI r1, 0       # a = 0
    LDI r2, 1       # b = 1
    LDI r4, 0x0040  # write ptr = data area start
    LDI r5, 0       # count = 0
    LDI r6, 8       # limit = 8
loop:
    ST [r4], r1     # RAM[addr] = a
    ADD r3, r1, r2  # tmp = a + b
    ADD r1, r2, r0  # a = b  (r0 is always 0)
    ADD r2, r3, r0  # b = tmp
    ADDI r4, r4, 4  # addr += 4
    ADDI r5, r5, 1  # count++
    BEQ r5, r6, end # if count == 8: goto end
    JMP loop
end:
    HALT
