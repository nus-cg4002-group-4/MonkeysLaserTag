# the compiler: gcc for C program, define as g++ for C++
CC = gcc
CXX = g++
# compiler flags:
CFLAGS  = -g -Wfatal-errors -Werror -Wpedantic -pedantic-errors -Wall -Wextra
LINKING = 
TARGET = *

all:
	$(CXX) $(CFLAGS) -o out $(TARGET).cpp $(LINKING)

clean:
	$(RM) $(TARGET)
