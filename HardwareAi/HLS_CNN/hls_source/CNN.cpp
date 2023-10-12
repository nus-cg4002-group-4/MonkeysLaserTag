#include "CNN.h"
#include <cmath>

#include "hls_stream.h"
#include "ap_int.h"
#include "ap_axi_sdata.h"

// Structs for data transfer

union fp_int {
	int ival;
	float fval;
};

struct AXIS_wLAST{
	int data;
	bool last;
};

//typedef ap_axis<32,0,0,0> AXIS_wLAST;

template <int totalSize>
void init(float* array, hls::stream<AXIS_wLAST>& DATA_INPUT) {
	AXIS_wLAST read_input;
	fp_int converter;

	// Read in data from input stream
	for (int i = 0; i < totalSize; i++) {
		read_input = DATA_INPUT.read();
		converter.ival = read_input.data;
		array[i] = converter.fval;
	}

}

template <int inputSamples, int inputAxes, int filterSamples, int filterAxes, int filterDepth, int stepSize>
void conv1DLayer(float* iMatrix, float* fWeights, float* fBiases, float* oMatrix) {
	int outputSamples = (inputSamples - filterSamples) / stepSize + 1;
    // Iterate through each filter
    for (int i = 0; i < filterDepth; i++) {
        // Iterate through each window
        for (int j = 0; j < outputSamples; j++) {
            float total = 0.0F;
            // Iterate though all samples in input window
            for (int k = 0; k < filterSamples; k++) {
                // Iterate through all axes in input window
                for (int m = 0; m < filterAxes; m++) {
//#pragma HLS UNROLL
#pragma HLS PIPELINE
                    total += iMatrix[(k + stepSize * j) * inputAxes + m] * fWeights[k * filterDepth * filterAxes + m * filterDepth + i];
                }
            }
            oMatrix[i + j * filterDepth] = total + fBiases[i];
        }
    }

    // Activation: ReLU
    for (int i = 0; i < (inputSamples - filterSamples + 1) * filterDepth; i++) {
    	if (oMatrix[i] < 0) {
    		oMatrix[i] = 0;
    	}
    }
}

template <int inputSamples, int filterSamples, int filterAxes>
void denseLayer(float* input, float* fWeights, float* fBiases, float* output, bool useActivation) {
	for (int i = 0; i < filterAxes; i++) {
		float total = 0.0F;
        for (int j = 0; j < filterSamples; j++) {
//#pragma HLS UNROLL factor=64
#pragma HLS PIPELINE
            total += fWeights[j * filterAxes + i] * input[j];
        }
        output[i] = total + fBiases[i];
    }

    if (useActivation) {
    	// Activation: ReLU
    	for (int i = 0; i < filterAxes; i++) {
    		if (output[i] < 0) {
    			output[i] = 0;
    		}
    	}
    }
}

template <int inputSamples, int inputAxes>
void linearDetrend(float mat[inputSamples * inputAxes]) {
    float N = inputSamples;
    float sumX = (float)((inputSamples - 1) * inputSamples) / 2.0F;
    float sumXSqu = sumX * sumX;
    float sumOfXSqu = (float)((N * (N + 1) * (2 * N + 1)) / 6);

    for (int i = 0; i < inputAxes; i++) {
        float sumXY = 0.0F;
        float sumY = 0.0F;

        for (int j = 0; j < inputSamples; j++) {
            sumY += mat[j * inputAxes + i];
            sumXY += (float)j * mat[j * inputAxes + i];
        }

        float m = (N * sumXY - sumX * sumY) / (N * sumOfXSqu - sumXSqu);
        float c = (sumY - m * sumX) / N;

        for (int j = 0; j < inputSamples; j++) {
            mat[inputAxes * j + i] = mat[j * inputAxes + i] - (m * j + c);
        }
    }
}

template <int inputSamples, int inputAxes>
void zScore(float mat[inputSamples * inputAxes]) {
    for (int i = 0; i < inputAxes; i++) {
        float mean = 0.0F;

        for (int j = 0; j < inputSamples; j++) {
            mean += mat[j * inputAxes + i];
        }

        mean /= (float)inputSamples;
        float sumDiffSqu = 0.0F;

        for (int j = 0; j < inputSamples; j++) {
            float diff = mat[j * inputAxes + i] - mean;
            sumDiffSqu += diff * diff;
        }

        float stdDev = std::sqrt(sumDiffSqu / (float)inputSamples);

        for (int j = 0; j < inputSamples; j++) {
            float z = (mat[j * inputAxes + i] - mean) / stdDev;
            mat[inputAxes * j + i] = z;
        }
    }
}

template <int size>
int argmax(float arr[size]) {
    int index = 0;
    for (int i = 1; i < size; i++) {
        if (arr[i] > arr[index]) 
            index = i;
    }
    return index;
}

void main_func(hls::stream<AXIS_wLAST>& DATA_INPUT, hls::stream<AXIS_wLAST>& DATA_OUTPUT) {
#pragma HLS INTERFACE ap_ctrl_none port=return
#pragma HLS INTERFACE axis port=DATA_INPUT
#pragma HLS INTERFACE axis port=DATA_OUTPUT

	float input[INPUTLENGTH * INPUTAXES];

	static float conv1Weights[CONV1LENGTH * CONV1AXES * CONV1FILTERS] = {
	    #include "conv1_weights.txt"
	};

	static float conv1Biases[CONV1FILTERS] = {
	    #include "conv1_biases.txt"
	};

	float conv1Output[CONV1OUTPUTLENGTH * CONV1OUTPUTAXES];

	static float conv2Weights[CONV2LENGTH * CONV2AXES * CONV2FILTERS] = {
	    #include "conv2_weights.txt"
	};

	static float conv2Biases[CONV2FILTERS] = {
	    #include "conv2_biases.txt"
	};

	float conv2Output[CONV2OUTPUTLENGTH * CONV2OUTPUTAXES];

	static float dense1Weights[DENSE1LENGTH * DENSE1AXES] = {
	    #include "dense1_weights.txt"
	};

	static float dense1Biases[DENSE1AXES] = {
	    #include "dense1_biases.txt"
	};

	float dense1Output[DENSE1OUTPUTLENGTH];

	static float dense2Weights[DENSE2LENGTH * DENSE2AXES] = {
	    #include "dense2_weights.txt"
	};

	static float dense2Biases[DENSE2AXES] = {
	    #include "dense2_biases.txt"
	};

	float dense2Output[DENSE2OUTPUTLENGTH];

    //linearDetrend<INPUTLENGTH, INPUTAXES>(input);
    //zScore<INPUTLENGTH, INPUTAXES>(input);

	//init<INPUTLENGTH * INPUTAXES>(input, DATA_INPUT);
	AXIS_wLAST read_input;
	fp_int converter;

	// Read in data from input stream
	for (int i = 0; i < INPUTLENGTH * INPUTAXES; i++) {
		read_input = DATA_INPUT.read();
		converter.ival = read_input.data;
		input[i] = converter.fval;
	}

	conv1DLayer<INPUTLENGTH, INPUTAXES, CONV1LENGTH, CONV1AXES, CONV1FILTERS, CONV1STEPSIZE> (
			input, conv1Weights, conv1Biases, conv1Output
		);

	conv1DLayer<CONV1OUTPUTLENGTH, CONV1OUTPUTAXES, CONV2LENGTH, CONV2AXES, CONV2FILTERS, CONV2STEPSIZE> (
				conv1Output, conv2Weights, conv2Biases, conv2Output
		);

	denseLayer<CONV2OUTPUTLENGTH * CONV2OUTPUTAXES, DENSE1LENGTH, DENSE1AXES> (
			conv2Output, dense1Weights, dense1Biases, dense1Output, true
		);

	denseLayer<DENSE1OUTPUTLENGTH, DENSE2LENGTH, DENSE2AXES> (
				dense1Output, dense2Weights, dense2Biases, dense2Output, false
		);

	// Write to output stream
	AXIS_wLAST write_output;
	// write_output.data = 0;
	// DATA_OUTPUT.write(write_output);
	write_output.data = argmax<DENSE2OUTPUTLENGTH>(dense2Output);
	write_output.last = 1;
	DATA_OUTPUT.write(write_output);
}
