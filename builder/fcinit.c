// Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
// Init wrapper for boot timing. It points at /sbin/init.

#include <unistd.h>

#define MAGIC_VALUE_SIGNAL_GUEST_BOOT_COMPLETE 123

#include <sys/io.h>

#define MAGIC_IOPORT_SIGNAL_GUEST_BOOT_COMPLETE 0x03f0

static __inline void boot_done(void)
{
    iopl(3);
    outb_p(MAGIC_VALUE_SIGNAL_GUEST_BOOT_COMPLETE, MAGIC_IOPORT_SIGNAL_GUEST_BOOT_COMPLETE);
}

int main(int argc, char* const argv[])
{
    boot_done();
    return 0;
}
