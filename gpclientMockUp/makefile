# Makefile for the lockfile program

# Compiler
CC = gcc

# Compiler flags
CFLAGS = -Wall -Wextra

# Source and target files
SRC = gpclientMockUp.c
TARGET = gpclientMockup

# Default target
all: $(TARGET)

# Build target
$(TARGET): $(SRC)
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC)

# Clean target
clean:
	rm -f $(TARGET)


.PHONY: all clean run
