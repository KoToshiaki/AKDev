# AKDev v0.1 hello world
# Outputs "Hi" to UART at 0x0100

LDI r2, 0x100    # r2 = UART base address
LDI r1, 72       # r1 = 'H' (ASCII 72)
OUT [r2], r1     # send 'H'
LDI r1, 105      # r1 = 'i' (ASCII 105)
OUT [r2], r1     # send 'i'
HALT
