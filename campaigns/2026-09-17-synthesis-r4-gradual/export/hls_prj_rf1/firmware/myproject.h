#ifndef MYPROJECT_H_
#define MYPROJECT_H_

#include "ap_fixed.h"
#include "ap_int.h"
#include "hls_stream.h"

#include "defines.h"


// Prototype of top level function for C-synthesis
extern "C" void myproject(
    input_1_t input_1[8*3],
    result_t layer83_out[5]
);

// hls-fpga-machine-learning insert emulator-defines


#endif
