from pynq import Overlay, allocate
import pynq.lib.dma
import sys, os
import numpy as np

cfd = sys.path[0]

print('Loading overlay...')
overlay = Overlay(os.path.join(cfd, 'design_1_wrapper.bit'))
dma = overlay.adder_dma
print('Overlay loaded.')

in_array = [1, 2, 3, 4]

in_buffer = allocate(shape=(4,), dtype=np.int32)
out_buffer = allocate(shape=(4,), dtype=np.int32)

in_buffer[:] = in_array

print('Sending buffers...')
dma.sendchannel.transfer(in_buffer)
print('Setting up receive channel...')
dma.recvchannel.transfer(out_buffer)
dma.sendchannel.wait()
print('Buffers sent.')
dma.recvchannel.wait()
print('Output received.')
print(out_buffer)
