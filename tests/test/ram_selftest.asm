# ram_selftest.asm — verify the CPU can ST/LD to the connected RAM.
# Used by PATCH_CPU_RAM_VALIDATION_V07.
#
# Writes a known value to a RAM address, reads it back, compares, and outputs
# "PASS" (match) or "FAIL" (mismatch) to the UART.
#
# Address choices (circuit mode: RAM 0x0000-0xFFFF, UART MMIO window 0x0100-0x0107):
#   UART base 0x0100  — same OUT method as hello.asm
#   RAM test  0x0200  — avoids the UART window and the code region (0x0000-0x005F)
#   value     0xABCD
#
# Register usage:
#   r2 = UART base, r3 = RAM test address, r4 = expected value,
#   r5 = value read back, r1 = char to OUT

    LDI r2, 0x100      # UART base
    LDI r3, 0x200      # RAM test address (outside the UART window)
    LDI r4, 0xABCD     # expected value
    ST  [r3], r4       # RAM[0x200] = 0xABCD
    LD  r5, [r3]       # read it back into r5
    BEQ r5, r4, pass   # if read-back == expected -> PASS
# FAIL path
    LDI r1, 70         # 'F'
    OUT [r2], r1
    LDI r1, 65         # 'A'
    OUT [r2], r1
    LDI r1, 73         # 'I'
    OUT [r2], r1
    LDI r1, 76         # 'L'
    OUT [r2], r1
    JMP end
pass:
    LDI r1, 80         # 'P'
    OUT [r2], r1
    LDI r1, 65         # 'A'
    OUT [r2], r1
    LDI r1, 83         # 'S'
    OUT [r2], r1
    LDI r1, 83         # 'S'
    OUT [r2], r1
end:
    HALT
