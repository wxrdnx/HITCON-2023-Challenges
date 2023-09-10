def decode(mapped_flag):
    shuffled_flag = []
    for i in range(len(mapped_flag)):
        byte = ((mapped_flag[i] ^ 137) - 113 + 256) % 256
        shuffled_flag.append(pow(256 if byte == 0 else byte, -1, 257) - 1)
    reverse_shuffle = [61, 46, 51, 26, 39, 58, 15, 17, 62, 54, 38, 37, 7, 30, 21, 1, 41, 28, 14, 42, 48, 3, 63, 44, 12, 23, 5, 19, 22, 33, 56, 43, 29, 45, 55, 57, 32, 59, 8, 16, 50, 27, 35, 0, 52, 18, 49, 25, 11, 10, 24, 6, 47, 13, 53, 34, 40, 2, 31, 60, 9, 36, 4, 20]
    flag = []
    for i in reverse_shuffle:
        flag.append(shuffled_flag[i])
    return flag
elf_magic = 0x464c457f
root_magic = 0x746f6f72
zero_magic = (0xffffffffffffffff >> 29) // 41
flag_num_encoded = [
        0x526851a7,
        0x31ff2785,
        0xc7d28788,
        0x523f23d3,
        0xaf1f1055,
        0x5c94f027,
        0x797a3fcd,
        0xe7f02f9f,
        0x3c86f045,
        0x6deab0f9,
        0x91f74290,
        0x7c9a3aed,
        0xdc846b01,
        0x0743c86c,
        0xdff7085c,
        0xa4aee3eb,
        ]

flag = b''
for cipher in flag_num_encoded:
    cipher = cipher ^ zero_magic
    cipher = (~cipher) % 0x100000000
    cipher = ((cipher >> 21) | (cipher << 11)) & 0xffffffff
    cipher = ((cipher ^ root_magic) - elf_magic + 0x100000000) & 0xffffffff
    flag += cipher.to_bytes(4, 'little')
flag = list(flag)
for i in range(256):
    flag = decode(flag)
flag = bytes(flag)

print(flag)
