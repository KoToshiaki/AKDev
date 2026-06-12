# AKDev test program — outputs "Hello World !\n" to the UART at 0x100.
# Same instruction set / UART method as src/hello.asm (LDI + OUT per char).
# Used by PATCH_CIRCUIT_WRITE_RUN_HELLO_V05 (Write Program -> Run).

LDI r2, 0x100    # r2 = UART base address
LDI r1, 72       # 'H'
OUT [r2], r1
LDI r1, 101      # 'e'
OUT [r2], r1
LDI r1, 108      # 'l'
OUT [r2], r1
LDI r1, 108      # 'l'
OUT [r2], r1
LDI r1, 111      # 'o'
OUT [r2], r1
LDI r1, 32       # ' '
OUT [r2], r1
LDI r1, 87       # 'W'
OUT [r2], r1
LDI r1, 111      # 'o'
OUT [r2], r1
LDI r1, 114      # 'r'
OUT [r2], r1
LDI r1, 108      # 'l'
OUT [r2], r1
LDI r1, 100      # 'd'
OUT [r2], r1
LDI r1, 32       # ' '
OUT [r2], r1
LDI r1, 33       # '!'
OUT [r2], r1
LDI r1, 10       # '\n' (newline)
OUT [r2], r1
HALT
