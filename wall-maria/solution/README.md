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
