#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <getopt.h>

#define LOCK_FILE "/tmp/gpclient.lock"


// Define the expected option
static struct option long_options[] = {
  {"cookie-on-stdin", no_argument, 0, 'c'},
  {"timeout", required_argument, 0, 't'},
  {0, 0, 0, 0}
};


void signal_handler(int sig) {
    if (sig == SIGTERM) {
        // Remove the lock file before exiting
        unlink(LOCK_FILE);
        printf("Lock file removed. Exiting...\n");
        exit(0);
    }
}

int main(int argc, char *argv[]) {
  // Check for command line options to contain cookie-on-stdin
  int opt;
  int cookie_on_stdin_present = 0;
  int timeout = 30;
  while ((opt = getopt_long(argc, argv, "c", long_options, NULL)) != -1) {
    switch (opt) {
    case 'c':
      cookie_on_stdin_present = 1;
      break;
    case 't':
      timeout = atoi(optarg);
      break;
    }
  }
  
  if (cookie_on_stdin_present){
    // read all there is from stdin
    char buffer[256];
    if (fgets(buffer, sizeof(buffer), stdin) != NULL) {
      fprintf(stderr, "Received: %s", buffer);
    }
  }
  
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
  
  fprintf(stderr, "Lock file created: %s with PID: %d\n", LOCK_FILE, getpid());
  
  // Loop for some seconds. This should be enough for tests, and we don't get
  // lingering applications.
  fprintf(stderr, "Simulating %d seconds of work...", timeout);
  sleep(timeout);
  
  unlink(LOCK_FILE);
  fprintf(stderr, "Removing lockfile and exiting.");
  return EXIT_SUCCESS;
}

