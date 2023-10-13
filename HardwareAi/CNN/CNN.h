#pragma once

#define INPUTLENGTH 80
#define INPUTAXES 3

#define CONV1LENGTH 3
#define CONV1AXES 3
#define CONV1FILTERS 16

#define CONV1OUTPUTLENGTH (INPUTLENGTH - CONV1LENGTH + 1)
#define CONV1OUTPUTAXES CONV1FILTERS

#define CONV2LENGTH 5
#define CONV2AXES 16
#define CONV2FILTERS 32

#define CONV2OUTPUTLENGTH (CONV1OUTPUTLENGTH - CONV2LENGTH + 1)
#define CONV2OUTPUTAXES CONV2FILTERS

#define DENSE1LENGTH 2368
#define DENSE1AXES 64

#define DENSE1OUTPUTLENGTH DENSE1AXES

#define DENSE2LENGTH 64
#define DENSE2AXES 6

#define DENSE2OUTPUTLENGTH DENSE2AXES

class Matrix {
public:
    int nSamples = 0;
    int nAxes = 0;
    float* values;

    Matrix(int samples, int axes, float* val);
    float getValue(int x, int y);
    void print();
};

class Tensor {
public:
    int nSamples = 0;
    int nAxes = 0;
    int nDepth = 0;
    float* values;

    Tensor(int samples, int axes, int depth, float* val);
    float getValue(int x, int y, int z);
};

class Conv1DLayer {
    Tensor weights = Tensor(0, 0, 0, nullptr);
    float* biases = nullptr;

public:
    Conv1DLayer(Tensor t, float* b);
    void activation(Matrix* iMatrix);
    void output(Matrix iMatrix, Matrix* oMatrix);
};

class DenseLayer {
    Matrix weights = Matrix(0, 0, nullptr);
    float* biases = nullptr;

public:
    DenseLayer(Matrix w, float* b);
    void activation(float* input);
    void output(float* input, float* output, bool useActivation);
};
