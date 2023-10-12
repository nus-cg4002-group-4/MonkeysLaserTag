from pynq import Overlay, allocate
import sys, os, re, time
import numpy as np

cfd = sys.path[0]

print('Loading overlay...')
overlay = Overlay(os.path.join(cfd, 'design_1_wrapper.bit'))
dma = overlay.axi_dma_0
print('Overlay loaded.')

# Begin tests

dir = os.path.join(cfd, 'test_values')

for file in os.listdir(dir):
    if file.endswith(".in"):
        print('Testing file', file)
        f = open(os.path.join(dir, file), 'r')
        data = f.read().split(',')

        start_time = time.time()
        in_buffer = allocate(shape=(560,), dtype=np.float32)
        out_buffer = allocate(shape=(1,), dtype=np.int32)
        in_buffer[:] = np.array(data).astype(np.float32)

        dma.sendchannel.transfer(in_buffer)
        dma.sendchannel.wait()
        dma.recvchannel.transfer(out_buffer)
        dma.recvchannel.wait()
        end_time = time.time()
        print('Output:', out_buffer)
        print('Time taken:', end_time - start_time)
