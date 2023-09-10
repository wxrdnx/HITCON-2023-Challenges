# Solution

## Vulnerability

Format String Bug :)

## Caveats

You can only `printf` once, so there must be a way to make it loop!

The intended solution is to use the `_dl_fini` function to control the program flow. The `_dl_fini` function will be called once the program exits, and during the initialization of the linker, a linkmap address will be left on the stack.

![](https://hackmd.io/_uploads/H1Iozs5An.png)

The [`_dl_fini` function](https://elixir.bootlin.com/glibc/glibc-2.35/source/elf/dl-fini.c#L134) is as follows:

```c
...
		      if (l->l_info[DT_FINI_ARRAY] != NULL)
			{
			  ElfW(Addr) *array =
			    (ElfW(Addr) *) (l->l_addr
					    + l->l_info[DT_FINI_ARRAY]->d_un.d_ptr);
			  unsigned int i = (l->l_info[DT_FINI_ARRAYSZ]->d_un.d_val
					    / sizeof (ElfW(Addr)));
			  while (i-- > 0)
			    ((fini_t) array[i]) ();
			}
...
```

Note that `linkmap->l_info` is basically `*(&linkmap + 0)`, so changing the byte at `&linkmap` is essentially changing the address of `linkmap->l_info`. If `linkmap->l_info` is shifted by x bytes, then the offset of `FINI_ARRAY` (`l->l_info[DT_FINI_ARRAY]`) will also be shifted by x bytes. Accordingly, if there exists an address `addr` that you want to jump to after shifting x bytes from `FINI_ARRAY`, you can actually **call `addr`**.

In this challenge, I intentionally put a main address near `FINI_ARRAY`, so by changing the byte at `&linkmap` to `8`, you can actually invoke `main` again!
 
## Exploitation

The rest is pretty boring: format string bug on non-stack variables. [This article](https://anee.me/format-string-exploits-when-buffer-is-not-on-the-stack-f7c83e1a6781) explains the concept pretty well. If you are not familiar with doing FSB on non-stack variables, check it out!

## Jail Escape

The binary `sina` has `CAP_SYS_CHROOT` privilege, this means that `sina` allows you to invoke the `chroot` syscall. Therefore, you can

1. Create a new directory called `foo`
2. `chroot` the directory to `foo`. Your new root becomes `/home/user/jail/home/user/foo`.
3. Change directory to `..` many times to reach `/`
4. `chroot` to `.`. Now, your new root becomes `/`. Hurray! You've escaped the chroot jail!

## Final Note

I don't know why format string errors are everywhere in CTF, even though it's been officially dead for decades. So ... I've created another one :), to prove that it's still alive ... no ... to prove that it is ... dead ... nope ... not yet dead ... (?
