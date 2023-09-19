#include "CNN.h"
#include <cmath>
#include <iostream>

float input[INPUTLENGTH * INPUTAXES];

float conv1Weights[CONV1LENGTH * CONV1AXES * CONV1FILTERS] = {
    #include "conv1_weights.txt"
};

float conv1Biases[CONV1FILTERS] = {
    #include "conv1_biases.txt"
};

float conv1Output[CONV1OUTPUTLENGTH * CONV1OUTPUTAXES];

float conv2Weights[CONV2LENGTH * CONV2AXES * CONV2FILTERS] = {
    #include "conv2_weights.txt"
};

float conv2Biases[CONV2FILTERS] = {
    #include "conv2_biases.txt"
};

float conv2Output[CONV2OUTPUTLENGTH * CONV2OUTPUTAXES];

float dense1Weights[DENSE1LENGTH * DENSE1AXES] = {
    #include "dense1_weights.txt"
};

float dense1Biases[DENSE1AXES] = {
    #include "dense1_biases.txt"
};

float dense1Output[DENSE1OUTPUTLENGTH];

float dense2Weights[DENSE2LENGTH * DENSE2AXES] = {
    #include "dense2_weights.txt"
};

float dense2Biases[DENSE2AXES] = {
    #include "dense2_biases.txt"
};

float dense2Output[DENSE2OUTPUTLENGTH];

Matrix::Matrix(int samples, int axes, float* val) {
    this->nSamples = samples;
    this->nAxes = axes;
    this->values = val;
}

float Matrix::getValue(int sample, int axis) {
    return this->values[axis + sample * this->nAxes];
}

void Matrix::print() {
    for (int i = 0; i < this->nSamples * this->nAxes; i++) {
        std::cout << values[i];
        if (i + 1 < this->nSamples * this->nAxes)
            std::cout << ",";
    }
    std::cout << std::endl;
}

Tensor::Tensor(int samples, int axes, int depth, float* val) {
    this->nSamples = samples;
    this->nAxes = axes;
    this->nDepth = depth;
    this->values = val;
}

float Tensor::getValue(int sample, int axis, int depth) {
    return values[depth + axis * this->nDepth + sample * this->nDepth * this->nAxes];
}

Conv1DLayer::Conv1DLayer(Tensor t, float* b) {
    this->weights = t;
    this->biases = b;
}

void Conv1DLayer::activation(Matrix* iMatrix) {
    // ReLU
    for (int i = 0; i < iMatrix->nSamples; i++) {
        for (int j = 0; j < iMatrix->nAxes; j++) {
            int index = i * iMatrix->nAxes + j;
            if (iMatrix->values[index] < 0) {
                iMatrix->values[index] = 0;
            }
        }
    }
}

void Conv1DLayer::output(Matrix iMatrix, Matrix* oMatrix) {
    int outputSamples = iMatrix.nSamples - this->weights.nSamples + 1;
    // Iterate through each filter
    for (int i = 0; i < this->weights.nDepth; i++) {
        // Iterate through each window
        for (int j = 0; j < outputSamples; j++) {
            float total = 0.0F;
            // Iterate though all samples in input window
            for (int k = 0; k < this->weights.nSamples; k++) {
                // Iterate throguh all axes in input window
                for (int m = 0; m < iMatrix.nAxes; m++) {
                    total += iMatrix.getValue(k + j, m) * this->weights.getValue(k, m, i);
                }
            }
            oMatrix->values[i + j * this->weights.nDepth] = total + biases[i];
        }
    }

    this->activation(oMatrix);
}

DenseLayer::DenseLayer(Matrix w, float* b) {
    this->weights = w;
    this->biases = b;
}

void DenseLayer::output(float* input, float* output, bool useActivation) {
    for (int i = 0; i < this->weights.nAxes; i++) {
        float total = 0.0F;
        for (int j = 0; j < this->weights.nSamples; j++) {
            total += this->weights.getValue(j, i) * input[j];
        }
        output[i] = total + this->biases[i];
    }

    if (useActivation)
        this->activation(output);
}

void DenseLayer::activation(float* input) {
    // ReLU
    for (int i = 0; i < this->weights.nAxes; i++) {
        if (input[i] < 0) {
            input[i] = 0;
        }
    }
}

void linearDetrend(Matrix* mat) {
    float N = (float)mat->nSamples;
    float sumX = (float)((mat->nSamples - 1) * mat->nSamples) / 2.0F;
    float sumXSqu = sumX * sumX;
    float sumOfXSqu = (float)((N * (N + 1) * (2 * N + 1)) / 6);

    for (int i = 0; i < mat->nAxes; i++) {
        float sumXY = 0.0F;
        float sumY = 0.0F;

        for (int j = 0; j < mat->nSamples; j++) {
            sumY += mat->getValue(j, i);
            sumXY += (float)j * mat->getValue(j, i);
        }

        float m = (N * sumXY - sumX * sumY) / (N * sumOfXSqu - sumXSqu);
        float c = (sumY - m * sumX) / N;

        for (int j = 0; j < mat->nSamples; j++) {
            mat->values[mat->nAxes * j + i] = mat->getValue(j, i) - (m * j + c);
        }
    }
}

void zScore(Matrix* mat) {
    for (int i = 0; i < mat->nAxes; i++) {
        float mean = 0.0F;

        for (int j = 0; j < mat->nSamples; j++) {
            mean += mat->getValue(j, i);
        }

        mean /= (float)mat->nSamples;
        float sumDiffSqu = 0.0F;

        for (int j = 0; j < mat->nSamples; j++) {
            float diff = mat->getValue(j, i) - mean;
            sumDiffSqu += diff * diff;
        }

        float stdDev = std::sqrt(sumDiffSqu / (float)mat->nSamples);

        for (int j = 0; j < mat->nSamples; j++) {
            float z = (mat->getValue(j, i) - mean) / stdDev;
            mat->values[mat->nAxes * j + i] = z;
        }
    }
}

void argmax(float* arr, int size) {
    int index = 0;
    for (int i = 1; i < size; i++) {
        if (arr[i] > arr[index]) 
            index = i;
    }
    std::cout << index;
}

int main() {
    for (int i = 0; i < INPUTLENGTH * INPUTAXES; i++) {
        std::cin >> input[i];
    }

    Matrix inputMat = Matrix(INPUTLENGTH, INPUTAXES, input);

    // For some reason NN performs better without preprocessing...
    // linearDetrend(&inputMat);
    // zScore(&inputMat);

    Matrix conv1OutputMat = Matrix(CONV1OUTPUTLENGTH, CONV1OUTPUTAXES, conv1Output);
    Tensor conv1Tensor = Tensor(CONV1LENGTH, CONV1AXES, CONV1FILTERS, conv1Weights);
    Conv1DLayer layer1 = Conv1DLayer(conv1Tensor, conv1Biases);
    layer1.output(inputMat, &conv1OutputMat);

    Matrix conv2OutputMat = Matrix(CONV2OUTPUTLENGTH, CONV2OUTPUTAXES, conv2Output);
    Tensor conv2Tensor = Tensor(CONV2LENGTH, CONV2AXES, CONV2FILTERS, conv2Weights);
    Conv1DLayer layer2 = Conv1DLayer(conv2Tensor, conv2Biases);
    layer2.output(conv1OutputMat, &conv2OutputMat);

    Matrix dense1Mat = Matrix(DENSE1LENGTH, DENSE1AXES, dense1Weights);
    DenseLayer layer4 = DenseLayer(dense1Mat, dense1Biases);
    layer4.output(conv2OutputMat.values, dense1Output, true);

    Matrix dense2Mat = Matrix(DENSE2LENGTH, DENSE2AXES, dense2Weights);
    DenseLayer layer5 = DenseLayer(dense2Mat, dense2Biases);
    layer5.output(dense1Output, dense2Output, false);

    argmax(dense2Output, DENSE2OUTPUTLENGTH);

    return 0;
}
