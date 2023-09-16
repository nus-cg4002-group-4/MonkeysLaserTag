from pynq import Overlay, allocate
import pynq.lib.dma
import sys, os

cfd = sys.path[0]

overlay = Overlay(os.path.join(cfd, 'design_1.bit'))
dma = overlay.axi_dma_0

in_buffer = allocate(shape=(240,), dtype=np.float32)
out_buffer = allocate(shape=(1,), dtype=np.uint32)

for file in os.listdir(cfd):
    if file.endswith(".in"):
        p = os.path.join(cfd, file)
        f = open(p, 'r')
        data = f.read().split(',')
        in_buffer[:] = data
        dma.sendchannel.transfer(in_buffer)
        dma.recvchannel.transfer(out_buffer)
        dma.sendchannel.wait()
        dma.recvchannel.wait()
        print(out_buffer)
