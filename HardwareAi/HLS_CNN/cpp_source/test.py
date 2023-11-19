# Test against C++
import subprocess, sys, os, pathlib, csv
import numpy as np

cfd = sys.path[0]
#test_result = subprocess.run([out_loc, '<', test_loc], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
in_loc = os.path.join(cfd, 'test.in')
out_loc = os.path.join(cfd, 'a.out')

subprocess.run('make', cwd=cfd)

for file in os.listdir(os.path.join(cfd, 'test')):
    if file.endswith(".csv"):
        values = np.loadtxt(os.path.join(cfd, 'test', file), delimiter=',', skiprows=1)

        normalize_flex = lambda i: i * (2**15 / 2**10)
        values[:,6] = np.vectorize(normalize_flex)(values[:,6])
        
        asfloat = lambda i: float(i + 2**15) / 2**15 - 1.0
        values = np.vectorize(asfloat)(values)

        values = values.flatten()

        np.savetxt(in_loc, values)
        test_pipe = subprocess.Popen(['cat', in_loc], stdout=subprocess.PIPE)
        out_pipe = subprocess.Popen([out_loc], stdin=test_pipe.stdout, stdout=subprocess.PIPE)
        output = out_pipe.communicate()[0].decode('ascii')
        print(file, output)
