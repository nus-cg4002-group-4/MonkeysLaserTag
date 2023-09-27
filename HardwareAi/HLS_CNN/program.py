from pynq import Overlay, allocate
import pynq.lib.dma
import sys, os, re

def init(name, total_size, dma):
    in_buffer = allocate(shape=(total_size,), dtype=np.float32)
    p = os.path.join(cfd, 'old_values_for_testing', name)
    f = open(p, 'r')
    data = f.read().split(',')
    in_buffer[:] = data
    dma.sendchannel.transfer(in_buffer)
    dma.sendchannel.wait()

cfd = sys.path[0]

overlay = Overlay(os.path.join(cfd, 'design_1.bit'))
dma = overlay.axi_dma_0

# Init
print('Initializing...')

constants = {}
with open(os.path.join(cfd, 'old_values_for_testing', 'CNN.h')) as infile:
    for line in infile:
        for name, value in re.findall(r'#define\s+(\w+)\s+(.*)', line):
            try:
                constants[name] = value
            except Exception as e:
                pass # maybe log something
print(constants)

init('conv1_weights.txt', int(constants['CONV1LENGTH']) * int(constants['CONV1AXES']) * int(constants['CONV1FILTERS']), dma)
init('conv1_biases.txt', int(constants['CONV1FILTERS']), dma)
init('conv2_weights.txt', int(constants['CONV2LENGTH']) * int(constants['CONV2AXES']) * int(constants['CONV2FILTERS']), dma)
init('conv2_biases.txt', int(constants['CONV2FILTERS']), dma)
init('dense1_weights.txt', int(constants['DENSE1LENGTH']) * int(constants['DENSE1AXES']), dma)
init('dense1_biases.txt', int(constants['DENSE1AXES']), dma)
init('dense2_weights.txt', int(constants['DENSE2LENGTH']) * int(constants['DENSE2AXES']), dma)
init('dense2_biases.txt', int(constants['DENSE2AXES']), dma)

print('Initialization done. Starting tests')

# Begin tests
# in_buffer = allocate(shape=(240,), dtype=np.float32)
out_buffer = allocate(shape=(2,), dtype=np.uint32)

for file in os.listdir(cfd):
    if file.endswith(".in"):
        print('Testing file', file)
        init(file, int(constants['INPUTLENGTH']) * int(constants['INPUTAXES']), dma)
        dma.recvchannel.transfer(out_buffer)
        dma.recvchannel.wait()
        print('Output:', out_buffer)
