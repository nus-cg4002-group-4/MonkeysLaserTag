import struct

test_int = []

test_float = 0.939393

test_int.append(struct.pack('i', test_float))
test_int = 2143289344



print(struct.unpack('f', test_int)[0])