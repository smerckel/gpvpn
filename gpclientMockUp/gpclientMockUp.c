#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

#define LOCK_FILE "/tmp/gpclient.lock"

void signal_handler(int sig) {
    if (sig == SIGTERM) {
        // Remove the lock file before exiting
        unlink(LOCK_FILE);
        printf("Lock file removed. Exiting...\n");
        exit(0);
    }
}

int main() {
    // Create a lock file
    int fd = open(LOCK_FILE, O_CREAT | O_EXCL | O_WRONLY, 0644);
    if (fd < 0) {
        perror("Could not create lock file");
        return EXIT_FAILURE;
    }

    // Write the PID to the lock file
    pid_t pid = getpid();
    dprintf(fd, "%d\n", pid);
    close(fd);
    // Register sigterm handler
    signal(SIGTERM, signal_handler);

    printf("Lock file created: %s with PID: %d\n", LOCK_FILE, getpid());

    // Loop for 30 seconds. This should be enough for tests, and we don't get
    // lingering applications.
    sleep(30);
    

    // Cleanup (not reachable, but good practice)

    unlink(LOCK_FILE);
    
    return EXIT_SUCCESS;
}
