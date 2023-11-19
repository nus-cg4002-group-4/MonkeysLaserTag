# Data collection

* Sample rate: 40 Hz
* Window size: 80 samples (2s)
* Stride: ?? (some groups have 10 samples/0.5s)

Rate of data output = ?? (Once every 10 samples/0.5s if above stride is taken)

Action should be in the middle of sample due to nature of Conv1D

Enumerations:
* Grenade
    * Pull back with fist clenched, throw over shoulder
    * Onset triggered on pull back
* Shield
    * Clench fist and hit chest, stay for 1s before returning
    * Onset triggered on raise
* Reload
   * From raised gun position, pull hand towrds chest with open palm facing upwards, the return to raised gun position
   * Onset triggered on pull back
* Punch
    * Throw punch straight ahead, then return to neutral position
    * Onset triggered on punch
* Spear
    * Pump imaginary spear twice slowly, then throw
    * Onset triggered on first pump
* Hammer
    * Swing arm in a circle clockwise on the right side of you twice, then release towards the front
    * Onset triggered on first circle
* Portal
    * Make L with three fingers, then spin in circle in front of you twice, then return to neutral position
    * Onset triggered while making the circle
* Spider
    * Pull your hand back towards you, then flick your wrist outwards, forming your hand into the spiderman shape
    * Onset triggered while flicking
* Logout
    * Tap right shoulder twice, then return to neutal position
    * Onset triggered on first tap
* Raise gun
    * From a neutral position, raise your gun and take aim
    * Onset triggered on raise

Actions which are confused:
* Grenade and punch
* Portal and hammer

## CSV

Headers of the CSV file:
```csv
[ax],[ay],[az],[gx],[gy],[gz],[flex]
```

# Preprocessing

* Vector and gyro normalization using linear detrend, then z-score
    * Detrend formula for $N$ points:
$$
y=mx+c
$$
$$
m = \frac{N\,\Sigma(xy)-\Sigma x\,\Sigma y}{N\,\Sigma(x^2)-(\Sigma x)^2}
$$
$$
c = \frac{\Sigma y - m\,\Sigma x}{N}
$$
    * Z-score formula:
$$
z=\frac{x-\mu}{\sigma}​
$$

* Balance data points so that number of samples per action is equal
* Train/test segmentation: 80/20 split looks good

# NN Architecture

Potential starting dimensions for each window:

### `(40, 12)` or `(1, 40, 12)`
* 40 for the amount of samples
* 12 for 3 sensors * 6 measurements
* `Conv2D` is possible but may hallucinate
* `Conv1D` looks promising, good separation

### `(40, 4, 3)` 
* 40 for the amount of samples
* 4 for each hand * each type of measurement
* 3 for $x,y,z$
* Better split of data
* Not odd, so awkward to train

### `(40, 2, 2, 3)`
* 40 for the amount of samples
* 2 for each hand
* 2 for each type of measurement (accel or gyro)
* 3 for $x,y,z$
* Very fine-grain
* But also nightmare to train

```python
# For (40, 6) case

model = Sequential()
model.add(Conv1D(16, 3, activation='relu', input_shape=(1, 40, 6)))

# Dimension: (38, 16)

model.add(Conv1D(32, 5, activation='relu'))

# Dimension: (34, 32)

model.add(Flatten())

# Dimension: (1088)

model.add(Dense(64, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(6, activation='softmax'))

model.compile(optimizer=Adam(learning_rate = 0.001), loss = 'sparse_categorical_crossentropy', metrics = ['accuracy'])
```

Softmax formula for series $x_1\cdots x_n$:
$$
\text{Softmax}(x_i)=\frac{\exp(x_i)}{\sum_{j=1}^n\exp(x_j)}
$$

# Data Augmentation

* Adding random vector to each?
* Playing with window cutoffs

## Start of Move Detection

Set magnitude threshold and check for it. Once detected then send window to FPGA.

Quick magnitude algo:

$$
\text{QuickMag} = x^2+y^2+z^2
$$

Maybe send several windows over and confirm if all windows return the same output?

**Idea**: Use two neural networks, one to check if window is a move and the second for move idenification

Since accelerometer essentially measures forces, take average of 10 vectors and use for calculations between windows
* $\cos \theta = \frac{A\cdot B}{\lvert A\rvert\lvert B\rvert}$

# Porting to HLS

https://www.youtube.com/watch?v=EjjzIimyiM0

Quantization-aware training
xczu3eg-sbva484-2-i with 150MHz clock

## Working With HLS

Apparently Vivado 2022.2 cannot synthesize/has bugs with AXI stream, so switched to 2019.1.

Initially values were integrated as part of BRAM, but Vivado 2019.1 takes extremely long time to synthesize (around 10 hours), and there is not enough area for implementation. 

~~Switched to loading values into IP using AXI stream, synthesis now takes 10 mins, enough area for implementation.~~

Bad idea, nightmare to initialize. Reduce network size to fit onto FPGA.
