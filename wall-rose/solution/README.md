# Solution

## Vulnerability

According to the source code, when `/dev/rose` is opened, `rose_open` will be invoked. Similarly, when `/dev/rose` is closed, `rose_release` will be called.

```c
static int rose_open(struct inode *inode, struct file *file) {
    data = kmalloc(MAX_DATA_HEIGHT, GFP_KERNEL);
    if (!data) {
        printk(KERN_ERR "Wall Rose: kmalloc error\n");
        return -1;
    }
    memset(data, 0, MAX_DATA_HEIGHT);
    return 0;
}

static int rose_release(struct inode *inode, struct file *file) {
    kfree(data);
    return 0;
}
```

Observer that in `rose_open`, a chunk of 0x400 is allocated, and in `rose_close`, the chunk is freed. The problem is that neither of these two functions are locked with mutex.

As a result, when you open two devices (one called `fd1`, another one called `fd2`), the 'data' pointer will store the chunk allocated by the later `open` call. However, if `fd1` and `fd2` are both closed, `data` will be freed twice, leading to double free error.

## Caveats

In order to exploit a double-freed block as an exploitable vector, you may need to implement arbitrary read/writes on the block. Unfortunately, no read/write is implemented on "rose.ko"

The solution is to leverage other kernel data structures that allow arbitrary read / write to chunk. For example, the `msg_msg` structure is a perfect candidate because it allows you to read / write arbitrary data at `chunk + 0x48`, and its chunk size ranges from 0x31 to 0x400.

In addition to `msg_msg`, you can also overlap `data` with a `pipe_buffer` structure. This structure is mainly used when calling pipe-related operations. What's interesting is that there exists a flag called `PIPE_BUF_CAN_MERGE` in this structure: If you create a pipe, when the destination file was not opened with `O_DIRECT` and the most recent write is incomplete, the following writes must then append to the file rather than overwriting it. The `PIPE_BUF_CAN_MERGE` exists for exactly this purpose! If it is set to 1, any data received from the pipe will be appended to the destination file.

## Exploitation

So here's an idea: You can create a pipe with `out_fd` equals to the file descriptor of "/etc/passwd". Initially, it's apparent that you do not have the permission to write any data to it. However, if you manage to 

I won't go into the underlying C code here, since it requires plenty of pages. [This article](https://0x434b.dev/learning-linux-kernel-exploitation-part-2-cve-2022-0847/) explains it very well. 

The overall steps of exploitation is as follows

1. Open "/etc/passwd" and a pipe.
2. Splice the fd of "/etc/passwd" with your pipe (`splice(passwd_fd, &offset, pipefd[1], NULL, 1, 0)`)
    - `splice` is a function that allows you to transfers data directly between two file descriptors without touching the kernel address
2. Set the `PIPE_BUF_CAN_MERGE` to 1 using double free error
3. Write root record (`root::0:0::/root:/bin/bash`) to `"/etc/passwd"`
4. `su root`
