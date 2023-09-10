# Solution Step

## Chroot Jailbreak in Linux VM

It's Covered in `wall-sina`, so I'll skip this

## Privilege Escalation in Linux VM

Again, covered in `wall-rose`, so I'll skip this too

## Qemu VM Escape

Covered in `wall-maria`, skipped

## Seccomp Shell "Escape" → Remote Code Execution in Docker

You do have a seccomp environment. However, other processes running on this machine may not be protected by seccopm. Therefore, if you have access to other ports on the same machine, you may be able to achieve a "seccomp jailbreak" by exploiting vulnerabilities in other ports.

Of course, poking other ports is pretty cumbersome, so you can use the binary in **`the-blade`** to simplify such process

In this challenge, you can use the portscan command in `the-blade` to discover open ports. You'll soon notice that port 80 (http), and port 6379 (redis) are both open. If you wander around a little more, you'll notice that `PHP` is also enabled. Therefore, you can try out [this redis pentest technique](https://book.hacktricks.xyz/network-services-pentesting/6379-pentesting-redis#text-php-webshell) to achieve RCE as `www-data`.

## Privilege Escalation

You can use [`linpeas.sh`](https://github.com/carlospolop/PEASS-ng/tree/master/linPEAS) to look for reasonal PE vectors.

After running the script, you'll notice that in `/etc/sudoers.d/99_misc`, the user run `cowsay` and `cowthink` as `root`. Well, here's the thing: You can actually execute arbitrary code in `cowsay` and `cowthink`! (Yeah, ..., WTF)

The command `cowsay -f /tmp/script.sh x` will **EXECUTE** the file `script.sh`, retrieve its output, and display as speaking cow format. Also, cowsay does not drop evelated privileges!

To bring things together, you can actually obtain a root shell through the following command:

```sh
echo 'exec "/bin/sh -i";' > /tmp/shell.sh
cowsay -f /tmp/shell.sh x
```

See [gtfobins cowsay](https://gtfobins.github.io/gtfobins/cowsay/) for more info. 

## Final Note

Since this is a pentest challenge, the exists no attachment for this challenge.

However, if you want to play this locally after the event ends, you can access the attachment in `sample-server/the_umi.tgz` (run `docker-compose up -d --build` to start the instance).
