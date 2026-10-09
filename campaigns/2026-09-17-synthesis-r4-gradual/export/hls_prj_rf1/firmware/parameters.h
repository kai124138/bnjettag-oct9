#ifndef PARAMETERS_H_
#define PARAMETERS_H_

#include "ap_fixed.h"
#include "ap_int.h"

#include "nnet_utils/nnet_code_gen.h"
#include "nnet_utils/nnet_helpers.h"
// hls-fpga-machine-learning insert includes
#include "nnet_utils/nnet_activation.h"
#include "nnet_utils/nnet_activation_stream.h"
#include "nnet_utils/nnet_batchnorm.h"
#include "nnet_utils/nnet_batchnorm_stream.h"
#include "nnet_utils/nnet_dense.h"
#include "nnet_utils/nnet_dense_compressed.h"
#include "nnet_utils/nnet_dense_stream.h"
#include "nnet_utils/nnet_einsum.h"
#include "nnet_utils/nnet_einsum_dense.h"
#include "nnet_utils/nnet_merge.h"
#include "nnet_utils/nnet_merge_stream.h"
#include "nnet_utils/nnet_pooling.h"
#include "nnet_utils/nnet_pooling_stream.h"

// hls-fpga-machine-learning insert weights
#include "weights/w3.h"
#include "weights/b3.h"
#include "weights/s5.h"
#include "weights/b5.h"
#include "weights/w7.h"
#include "weights/b7.h"
#include "weights/w9.h"
#include "weights/b9.h"
#include "weights/s11.h"
#include "weights/b11.h"
#include "weights/s13.h"
#include "weights/b13.h"
#include "weights/w18.h"
#include "weights/b18.h"
#include "weights/s21.h"
#include "weights/b21.h"
#include "weights/w26.h"
#include "weights/b26.h"
#include "weights/s28.h"
#include "weights/b28.h"
#include "weights/w31.h"
#include "weights/b31.h"
#include "weights/s33.h"
#include "weights/b33.h"
#include "weights/w36.h"
#include "weights/b36.h"
#include "weights/s38.h"
#include "weights/b38.h"
#include "weights/w41.h"
#include "weights/b41.h"
#include "weights/w43.h"
#include "weights/b43.h"
#include "weights/s45.h"
#include "weights/b45.h"
#include "weights/s47.h"
#include "weights/b47.h"
#include "weights/w52.h"
#include "weights/b52.h"
#include "weights/s55.h"
#include "weights/b55.h"
#include "weights/w60.h"
#include "weights/b60.h"
#include "weights/s62.h"
#include "weights/b62.h"
#include "weights/w65.h"
#include "weights/b65.h"
#include "weights/s67.h"
#include "weights/b67.h"
#include "weights/w70.h"
#include "weights/b70.h"
#include "weights/s72.h"
#include "weights/b72.h"
#include "weights/w76.h"
#include "weights/b76.h"
#include "weights/s78.h"
#include "weights/b78.h"
#include "weights/w81.h"
#include "weights/b81.h"
#include "weights/s83.h"
#include "weights/b83.h"


// hls-fpga-machine-learning insert layer-config
// input_proj
struct config3_tpose_inp {
    static const unsigned dims = 2;
    static const unsigned N = 24;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config3_tpose_inp_from_shape[2] = {8, 3};
unsigned config3_tpose_inp_to_shape[2] = {8, 3};
unsigned config3_tpose_inp_perm[2] = {0, 1};
unsigned config3_tpose_inp_perm_strides[2] = {3, 1};

const unsigned* const config3_tpose_inp::from_shape = config3_tpose_inp_from_shape;
const unsigned* const config3_tpose_inp::to_shape = config3_tpose_inp_to_shape;
const unsigned* const config3_tpose_inp::perm = config3_tpose_inp_perm;
const unsigned* const config3_tpose_inp::perm_strides = config3_tpose_inp_perm_strides;


struct config3_tpose_out {
    static const unsigned dims = 2;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config3_tpose_out_from_shape[2] = {8, 32};
unsigned config3_tpose_out_to_shape[2] = {8, 32};
unsigned config3_tpose_out_perm[2] = {0, 1};
unsigned config3_tpose_out_perm_strides[2] = {32, 1};

const unsigned* const config3_tpose_out::from_shape = config3_tpose_out_from_shape;
const unsigned* const config3_tpose_out::to_shape = config3_tpose_out_to_shape;
const unsigned* const config3_tpose_out::perm = config3_tpose_out_perm;
const unsigned* const config3_tpose_out::perm_strides = config3_tpose_out_perm_strides;


struct config3_dense : nnet::dense_config {
    static const unsigned n_in = 3;
    static const unsigned n_out = 32;
    static const unsigned reuse_factor = 1;
    static const unsigned strategy = nnet::latency;
    static const unsigned n_zeros = 0;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in * n_out, reuse_factor) - n_zeros / reuse_factor;
    typedef input_proj_accum_t accum_t;
    typedef input_proj_bias_t bias_t;
    typedef input_proj_weight_t weight_t;
    template<class data_T, class res_T, class CONFIG_T>
    using kernel = nnet::DenseLatency<data_T, res_T, CONFIG_T>;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};



struct config3 {
    typedef config3_tpose_inp tpose_inp_conf;
    typedef config3_tpose_out tpose_out_conf;

    typedef input_proj_accum_t accum_t;
    typedef input_proj_bias_t bias_t;

    typedef config3_dense dense_conf;

    // Layer Sizes
    static const unsigned n_free_data = 8;
    static const unsigned n_free_kernel = 32;
    static const unsigned n_contract = 3;
    static const unsigned n_inplace = 1;

    // Resource reuse info
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned strategy = nnet::latency;
    static const unsigned reuse_factor = 1;
    static const unsigned parallelization_factor = 8; // Only useful when n_inplace > 1
};

// input_proj_affine
struct config5 : nnet::batchnorm_config {
    static const unsigned n_in = 8*32;
    static const unsigned n_filt = 32;
    static const unsigned n_scale_bias = (n_filt == -1) ? n_in : n_filt;
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned reuse_factor = 1;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in, reuse_factor);
    static const bool store_weights_in_bram = false;
    typedef input_proj_affine_bias_t bias_t;
    typedef input_proj_affine_scale_t scale_t;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};

// bit_block_0_attn_Wq
struct config7_tpose_inp {
    static const unsigned dims = 2;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config7_tpose_inp_from_shape[2] = {8, 32};
unsigned config7_tpose_inp_to_shape[2] = {8, 32};
unsigned config7_tpose_inp_perm[2] = {0, 1};
unsigned config7_tpose_inp_perm_strides[2] = {32, 1};

const unsigned* const config7_tpose_inp::from_shape = config7_tpose_inp_from_shape;
const unsigned* const config7_tpose_inp::to_shape = config7_tpose_inp_to_shape;
const unsigned* const config7_tpose_inp::perm = config7_tpose_inp_perm;
const unsigned* const config7_tpose_inp::perm_strides = config7_tpose_inp_perm_strides;


struct config7_tpose_out {
    static const unsigned dims = 3;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config7_tpose_out_from_shape[3] = {8, 4, 8};
unsigned config7_tpose_out_to_shape[3] = {8, 4, 8};
unsigned config7_tpose_out_perm[3] = {0, 1, 2};
unsigned config7_tpose_out_perm_strides[3] = {32, 8, 1};

const unsigned* const config7_tpose_out::from_shape = config7_tpose_out_from_shape;
const unsigned* const config7_tpose_out::to_shape = config7_tpose_out_to_shape;
const unsigned* const config7_tpose_out::perm = config7_tpose_out_perm;
const unsigned* const config7_tpose_out::perm_strides = config7_tpose_out_perm_strides;


struct config7_dense : nnet::dense_config {
    static const unsigned n_in = 32;
    static const unsigned n_out = 32;
    static const unsigned reuse_factor = 1;
    static const unsigned strategy = nnet::latency;
    static const unsigned n_zeros = 0;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in * n_out, reuse_factor) - n_zeros / reuse_factor;
    typedef bit_block_0_attn_Wq_accum_t accum_t;
    typedef model_default_t bias_t;
    typedef model_default_t weight_t;
    template<class data_T, class res_T, class CONFIG_T>
    using kernel = nnet::DenseLatency<data_T, res_T, CONFIG_T>;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};



struct config7 {
    typedef config7_tpose_inp tpose_inp_conf;
    typedef config7_tpose_out tpose_out_conf;

    typedef bit_block_0_attn_Wq_accum_t accum_t;
    typedef model_default_t bias_t;

    typedef config7_dense dense_conf;

    // Layer Sizes
    static const unsigned n_free_data = 8;
    static const unsigned n_free_kernel = 32;
    static const unsigned n_contract = 32;
    static const unsigned n_inplace = 1;

    // Resource reuse info
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned strategy = nnet::latency;
    static const unsigned reuse_factor = 1;
    static const unsigned parallelization_factor = 8; // Only useful when n_inplace > 1
};

// bit_block_0_attn_Wk
struct config9_tpose_inp {
    static const unsigned dims = 2;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config9_tpose_inp_from_shape[2] = {8, 32};
unsigned config9_tpose_inp_to_shape[2] = {8, 32};
unsigned config9_tpose_inp_perm[2] = {0, 1};
unsigned config9_tpose_inp_perm_strides[2] = {32, 1};

const unsigned* const config9_tpose_inp::from_shape = config9_tpose_inp_from_shape;
const unsigned* const config9_tpose_inp::to_shape = config9_tpose_inp_to_shape;
const unsigned* const config9_tpose_inp::perm = config9_tpose_inp_perm;
const unsigned* const config9_tpose_inp::perm_strides = config9_tpose_inp_perm_strides;


struct config9_tpose_out {
    static const unsigned dims = 3;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config9_tpose_out_from_shape[3] = {8, 4, 8};
unsigned config9_tpose_out_to_shape[3] = {8, 4, 8};
unsigned config9_tpose_out_perm[3] = {0, 1, 2};
unsigned config9_tpose_out_perm_strides[3] = {32, 8, 1};

const unsigned* const config9_tpose_out::from_shape = config9_tpose_out_from_shape;
const unsigned* const config9_tpose_out::to_shape = config9_tpose_out_to_shape;
const unsigned* const config9_tpose_out::perm = config9_tpose_out_perm;
const unsigned* const config9_tpose_out::perm_strides = config9_tpose_out_perm_strides;


struct config9_dense : nnet::dense_config {
    static const unsigned n_in = 32;
    static const unsigned n_out = 32;
    static const unsigned reuse_factor = 1;
    static const unsigned strategy = nnet::latency;
    static const unsigned n_zeros = 0;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in * n_out, reuse_factor) - n_zeros / reuse_factor;
    typedef bit_block_0_attn_Wk_accum_t accum_t;
    typedef model_default_t bias_t;
    typedef model_default_t weight_t;
    template<class data_T, class res_T, class CONFIG_T>
    using kernel = nnet::DenseLatency<data_T, res_T, CONFIG_T>;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};



struct config9 {
    typedef config9_tpose_inp tpose_inp_conf;
    typedef config9_tpose_out tpose_out_conf;

    typedef bit_block_0_attn_Wk_accum_t accum_t;
    typedef model_default_t bias_t;

    typedef config9_dense dense_conf;

    // Layer Sizes
    static const unsigned n_free_data = 8;
    static const unsigned n_free_kernel = 32;
    static const unsigned n_contract = 32;
    static const unsigned n_inplace = 1;

    // Resource reuse info
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned strategy = nnet::latency;
    static const unsigned reuse_factor = 1;
    static const unsigned parallelization_factor = 8; // Only useful when n_inplace > 1
};

// bit_block_0_attn_Wq_affine
struct config11 : nnet::batchnorm_config {
    static const unsigned n_in = 8*4*8;
    static const unsigned n_filt = 8;
    static const unsigned n_scale_bias = (n_filt == -1) ? n_in : n_filt;
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned reuse_factor = 1;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in, reuse_factor);
    static const bool store_weights_in_bram = false;
    typedef bit_block_0_attn_Wq_affine_bias_t bias_t;
    typedef bit_block_0_attn_Wq_affine_scale_t scale_t;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};

// bit_block_0_attn_Wk_affine
struct config13 : nnet::batchnorm_config {
    static const unsigned n_in = 8*4*8;
    static const unsigned n_filt = 8;
    static const unsigned n_scale_bias = (n_filt == -1) ? n_in : n_filt;
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned reuse_factor = 1;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in, reuse_factor);
    static const bool store_weights_in_bram = false;
    typedef bit_block_0_attn_Wk_affine_bias_t bias_t;
    typedef bit_block_0_attn_Wk_affine_scale_t scale_t;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};

// bit_block_0_attn_scores
struct config16_tpose_inp0 {
    static const unsigned dims = 3;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config16_tpose_inp0_from_shape[3] = {8, 4, 8};
unsigned config16_tpose_inp0_to_shape[3] = {4, 8, 8};
unsigned config16_tpose_inp0_perm[3] = {1, 0, 2};
unsigned config16_tpose_inp0_perm_strides[3] = {8, 32, 1};

const unsigned* const config16_tpose_inp0::from_shape = config16_tpose_inp0_from_shape;
const unsigned* const config16_tpose_inp0::to_shape = config16_tpose_inp0_to_shape;
const unsigned* const config16_tpose_inp0::perm = config16_tpose_inp0_perm;
const unsigned* const config16_tpose_inp0::perm_strides = config16_tpose_inp0_perm_strides;


struct config16_tpose_inp1 {
    static const unsigned dims = 3;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config16_tpose_inp1_from_shape[3] = {8, 4, 8};
unsigned config16_tpose_inp1_to_shape[3] = {4, 8, 8};
unsigned config16_tpose_inp1_perm[3] = {1, 0, 2};
unsigned config16_tpose_inp1_perm_strides[3] = {8, 32, 1};

const unsigned* const config16_tpose_inp1::from_shape = config16_tpose_inp1_from_shape;
const unsigned* const config16_tpose_inp1::to_shape = config16_tpose_inp1_to_shape;
const unsigned* const config16_tpose_inp1::perm = config16_tpose_inp1_perm;
const unsigned* const config16_tpose_inp1::perm_strides = config16_tpose_inp1_perm_strides;


struct config16_tpose_out {
    static const unsigned dims = 3;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config16_tpose_out_from_shape[3] = {4, 8, 8};
unsigned config16_tpose_out_to_shape[3] = {4, 8, 8};
unsigned config16_tpose_out_perm[3] = {0, 1, 2};
unsigned config16_tpose_out_perm_strides[3] = {64, 8, 1};

const unsigned* const config16_tpose_out::from_shape = config16_tpose_out_from_shape;
const unsigned* const config16_tpose_out::to_shape = config16_tpose_out_to_shape;
const unsigned* const config16_tpose_out::perm = config16_tpose_out_perm;
const unsigned* const config16_tpose_out::perm_strides = config16_tpose_out_perm_strides;



struct config16 {
    typedef config16_tpose_inp0 tpose_inp0_config;
    typedef config16_tpose_inp1 tpose_inp1_config;
    typedef config16_tpose_out tpose_out_conf;

    typedef bit_block_0_attn_scores_accum_t accum_t;

    // Layer Sizes
    static const unsigned n_free0 = 8;
    static const unsigned n_free1 = 8;
    static const unsigned n_contract = 8;
    static const unsigned n_inplace = 4;

    // Resource reuse info
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned strategy = nnet::latency;
    static const unsigned reuse_factor = 1;
    static const unsigned multiplier_limit = 2048;
    static const bool store_weights_in_bram = false; // NOT USED

    template <class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};

// bit_block_0_attn_Wv
struct config18_tpose_inp {
    static const unsigned dims = 2;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config18_tpose_inp_from_shape[2] = {8, 32};
unsigned config18_tpose_inp_to_shape[2] = {8, 32};
unsigned config18_tpose_inp_perm[2] = {0, 1};
unsigned config18_tpose_inp_perm_strides[2] = {32, 1};

const unsigned* const config18_tpose_inp::from_shape = config18_tpose_inp_from_shape;
const unsigned* const config18_tpose_inp::to_shape = config18_tpose_inp_to_shape;
const unsigned* const config18_tpose_inp::perm = config18_tpose_inp_perm;
const unsigned* const config18_tpose_inp::perm_strides = config18_tpose_inp_perm_strides;


struct config18_tpose_out {
    static const unsigned dims = 3;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config18_tpose_out_from_shape[3] = {8, 4, 8};
unsigned config18_tpose_out_to_shape[3] = {8, 4, 8};
unsigned config18_tpose_out_perm[3] = {0, 1, 2};
unsigned config18_tpose_out_perm_strides[3] = {32, 8, 1};

const unsigned* const config18_tpose_out::from_shape = config18_tpose_out_from_shape;
const unsigned* const config18_tpose_out::to_shape = config18_tpose_out_to_shape;
const unsigned* const config18_tpose_out::perm = config18_tpose_out_perm;
const unsigned* const config18_tpose_out::perm_strides = config18_tpose_out_perm_strides;


struct config18_dense : nnet::dense_config {
    static const unsigned n_in = 32;
    static const unsigned n_out = 32;
    static const unsigned reuse_factor = 1;
    static const unsigned strategy = nnet::latency;
    static const unsigned n_zeros = 0;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in * n_out, reuse_factor) - n_zeros / reuse_factor;
    typedef bit_block_0_attn_Wv_accum_t accum_t;
    typedef model_default_t bias_t;
    typedef model_default_t weight_t;
    template<class data_T, class res_T, class CONFIG_T>
    using kernel = nnet::DenseLatency<data_T, res_T, CONFIG_T>;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};



struct config18 {
    typedef config18_tpose_inp tpose_inp_conf;
    typedef config18_tpose_out tpose_out_conf;

    typedef bit_block_0_attn_Wv_accum_t accum_t;
    typedef model_default_t bias_t;

    typedef config18_dense dense_conf;

    // Layer Sizes
    static const unsigned n_free_data = 8;
    static const unsigned n_free_kernel = 32;
    static const unsigned n_contract = 32;
    static const unsigned n_inplace = 1;

    // Resource reuse info
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned strategy = nnet::latency;
    static const unsigned reuse_factor = 1;
    static const unsigned parallelization_factor = 8; // Only useful when n_inplace > 1
};

// bit_block_0_attn_softmax
struct softmax_config19 : nnet::activ_config {
    static const unsigned n_in = 256;
    static const unsigned n_slice = 8;
    static const unsigned n_outer = 32;
    static const unsigned n_inner = 1;
    static const unsigned parallelization_factor = 32;
    static const unsigned exp_table_size = 1024;
    static const unsigned inv_table_size = 4096;
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned reuse_factor = 1;
    static const unsigned axis = -1;
    static const nnet::softmax_implementation implementation = nnet::softmax_implementation::stable;
    static constexpr float exp_scale = 0.35355339059327373;
    typedef bit_block_0_attn_softmax_exp_table_t exp_table_t;
    typedef bit_block_0_attn_softmax_inv_table_t inv_table_t;
    typedef bit_block_0_attn_softmax_accum_t accum_t;
    typedef bit_block_0_attn_softmax_inv_inp_t inv_inp_t;
    typedef bit_block_0_attn_softmax_inp_norm_t inp_norm_t;
};

// bit_block_0_attn_Wv_affine
struct config21 : nnet::batchnorm_config {
    static const unsigned n_in = 8*4*8;
    static const unsigned n_filt = 8;
    static const unsigned n_scale_bias = (n_filt == -1) ? n_in : n_filt;
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned reuse_factor = 1;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in, reuse_factor);
    static const bool store_weights_in_bram = false;
    typedef bit_block_0_attn_Wv_affine_bias_t bias_t;
    typedef bit_block_0_attn_Wv_affine_scale_t scale_t;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};

// bit_block_0_attn_ctx
struct config24_tpose_inp0 {
    static const unsigned dims = 3;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config24_tpose_inp0_from_shape[3] = {4, 8, 8};
unsigned config24_tpose_inp0_to_shape[3] = {4, 8, 8};
unsigned config24_tpose_inp0_perm[3] = {0, 1, 2};
unsigned config24_tpose_inp0_perm_strides[3] = {64, 8, 1};

const unsigned* const config24_tpose_inp0::from_shape = config24_tpose_inp0_from_shape;
const unsigned* const config24_tpose_inp0::to_shape = config24_tpose_inp0_to_shape;
const unsigned* const config24_tpose_inp0::perm = config24_tpose_inp0_perm;
const unsigned* const config24_tpose_inp0::perm_strides = config24_tpose_inp0_perm_strides;


struct config24_tpose_inp1 {
    static const unsigned dims = 3;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config24_tpose_inp1_from_shape[3] = {8, 4, 8};
unsigned config24_tpose_inp1_to_shape[3] = {4, 8, 8};
unsigned config24_tpose_inp1_perm[3] = {1, 2, 0};
unsigned config24_tpose_inp1_perm_strides[3] = {8, 1, 32};

const unsigned* const config24_tpose_inp1::from_shape = config24_tpose_inp1_from_shape;
const unsigned* const config24_tpose_inp1::to_shape = config24_tpose_inp1_to_shape;
const unsigned* const config24_tpose_inp1::perm = config24_tpose_inp1_perm;
const unsigned* const config24_tpose_inp1::perm_strides = config24_tpose_inp1_perm_strides;


struct config24_tpose_out {
    static const unsigned dims = 3;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config24_tpose_out_from_shape[3] = {4, 8, 8};
unsigned config24_tpose_out_to_shape[3] = {8, 4, 8};
unsigned config24_tpose_out_perm[3] = {1, 0, 2};
unsigned config24_tpose_out_perm_strides[3] = {8, 64, 1};

const unsigned* const config24_tpose_out::from_shape = config24_tpose_out_from_shape;
const unsigned* const config24_tpose_out::to_shape = config24_tpose_out_to_shape;
const unsigned* const config24_tpose_out::perm = config24_tpose_out_perm;
const unsigned* const config24_tpose_out::perm_strides = config24_tpose_out_perm_strides;



struct config24 {
    typedef config24_tpose_inp0 tpose_inp0_config;
    typedef config24_tpose_inp1 tpose_inp1_config;
    typedef config24_tpose_out tpose_out_conf;

    typedef bit_block_0_attn_ctx_accum_t accum_t;

    // Layer Sizes
    static const unsigned n_free0 = 8;
    static const unsigned n_free1 = 8;
    static const unsigned n_contract = 8;
    static const unsigned n_inplace = 4;

    // Resource reuse info
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned strategy = nnet::latency;
    static const unsigned reuse_factor = 1;
    static const unsigned multiplier_limit = 2048;
    static const bool store_weights_in_bram = false; // NOT USED

    template <class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};

// bit_block_0_attn_Wo
struct config26_tpose_inp {
    static const unsigned dims = 3;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config26_tpose_inp_from_shape[3] = {8, 4, 8};
unsigned config26_tpose_inp_to_shape[3] = {8, 4, 8};
unsigned config26_tpose_inp_perm[3] = {0, 1, 2};
unsigned config26_tpose_inp_perm_strides[3] = {32, 8, 1};

const unsigned* const config26_tpose_inp::from_shape = config26_tpose_inp_from_shape;
const unsigned* const config26_tpose_inp::to_shape = config26_tpose_inp_to_shape;
const unsigned* const config26_tpose_inp::perm = config26_tpose_inp_perm;
const unsigned* const config26_tpose_inp::perm_strides = config26_tpose_inp_perm_strides;


struct config26_tpose_out {
    static const unsigned dims = 2;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config26_tpose_out_from_shape[2] = {8, 32};
unsigned config26_tpose_out_to_shape[2] = {8, 32};
unsigned config26_tpose_out_perm[2] = {0, 1};
unsigned config26_tpose_out_perm_strides[2] = {32, 1};

const unsigned* const config26_tpose_out::from_shape = config26_tpose_out_from_shape;
const unsigned* const config26_tpose_out::to_shape = config26_tpose_out_to_shape;
const unsigned* const config26_tpose_out::perm = config26_tpose_out_perm;
const unsigned* const config26_tpose_out::perm_strides = config26_tpose_out_perm_strides;


struct config26_dense : nnet::dense_config {
    static const unsigned n_in = 32;
    static const unsigned n_out = 32;
    static const unsigned reuse_factor = 1;
    static const unsigned strategy = nnet::latency;
    static const unsigned n_zeros = 0;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in * n_out, reuse_factor) - n_zeros / reuse_factor;
    typedef bit_block_0_attn_Wo_accum_t accum_t;
    typedef model_default_t bias_t;
    typedef model_default_t weight_t;
    template<class data_T, class res_T, class CONFIG_T>
    using kernel = nnet::DenseLatency<data_T, res_T, CONFIG_T>;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};



struct config26 {
    typedef config26_tpose_inp tpose_inp_conf;
    typedef config26_tpose_out tpose_out_conf;

    typedef bit_block_0_attn_Wo_accum_t accum_t;
    typedef model_default_t bias_t;

    typedef config26_dense dense_conf;

    // Layer Sizes
    static const unsigned n_free_data = 8;
    static const unsigned n_free_kernel = 32;
    static const unsigned n_contract = 32;
    static const unsigned n_inplace = 1;

    // Resource reuse info
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned strategy = nnet::latency;
    static const unsigned reuse_factor = 1;
    static const unsigned parallelization_factor = 8; // Only useful when n_inplace > 1
};

// bit_block_0_attn_Wo_affine
struct config28 : nnet::batchnorm_config {
    static const unsigned n_in = 8*32;
    static const unsigned n_filt = 32;
    static const unsigned n_scale_bias = (n_filt == -1) ? n_in : n_filt;
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned reuse_factor = 1;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in, reuse_factor);
    static const bool store_weights_in_bram = false;
    typedef bit_block_0_attn_Wo_affine_bias_t bias_t;
    typedef bit_block_0_attn_Wo_affine_scale_t scale_t;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};

// bit_block_0_add_attn
struct config29 : nnet::merge_config {
    static const unsigned n_elem = 8*32;
    static const unsigned n_elem1 = 8*32;
    static const unsigned n_elem2 = 8*32;
    static const unsigned reuse_factor = 1;
};

// bit_block_0_ffn_fc1
struct config31_tpose_inp {
    static const unsigned dims = 2;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config31_tpose_inp_from_shape[2] = {8, 32};
unsigned config31_tpose_inp_to_shape[2] = {8, 32};
unsigned config31_tpose_inp_perm[2] = {0, 1};
unsigned config31_tpose_inp_perm_strides[2] = {32, 1};

const unsigned* const config31_tpose_inp::from_shape = config31_tpose_inp_from_shape;
const unsigned* const config31_tpose_inp::to_shape = config31_tpose_inp_to_shape;
const unsigned* const config31_tpose_inp::perm = config31_tpose_inp_perm;
const unsigned* const config31_tpose_inp::perm_strides = config31_tpose_inp_perm_strides;


struct config31_tpose_out {
    static const unsigned dims = 2;
    static const unsigned N = 512;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config31_tpose_out_from_shape[2] = {8, 64};
unsigned config31_tpose_out_to_shape[2] = {8, 64};
unsigned config31_tpose_out_perm[2] = {0, 1};
unsigned config31_tpose_out_perm_strides[2] = {64, 1};

const unsigned* const config31_tpose_out::from_shape = config31_tpose_out_from_shape;
const unsigned* const config31_tpose_out::to_shape = config31_tpose_out_to_shape;
const unsigned* const config31_tpose_out::perm = config31_tpose_out_perm;
const unsigned* const config31_tpose_out::perm_strides = config31_tpose_out_perm_strides;


struct config31_dense : nnet::dense_config {
    static const unsigned n_in = 32;
    static const unsigned n_out = 64;
    static const unsigned reuse_factor = 1;
    static const unsigned strategy = nnet::latency;
    static const unsigned n_zeros = 0;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in * n_out, reuse_factor) - n_zeros / reuse_factor;
    typedef bit_block_0_ffn_fc1_accum_t accum_t;
    typedef bit_block_0_ffn_fc1_bias_t bias_t;
    typedef bit_block_0_ffn_fc1_weight_t weight_t;
    template<class data_T, class res_T, class CONFIG_T>
    using kernel = nnet::DenseLatency<data_T, res_T, CONFIG_T>;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};



struct config31 {
    typedef config31_tpose_inp tpose_inp_conf;
    typedef config31_tpose_out tpose_out_conf;

    typedef bit_block_0_ffn_fc1_accum_t accum_t;
    typedef bit_block_0_ffn_fc1_bias_t bias_t;

    typedef config31_dense dense_conf;

    // Layer Sizes
    static const unsigned n_free_data = 8;
    static const unsigned n_free_kernel = 64;
    static const unsigned n_contract = 32;
    static const unsigned n_inplace = 1;

    // Resource reuse info
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned strategy = nnet::latency;
    static const unsigned reuse_factor = 1;
    static const unsigned parallelization_factor = 8; // Only useful when n_inplace > 1
};

// bit_block_0_ffn_fc1_affine
struct config33 : nnet::batchnorm_config {
    static const unsigned n_in = 8*64;
    static const unsigned n_filt = 64;
    static const unsigned n_scale_bias = (n_filt == -1) ? n_in : n_filt;
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned reuse_factor = 1;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in, reuse_factor);
    static const bool store_weights_in_bram = false;
    typedef bit_block_0_ffn_fc1_affine_bias_t bias_t;
    typedef bit_block_0_ffn_fc1_affine_scale_t scale_t;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};

// bit_block_0_ffn_act
struct relu_config34 : nnet::activ_config {
    static const unsigned n_in = 512;
    static const unsigned table_size = 1048576;
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned reuse_factor = 1;
    typedef bit_block_0_ffn_act_table_t table_t;
};

// bit_block_0_ffn_fc2
struct config36_tpose_inp {
    static const unsigned dims = 2;
    static const unsigned N = 512;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config36_tpose_inp_from_shape[2] = {8, 64};
unsigned config36_tpose_inp_to_shape[2] = {8, 64};
unsigned config36_tpose_inp_perm[2] = {0, 1};
unsigned config36_tpose_inp_perm_strides[2] = {64, 1};

const unsigned* const config36_tpose_inp::from_shape = config36_tpose_inp_from_shape;
const unsigned* const config36_tpose_inp::to_shape = config36_tpose_inp_to_shape;
const unsigned* const config36_tpose_inp::perm = config36_tpose_inp_perm;
const unsigned* const config36_tpose_inp::perm_strides = config36_tpose_inp_perm_strides;


struct config36_tpose_out {
    static const unsigned dims = 2;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config36_tpose_out_from_shape[2] = {8, 32};
unsigned config36_tpose_out_to_shape[2] = {8, 32};
unsigned config36_tpose_out_perm[2] = {0, 1};
unsigned config36_tpose_out_perm_strides[2] = {32, 1};

const unsigned* const config36_tpose_out::from_shape = config36_tpose_out_from_shape;
const unsigned* const config36_tpose_out::to_shape = config36_tpose_out_to_shape;
const unsigned* const config36_tpose_out::perm = config36_tpose_out_perm;
const unsigned* const config36_tpose_out::perm_strides = config36_tpose_out_perm_strides;


struct config36_dense : nnet::dense_config {
    static const unsigned n_in = 64;
    static const unsigned n_out = 32;
    static const unsigned reuse_factor = 1;
    static const unsigned strategy = nnet::latency;
    static const unsigned n_zeros = 0;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in * n_out, reuse_factor) - n_zeros / reuse_factor;
    typedef bit_block_0_ffn_fc2_accum_t accum_t;
    typedef bit_block_0_ffn_fc2_bias_t bias_t;
    typedef bit_block_0_ffn_fc2_weight_t weight_t;
    template<class data_T, class res_T, class CONFIG_T>
    using kernel = nnet::DenseLatency<data_T, res_T, CONFIG_T>;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};



struct config36 {
    typedef config36_tpose_inp tpose_inp_conf;
    typedef config36_tpose_out tpose_out_conf;

    typedef bit_block_0_ffn_fc2_accum_t accum_t;
    typedef bit_block_0_ffn_fc2_bias_t bias_t;

    typedef config36_dense dense_conf;

    // Layer Sizes
    static const unsigned n_free_data = 8;
    static const unsigned n_free_kernel = 32;
    static const unsigned n_contract = 64;
    static const unsigned n_inplace = 1;

    // Resource reuse info
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned strategy = nnet::latency;
    static const unsigned reuse_factor = 1;
    static const unsigned parallelization_factor = 8; // Only useful when n_inplace > 1
};

// bit_block_0_ffn_fc2_affine
struct config38 : nnet::batchnorm_config {
    static const unsigned n_in = 8*32;
    static const unsigned n_filt = 32;
    static const unsigned n_scale_bias = (n_filt == -1) ? n_in : n_filt;
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned reuse_factor = 1;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in, reuse_factor);
    static const bool store_weights_in_bram = false;
    typedef bit_block_0_ffn_fc2_affine_bias_t bias_t;
    typedef bit_block_0_ffn_fc2_affine_scale_t scale_t;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};

// bit_block_0_add_ffn
struct config39 : nnet::merge_config {
    static const unsigned n_elem = 8*32;
    static const unsigned n_elem1 = 8*32;
    static const unsigned n_elem2 = 8*32;
    static const unsigned reuse_factor = 1;
};

// bit_block_1_attn_Wq
struct config41_tpose_inp {
    static const unsigned dims = 2;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config41_tpose_inp_from_shape[2] = {8, 32};
unsigned config41_tpose_inp_to_shape[2] = {8, 32};
unsigned config41_tpose_inp_perm[2] = {0, 1};
unsigned config41_tpose_inp_perm_strides[2] = {32, 1};

const unsigned* const config41_tpose_inp::from_shape = config41_tpose_inp_from_shape;
const unsigned* const config41_tpose_inp::to_shape = config41_tpose_inp_to_shape;
const unsigned* const config41_tpose_inp::perm = config41_tpose_inp_perm;
const unsigned* const config41_tpose_inp::perm_strides = config41_tpose_inp_perm_strides;


struct config41_tpose_out {
    static const unsigned dims = 3;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config41_tpose_out_from_shape[3] = {8, 4, 8};
unsigned config41_tpose_out_to_shape[3] = {8, 4, 8};
unsigned config41_tpose_out_perm[3] = {0, 1, 2};
unsigned config41_tpose_out_perm_strides[3] = {32, 8, 1};

const unsigned* const config41_tpose_out::from_shape = config41_tpose_out_from_shape;
const unsigned* const config41_tpose_out::to_shape = config41_tpose_out_to_shape;
const unsigned* const config41_tpose_out::perm = config41_tpose_out_perm;
const unsigned* const config41_tpose_out::perm_strides = config41_tpose_out_perm_strides;


struct config41_dense : nnet::dense_config {
    static const unsigned n_in = 32;
    static const unsigned n_out = 32;
    static const unsigned reuse_factor = 1;
    static const unsigned strategy = nnet::latency;
    static const unsigned n_zeros = 0;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in * n_out, reuse_factor) - n_zeros / reuse_factor;
    typedef bit_block_1_attn_Wq_accum_t accum_t;
    typedef model_default_t bias_t;
    typedef model_default_t weight_t;
    template<class data_T, class res_T, class CONFIG_T>
    using kernel = nnet::DenseLatency<data_T, res_T, CONFIG_T>;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};



struct config41 {
    typedef config41_tpose_inp tpose_inp_conf;
    typedef config41_tpose_out tpose_out_conf;

    typedef bit_block_1_attn_Wq_accum_t accum_t;
    typedef model_default_t bias_t;

    typedef config41_dense dense_conf;

    // Layer Sizes
    static const unsigned n_free_data = 8;
    static const unsigned n_free_kernel = 32;
    static const unsigned n_contract = 32;
    static const unsigned n_inplace = 1;

    // Resource reuse info
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned strategy = nnet::latency;
    static const unsigned reuse_factor = 1;
    static const unsigned parallelization_factor = 8; // Only useful when n_inplace > 1
};

// bit_block_1_attn_Wk
struct config43_tpose_inp {
    static const unsigned dims = 2;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config43_tpose_inp_from_shape[2] = {8, 32};
unsigned config43_tpose_inp_to_shape[2] = {8, 32};
unsigned config43_tpose_inp_perm[2] = {0, 1};
unsigned config43_tpose_inp_perm_strides[2] = {32, 1};

const unsigned* const config43_tpose_inp::from_shape = config43_tpose_inp_from_shape;
const unsigned* const config43_tpose_inp::to_shape = config43_tpose_inp_to_shape;
const unsigned* const config43_tpose_inp::perm = config43_tpose_inp_perm;
const unsigned* const config43_tpose_inp::perm_strides = config43_tpose_inp_perm_strides;


struct config43_tpose_out {
    static const unsigned dims = 3;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config43_tpose_out_from_shape[3] = {8, 4, 8};
unsigned config43_tpose_out_to_shape[3] = {8, 4, 8};
unsigned config43_tpose_out_perm[3] = {0, 1, 2};
unsigned config43_tpose_out_perm_strides[3] = {32, 8, 1};

const unsigned* const config43_tpose_out::from_shape = config43_tpose_out_from_shape;
const unsigned* const config43_tpose_out::to_shape = config43_tpose_out_to_shape;
const unsigned* const config43_tpose_out::perm = config43_tpose_out_perm;
const unsigned* const config43_tpose_out::perm_strides = config43_tpose_out_perm_strides;


struct config43_dense : nnet::dense_config {
    static const unsigned n_in = 32;
    static const unsigned n_out = 32;
    static const unsigned reuse_factor = 1;
    static const unsigned strategy = nnet::latency;
    static const unsigned n_zeros = 0;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in * n_out, reuse_factor) - n_zeros / reuse_factor;
    typedef bit_block_1_attn_Wk_accum_t accum_t;
    typedef model_default_t bias_t;
    typedef model_default_t weight_t;
    template<class data_T, class res_T, class CONFIG_T>
    using kernel = nnet::DenseLatency<data_T, res_T, CONFIG_T>;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};



struct config43 {
    typedef config43_tpose_inp tpose_inp_conf;
    typedef config43_tpose_out tpose_out_conf;

    typedef bit_block_1_attn_Wk_accum_t accum_t;
    typedef model_default_t bias_t;

    typedef config43_dense dense_conf;

    // Layer Sizes
    static const unsigned n_free_data = 8;
    static const unsigned n_free_kernel = 32;
    static const unsigned n_contract = 32;
    static const unsigned n_inplace = 1;

    // Resource reuse info
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned strategy = nnet::latency;
    static const unsigned reuse_factor = 1;
    static const unsigned parallelization_factor = 8; // Only useful when n_inplace > 1
};

// bit_block_1_attn_Wq_affine
struct config45 : nnet::batchnorm_config {
    static const unsigned n_in = 8*4*8;
    static const unsigned n_filt = 8;
    static const unsigned n_scale_bias = (n_filt == -1) ? n_in : n_filt;
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned reuse_factor = 1;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in, reuse_factor);
    static const bool store_weights_in_bram = false;
    typedef bit_block_1_attn_Wq_affine_bias_t bias_t;
    typedef bit_block_1_attn_Wq_affine_scale_t scale_t;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};

// bit_block_1_attn_Wk_affine
struct config47 : nnet::batchnorm_config {
    static const unsigned n_in = 8*4*8;
    static const unsigned n_filt = 8;
    static const unsigned n_scale_bias = (n_filt == -1) ? n_in : n_filt;
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned reuse_factor = 1;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in, reuse_factor);
    static const bool store_weights_in_bram = false;
    typedef bit_block_1_attn_Wk_affine_bias_t bias_t;
    typedef bit_block_1_attn_Wk_affine_scale_t scale_t;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};

// bit_block_1_attn_scores
struct config50_tpose_inp0 {
    static const unsigned dims = 3;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config50_tpose_inp0_from_shape[3] = {8, 4, 8};
unsigned config50_tpose_inp0_to_shape[3] = {4, 8, 8};
unsigned config50_tpose_inp0_perm[3] = {1, 0, 2};
unsigned config50_tpose_inp0_perm_strides[3] = {8, 32, 1};

const unsigned* const config50_tpose_inp0::from_shape = config50_tpose_inp0_from_shape;
const unsigned* const config50_tpose_inp0::to_shape = config50_tpose_inp0_to_shape;
const unsigned* const config50_tpose_inp0::perm = config50_tpose_inp0_perm;
const unsigned* const config50_tpose_inp0::perm_strides = config50_tpose_inp0_perm_strides;


struct config50_tpose_inp1 {
    static const unsigned dims = 3;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config50_tpose_inp1_from_shape[3] = {8, 4, 8};
unsigned config50_tpose_inp1_to_shape[3] = {4, 8, 8};
unsigned config50_tpose_inp1_perm[3] = {1, 0, 2};
unsigned config50_tpose_inp1_perm_strides[3] = {8, 32, 1};

const unsigned* const config50_tpose_inp1::from_shape = config50_tpose_inp1_from_shape;
const unsigned* const config50_tpose_inp1::to_shape = config50_tpose_inp1_to_shape;
const unsigned* const config50_tpose_inp1::perm = config50_tpose_inp1_perm;
const unsigned* const config50_tpose_inp1::perm_strides = config50_tpose_inp1_perm_strides;


struct config50_tpose_out {
    static const unsigned dims = 3;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config50_tpose_out_from_shape[3] = {4, 8, 8};
unsigned config50_tpose_out_to_shape[3] = {4, 8, 8};
unsigned config50_tpose_out_perm[3] = {0, 1, 2};
unsigned config50_tpose_out_perm_strides[3] = {64, 8, 1};

const unsigned* const config50_tpose_out::from_shape = config50_tpose_out_from_shape;
const unsigned* const config50_tpose_out::to_shape = config50_tpose_out_to_shape;
const unsigned* const config50_tpose_out::perm = config50_tpose_out_perm;
const unsigned* const config50_tpose_out::perm_strides = config50_tpose_out_perm_strides;



struct config50 {
    typedef config50_tpose_inp0 tpose_inp0_config;
    typedef config50_tpose_inp1 tpose_inp1_config;
    typedef config50_tpose_out tpose_out_conf;

    typedef bit_block_1_attn_scores_accum_t accum_t;

    // Layer Sizes
    static const unsigned n_free0 = 8;
    static const unsigned n_free1 = 8;
    static const unsigned n_contract = 8;
    static const unsigned n_inplace = 4;

    // Resource reuse info
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned strategy = nnet::latency;
    static const unsigned reuse_factor = 1;
    static const unsigned multiplier_limit = 2048;
    static const bool store_weights_in_bram = false; // NOT USED

    template <class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};

// bit_block_1_attn_Wv
struct config52_tpose_inp {
    static const unsigned dims = 2;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config52_tpose_inp_from_shape[2] = {8, 32};
unsigned config52_tpose_inp_to_shape[2] = {8, 32};
unsigned config52_tpose_inp_perm[2] = {0, 1};
unsigned config52_tpose_inp_perm_strides[2] = {32, 1};

const unsigned* const config52_tpose_inp::from_shape = config52_tpose_inp_from_shape;
const unsigned* const config52_tpose_inp::to_shape = config52_tpose_inp_to_shape;
const unsigned* const config52_tpose_inp::perm = config52_tpose_inp_perm;
const unsigned* const config52_tpose_inp::perm_strides = config52_tpose_inp_perm_strides;


struct config52_tpose_out {
    static const unsigned dims = 3;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config52_tpose_out_from_shape[3] = {8, 4, 8};
unsigned config52_tpose_out_to_shape[3] = {8, 4, 8};
unsigned config52_tpose_out_perm[3] = {0, 1, 2};
unsigned config52_tpose_out_perm_strides[3] = {32, 8, 1};

const unsigned* const config52_tpose_out::from_shape = config52_tpose_out_from_shape;
const unsigned* const config52_tpose_out::to_shape = config52_tpose_out_to_shape;
const unsigned* const config52_tpose_out::perm = config52_tpose_out_perm;
const unsigned* const config52_tpose_out::perm_strides = config52_tpose_out_perm_strides;


struct config52_dense : nnet::dense_config {
    static const unsigned n_in = 32;
    static const unsigned n_out = 32;
    static const unsigned reuse_factor = 1;
    static const unsigned strategy = nnet::latency;
    static const unsigned n_zeros = 0;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in * n_out, reuse_factor) - n_zeros / reuse_factor;
    typedef bit_block_1_attn_Wv_accum_t accum_t;
    typedef model_default_t bias_t;
    typedef model_default_t weight_t;
    template<class data_T, class res_T, class CONFIG_T>
    using kernel = nnet::DenseLatency<data_T, res_T, CONFIG_T>;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};



struct config52 {
    typedef config52_tpose_inp tpose_inp_conf;
    typedef config52_tpose_out tpose_out_conf;

    typedef bit_block_1_attn_Wv_accum_t accum_t;
    typedef model_default_t bias_t;

    typedef config52_dense dense_conf;

    // Layer Sizes
    static const unsigned n_free_data = 8;
    static const unsigned n_free_kernel = 32;
    static const unsigned n_contract = 32;
    static const unsigned n_inplace = 1;

    // Resource reuse info
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned strategy = nnet::latency;
    static const unsigned reuse_factor = 1;
    static const unsigned parallelization_factor = 8; // Only useful when n_inplace > 1
};

// bit_block_1_attn_softmax
struct softmax_config53 : nnet::activ_config {
    static const unsigned n_in = 256;
    static const unsigned n_slice = 8;
    static const unsigned n_outer = 32;
    static const unsigned n_inner = 1;
    static const unsigned parallelization_factor = 32;
    static const unsigned exp_table_size = 1024;
    static const unsigned inv_table_size = 4096;
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned reuse_factor = 1;
    static const unsigned axis = -1;
    static const nnet::softmax_implementation implementation = nnet::softmax_implementation::stable;
    static constexpr float exp_scale = 0.35355339059327373;
    typedef bit_block_1_attn_softmax_exp_table_t exp_table_t;
    typedef bit_block_1_attn_softmax_inv_table_t inv_table_t;
    typedef bit_block_1_attn_softmax_accum_t accum_t;
    typedef bit_block_1_attn_softmax_inv_inp_t inv_inp_t;
    typedef bit_block_1_attn_softmax_inp_norm_t inp_norm_t;
};

// bit_block_1_attn_Wv_affine
struct config55 : nnet::batchnorm_config {
    static const unsigned n_in = 8*4*8;
    static const unsigned n_filt = 8;
    static const unsigned n_scale_bias = (n_filt == -1) ? n_in : n_filt;
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned reuse_factor = 1;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in, reuse_factor);
    static const bool store_weights_in_bram = false;
    typedef bit_block_1_attn_Wv_affine_bias_t bias_t;
    typedef bit_block_1_attn_Wv_affine_scale_t scale_t;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};

// bit_block_1_attn_ctx
struct config58_tpose_inp0 {
    static const unsigned dims = 3;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config58_tpose_inp0_from_shape[3] = {4, 8, 8};
unsigned config58_tpose_inp0_to_shape[3] = {4, 8, 8};
unsigned config58_tpose_inp0_perm[3] = {0, 1, 2};
unsigned config58_tpose_inp0_perm_strides[3] = {64, 8, 1};

const unsigned* const config58_tpose_inp0::from_shape = config58_tpose_inp0_from_shape;
const unsigned* const config58_tpose_inp0::to_shape = config58_tpose_inp0_to_shape;
const unsigned* const config58_tpose_inp0::perm = config58_tpose_inp0_perm;
const unsigned* const config58_tpose_inp0::perm_strides = config58_tpose_inp0_perm_strides;


struct config58_tpose_inp1 {
    static const unsigned dims = 3;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config58_tpose_inp1_from_shape[3] = {8, 4, 8};
unsigned config58_tpose_inp1_to_shape[3] = {4, 8, 8};
unsigned config58_tpose_inp1_perm[3] = {1, 2, 0};
unsigned config58_tpose_inp1_perm_strides[3] = {8, 1, 32};

const unsigned* const config58_tpose_inp1::from_shape = config58_tpose_inp1_from_shape;
const unsigned* const config58_tpose_inp1::to_shape = config58_tpose_inp1_to_shape;
const unsigned* const config58_tpose_inp1::perm = config58_tpose_inp1_perm;
const unsigned* const config58_tpose_inp1::perm_strides = config58_tpose_inp1_perm_strides;


struct config58_tpose_out {
    static const unsigned dims = 3;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config58_tpose_out_from_shape[3] = {4, 8, 8};
unsigned config58_tpose_out_to_shape[3] = {8, 4, 8};
unsigned config58_tpose_out_perm[3] = {1, 0, 2};
unsigned config58_tpose_out_perm_strides[3] = {8, 64, 1};

const unsigned* const config58_tpose_out::from_shape = config58_tpose_out_from_shape;
const unsigned* const config58_tpose_out::to_shape = config58_tpose_out_to_shape;
const unsigned* const config58_tpose_out::perm = config58_tpose_out_perm;
const unsigned* const config58_tpose_out::perm_strides = config58_tpose_out_perm_strides;



struct config58 {
    typedef config58_tpose_inp0 tpose_inp0_config;
    typedef config58_tpose_inp1 tpose_inp1_config;
    typedef config58_tpose_out tpose_out_conf;

    typedef bit_block_1_attn_ctx_accum_t accum_t;

    // Layer Sizes
    static const unsigned n_free0 = 8;
    static const unsigned n_free1 = 8;
    static const unsigned n_contract = 8;
    static const unsigned n_inplace = 4;

    // Resource reuse info
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned strategy = nnet::latency;
    static const unsigned reuse_factor = 1;
    static const unsigned multiplier_limit = 2048;
    static const bool store_weights_in_bram = false; // NOT USED

    template <class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};

// bit_block_1_attn_Wo
struct config60_tpose_inp {
    static const unsigned dims = 3;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config60_tpose_inp_from_shape[3] = {8, 4, 8};
unsigned config60_tpose_inp_to_shape[3] = {8, 4, 8};
unsigned config60_tpose_inp_perm[3] = {0, 1, 2};
unsigned config60_tpose_inp_perm_strides[3] = {32, 8, 1};

const unsigned* const config60_tpose_inp::from_shape = config60_tpose_inp_from_shape;
const unsigned* const config60_tpose_inp::to_shape = config60_tpose_inp_to_shape;
const unsigned* const config60_tpose_inp::perm = config60_tpose_inp_perm;
const unsigned* const config60_tpose_inp::perm_strides = config60_tpose_inp_perm_strides;


struct config60_tpose_out {
    static const unsigned dims = 2;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config60_tpose_out_from_shape[2] = {8, 32};
unsigned config60_tpose_out_to_shape[2] = {8, 32};
unsigned config60_tpose_out_perm[2] = {0, 1};
unsigned config60_tpose_out_perm_strides[2] = {32, 1};

const unsigned* const config60_tpose_out::from_shape = config60_tpose_out_from_shape;
const unsigned* const config60_tpose_out::to_shape = config60_tpose_out_to_shape;
const unsigned* const config60_tpose_out::perm = config60_tpose_out_perm;
const unsigned* const config60_tpose_out::perm_strides = config60_tpose_out_perm_strides;


struct config60_dense : nnet::dense_config {
    static const unsigned n_in = 32;
    static const unsigned n_out = 32;
    static const unsigned reuse_factor = 1;
    static const unsigned strategy = nnet::latency;
    static const unsigned n_zeros = 0;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in * n_out, reuse_factor) - n_zeros / reuse_factor;
    typedef bit_block_1_attn_Wo_accum_t accum_t;
    typedef model_default_t bias_t;
    typedef model_default_t weight_t;
    template<class data_T, class res_T, class CONFIG_T>
    using kernel = nnet::DenseLatency<data_T, res_T, CONFIG_T>;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};



struct config60 {
    typedef config60_tpose_inp tpose_inp_conf;
    typedef config60_tpose_out tpose_out_conf;

    typedef bit_block_1_attn_Wo_accum_t accum_t;
    typedef model_default_t bias_t;

    typedef config60_dense dense_conf;

    // Layer Sizes
    static const unsigned n_free_data = 8;
    static const unsigned n_free_kernel = 32;
    static const unsigned n_contract = 32;
    static const unsigned n_inplace = 1;

    // Resource reuse info
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned strategy = nnet::latency;
    static const unsigned reuse_factor = 1;
    static const unsigned parallelization_factor = 8; // Only useful when n_inplace > 1
};

// bit_block_1_attn_Wo_affine
struct config62 : nnet::batchnorm_config {
    static const unsigned n_in = 8*32;
    static const unsigned n_filt = 32;
    static const unsigned n_scale_bias = (n_filt == -1) ? n_in : n_filt;
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned reuse_factor = 1;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in, reuse_factor);
    static const bool store_weights_in_bram = false;
    typedef bit_block_1_attn_Wo_affine_bias_t bias_t;
    typedef bit_block_1_attn_Wo_affine_scale_t scale_t;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};

// bit_block_1_add_attn
struct config63 : nnet::merge_config {
    static const unsigned n_elem = 8*32;
    static const unsigned n_elem1 = 8*32;
    static const unsigned n_elem2 = 8*32;
    static const unsigned reuse_factor = 1;
};

// bit_block_1_ffn_fc1
struct config65_tpose_inp {
    static const unsigned dims = 2;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config65_tpose_inp_from_shape[2] = {8, 32};
unsigned config65_tpose_inp_to_shape[2] = {8, 32};
unsigned config65_tpose_inp_perm[2] = {0, 1};
unsigned config65_tpose_inp_perm_strides[2] = {32, 1};

const unsigned* const config65_tpose_inp::from_shape = config65_tpose_inp_from_shape;
const unsigned* const config65_tpose_inp::to_shape = config65_tpose_inp_to_shape;
const unsigned* const config65_tpose_inp::perm = config65_tpose_inp_perm;
const unsigned* const config65_tpose_inp::perm_strides = config65_tpose_inp_perm_strides;


struct config65_tpose_out {
    static const unsigned dims = 2;
    static const unsigned N = 512;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config65_tpose_out_from_shape[2] = {8, 64};
unsigned config65_tpose_out_to_shape[2] = {8, 64};
unsigned config65_tpose_out_perm[2] = {0, 1};
unsigned config65_tpose_out_perm_strides[2] = {64, 1};

const unsigned* const config65_tpose_out::from_shape = config65_tpose_out_from_shape;
const unsigned* const config65_tpose_out::to_shape = config65_tpose_out_to_shape;
const unsigned* const config65_tpose_out::perm = config65_tpose_out_perm;
const unsigned* const config65_tpose_out::perm_strides = config65_tpose_out_perm_strides;


struct config65_dense : nnet::dense_config {
    static const unsigned n_in = 32;
    static const unsigned n_out = 64;
    static const unsigned reuse_factor = 1;
    static const unsigned strategy = nnet::latency;
    static const unsigned n_zeros = 0;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in * n_out, reuse_factor) - n_zeros / reuse_factor;
    typedef bit_block_1_ffn_fc1_accum_t accum_t;
    typedef bit_block_1_ffn_fc1_bias_t bias_t;
    typedef bit_block_1_ffn_fc1_weight_t weight_t;
    template<class data_T, class res_T, class CONFIG_T>
    using kernel = nnet::DenseLatency<data_T, res_T, CONFIG_T>;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};



struct config65 {
    typedef config65_tpose_inp tpose_inp_conf;
    typedef config65_tpose_out tpose_out_conf;

    typedef bit_block_1_ffn_fc1_accum_t accum_t;
    typedef bit_block_1_ffn_fc1_bias_t bias_t;

    typedef config65_dense dense_conf;

    // Layer Sizes
    static const unsigned n_free_data = 8;
    static const unsigned n_free_kernel = 64;
    static const unsigned n_contract = 32;
    static const unsigned n_inplace = 1;

    // Resource reuse info
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned strategy = nnet::latency;
    static const unsigned reuse_factor = 1;
    static const unsigned parallelization_factor = 8; // Only useful when n_inplace > 1
};

// bit_block_1_ffn_fc1_affine
struct config67 : nnet::batchnorm_config {
    static const unsigned n_in = 8*64;
    static const unsigned n_filt = 64;
    static const unsigned n_scale_bias = (n_filt == -1) ? n_in : n_filt;
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned reuse_factor = 1;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in, reuse_factor);
    static const bool store_weights_in_bram = false;
    typedef bit_block_1_ffn_fc1_affine_bias_t bias_t;
    typedef bit_block_1_ffn_fc1_affine_scale_t scale_t;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};

// bit_block_1_ffn_act
struct relu_config68 : nnet::activ_config {
    static const unsigned n_in = 512;
    static const unsigned table_size = 1048576;
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned reuse_factor = 1;
    typedef bit_block_1_ffn_act_table_t table_t;
};

// bit_block_1_ffn_fc2
struct config70_tpose_inp {
    static const unsigned dims = 2;
    static const unsigned N = 512;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config70_tpose_inp_from_shape[2] = {8, 64};
unsigned config70_tpose_inp_to_shape[2] = {8, 64};
unsigned config70_tpose_inp_perm[2] = {0, 1};
unsigned config70_tpose_inp_perm_strides[2] = {64, 1};

const unsigned* const config70_tpose_inp::from_shape = config70_tpose_inp_from_shape;
const unsigned* const config70_tpose_inp::to_shape = config70_tpose_inp_to_shape;
const unsigned* const config70_tpose_inp::perm = config70_tpose_inp_perm;
const unsigned* const config70_tpose_inp::perm_strides = config70_tpose_inp_perm_strides;


struct config70_tpose_out {
    static const unsigned dims = 2;
    static const unsigned N = 256;
    static const unsigned* const from_shape;
    static const unsigned* const to_shape;
    static const unsigned* const perm;
    static const unsigned* const perm_strides;
};

unsigned config70_tpose_out_from_shape[2] = {8, 32};
unsigned config70_tpose_out_to_shape[2] = {8, 32};
unsigned config70_tpose_out_perm[2] = {0, 1};
unsigned config70_tpose_out_perm_strides[2] = {32, 1};

const unsigned* const config70_tpose_out::from_shape = config70_tpose_out_from_shape;
const unsigned* const config70_tpose_out::to_shape = config70_tpose_out_to_shape;
const unsigned* const config70_tpose_out::perm = config70_tpose_out_perm;
const unsigned* const config70_tpose_out::perm_strides = config70_tpose_out_perm_strides;


struct config70_dense : nnet::dense_config {
    static const unsigned n_in = 64;
    static const unsigned n_out = 32;
    static const unsigned reuse_factor = 1;
    static const unsigned strategy = nnet::latency;
    static const unsigned n_zeros = 0;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in * n_out, reuse_factor) - n_zeros / reuse_factor;
    typedef bit_block_1_ffn_fc2_accum_t accum_t;
    typedef bit_block_1_ffn_fc2_bias_t bias_t;
    typedef bit_block_1_ffn_fc2_weight_t weight_t;
    template<class data_T, class res_T, class CONFIG_T>
    using kernel = nnet::DenseLatency<data_T, res_T, CONFIG_T>;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};



struct config70 {
    typedef config70_tpose_inp tpose_inp_conf;
    typedef config70_tpose_out tpose_out_conf;

    typedef bit_block_1_ffn_fc2_accum_t accum_t;
    typedef bit_block_1_ffn_fc2_bias_t bias_t;

    typedef config70_dense dense_conf;

    // Layer Sizes
    static const unsigned n_free_data = 8;
    static const unsigned n_free_kernel = 32;
    static const unsigned n_contract = 64;
    static const unsigned n_inplace = 1;

    // Resource reuse info
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned strategy = nnet::latency;
    static const unsigned reuse_factor = 1;
    static const unsigned parallelization_factor = 8; // Only useful when n_inplace > 1
};

// bit_block_1_ffn_fc2_affine
struct config72 : nnet::batchnorm_config {
    static const unsigned n_in = 8*32;
    static const unsigned n_filt = 32;
    static const unsigned n_scale_bias = (n_filt == -1) ? n_in : n_filt;
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned reuse_factor = 1;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in, reuse_factor);
    static const bool store_weights_in_bram = false;
    typedef bit_block_1_ffn_fc2_affine_bias_t bias_t;
    typedef bit_block_1_ffn_fc2_affine_scale_t scale_t;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};

// bit_block_1_add_ffn
struct config73 : nnet::merge_config {
    static const unsigned n_elem = 8*32;
    static const unsigned n_elem1 = 8*32;
    static const unsigned n_elem2 = 8*32;
    static const unsigned reuse_factor = 1;
};

// gap
struct config74 : nnet::pooling1d_config {
    static const unsigned n_in = 8;
    static const unsigned n_filt = 32;
    static const nnet::Pool_Op pool_op = nnet::Average;
    static const unsigned reuse_factor = 1;
    typedef gap_accum_t accum_t;
};

// head_fc1
struct config76 : nnet::dense_config {
    static const unsigned n_in = 32;
    static const unsigned n_out = 32;
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned strategy = nnet::latency;
    static const unsigned reuse_factor = 1;
    static const unsigned n_zeros = 0;
    static const unsigned n_nonzeros = 1024;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in * n_out, reuse_factor) - n_zeros / reuse_factor;
    static const bool store_weights_in_bram = false;
    typedef head_fc1_accum_t accum_t;
    typedef head_fc1_bias_t bias_t;
    typedef head_fc1_weight_t weight_t;
    typedef layer76_index index_t;
    template<class data_T, class res_T, class CONFIG_T>
    using kernel = nnet::DenseLatency<data_T, res_T, CONFIG_T>;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};

// head_fc1_affine
struct config78 : nnet::batchnorm_config {
    static const unsigned n_in = 32;
    static const unsigned n_filt = 32;
    static const unsigned n_scale_bias = (n_filt == -1) ? n_in : n_filt;
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned reuse_factor = 1;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in, reuse_factor);
    static const bool store_weights_in_bram = false;
    typedef head_fc1_affine_bias_t bias_t;
    typedef head_fc1_affine_scale_t scale_t;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};

// head_act
struct relu_config79 : nnet::activ_config {
    static const unsigned n_in = 32;
    static const unsigned table_size = 2097152;
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned reuse_factor = 1;
    typedef head_act_table_t table_t;
};

// head_fc2
struct config81 : nnet::dense_config {
    static const unsigned n_in = 32;
    static const unsigned n_out = 5;
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned strategy = nnet::latency;
    static const unsigned reuse_factor = 1;
    static const unsigned n_zeros = 0;
    static const unsigned n_nonzeros = 160;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in * n_out, reuse_factor) - n_zeros / reuse_factor;
    static const bool store_weights_in_bram = false;
    typedef head_fc2_accum_t accum_t;
    typedef head_fc2_bias_t bias_t;
    typedef head_fc2_weight_t weight_t;
    typedef layer81_index index_t;
    template<class data_T, class res_T, class CONFIG_T>
    using kernel = nnet::DenseLatency<data_T, res_T, CONFIG_T>;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};

// head_fc2_affine
struct config83 : nnet::batchnorm_config {
    static const unsigned n_in = 5;
    static const unsigned n_filt = 5;
    static const unsigned n_scale_bias = (n_filt == -1) ? n_in : n_filt;
    static const unsigned io_type = nnet::io_parallel;
    static const unsigned reuse_factor = 1;
    static const unsigned multiplier_limit = DIV_ROUNDUP(n_in, reuse_factor);
    static const bool store_weights_in_bram = false;
    typedef head_fc2_affine_bias_t bias_t;
    typedef head_fc2_affine_scale_t scale_t;
    template<class x_T, class y_T>
    using product = nnet::product::mult<x_T, y_T>;
};



#endif
