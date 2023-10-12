# the compiler: gcc for C program, define as g++ for C++
CC = gcc
CXX = g++
# compiler flags:
CFLAGS  = -g -Wfatal-errors -Wpedantic -pedantic-errors -Wall -Wextra
LINKING = 
TARGET = *

all:
	$(CXX) $(CFLAGS) $(TARGET).cpp $(LINKING)

clean:
	$(RM) $(TARGET)
