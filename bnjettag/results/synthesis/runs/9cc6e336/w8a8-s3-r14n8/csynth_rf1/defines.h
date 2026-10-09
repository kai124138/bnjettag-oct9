#ifndef DEFINES_H_
#define DEFINES_H_

#include "ap_fixed.h"
#include "ap_int.h"
#include "nnet_utils/nnet_types.h"
#include <array>
#include <cstddef>
#include <cstdio>
#include <tuple>
#include <tuple>


// hls-fpga-machine-learning insert numbers

// hls-fpga-machine-learning insert layer-precision
typedef ap_fixed<8,4,AP_RND_CONV,AP_SAT,0> input_1_t;
typedef ap_fixed<35,5> input_proj_accum_t;
typedef ap_fixed<35,5> input_proj_t;
typedef ap_fixed<6,1> input_proj_weight_t;
typedef ap_fixed<31,1> input_proj_bias_t;
typedef ap_fixed<8,3> bit_block_0_attn_Wq_iq_t;
typedef ap_fixed<16,6> bit_block_0_attn_Wq_accum_t;
typedef ap_fixed<8,4,AP_RND_CONV,AP_SAT,0> bit_block_0_attn_Wq_t;
typedef ap_fixed<24,12> model_default_t;
typedef ap_fixed<8,3> bit_block_0_attn_Wk_iq_t;
typedef ap_fixed<16,6> bit_block_0_attn_Wk_accum_t;
typedef ap_fixed<8,3,AP_RND_CONV,AP_SAT,0> bit_block_0_attn_Wk_t;
typedef ap_fixed<19,10> bit_block_0_attn_scores_accum_t;
typedef ap_fixed<19,10> bit_block_0_attn_scores_t;
typedef ap_ufixed<12,1,AP_RND_CONV,AP_SAT,0> bit_block_0_attn_softmax_exp_table_t;
typedef ap_ufixed<12,1,AP_RND_CONV,AP_SAT,0> bit_block_0_attn_softmax_inv_table_t;
typedef ap_ufixed<12,4,AP_RND_CONV,AP_SAT,0> bit_block_0_attn_softmax_inv_inp_t;
typedef ap_fixed<10,7,AP_RND_CONV,AP_SAT,0> bit_block_0_attn_softmax_inp_norm_t;
typedef ap_ufixed<24,7> bit_block_0_attn_softmax_accum_t;
typedef ap_ufixed<10,1,AP_RND_CONV,AP_SAT,0> bit_block_0_attn_softmax_t;
typedef ap_fixed<18,8> bit_block_0_attn_softmax_table_t;
typedef ap_fixed<8,3> bit_block_0_attn_Wv_iq_t;
typedef ap_fixed<16,6> bit_block_0_attn_Wv_accum_t;
typedef ap_fixed<8,5,AP_RND_CONV,AP_SAT,0> bit_block_0_attn_Wv_t;
typedef ap_fixed<21,9> bit_block_0_attn_ctx_accum_t;
typedef ap_fixed<8,4,AP_RND_CONV,AP_SAT,0> bit_block_0_attn_ctx_t;
typedef ap_fixed<39,7> bit_block_0_attn_Wo_accum_t;
typedef ap_fixed<39,7> bit_block_0_attn_Wo_t;
typedef ap_fixed<40,8> bit_block_0_add_attn_t;
typedef ap_fixed<8,4> bit_block_0_ffn_fc1_iq_t;
typedef ap_fixed<39,7> bit_block_0_ffn_fc1_accum_t;
typedef ap_fixed<39,7> bit_block_0_ffn_fc1_t;
typedef ap_fixed<6,1> bit_block_0_ffn_fc1_weight_t;
typedef ap_fixed<30,-2> bit_block_0_ffn_fc1_bias_t;
typedef ap_ufixed<7,2,AP_RND_CONV,AP_SAT,0> bit_block_0_ffn_act_t;
typedef ap_ufixed<2,32> bit_block_0_ffn_act_param_t;
typedef ap_fixed<18,8> bit_block_0_ffn_act_table_t;
typedef ap_fixed<38,6> bit_block_0_ffn_fc2_accum_t;
typedef ap_fixed<38,6> bit_block_0_ffn_fc2_t;
typedef ap_fixed<6,1> bit_block_0_ffn_fc2_weight_t;
typedef ap_fixed<30,-2> bit_block_0_ffn_fc2_bias_t;
typedef ap_fixed<41,9> bit_block_0_add_ffn_t;
typedef ap_fixed<8,4> bit_block_1_attn_Wq_iq_t;
typedef ap_fixed<16,7> bit_block_1_attn_Wq_accum_t;
typedef ap_fixed<8,4,AP_RND_CONV,AP_SAT,0> bit_block_1_attn_Wq_t;
typedef ap_fixed<8,4> bit_block_1_attn_Wk_iq_t;
typedef ap_fixed<16,7> bit_block_1_attn_Wk_accum_t;
typedef ap_fixed<8,4,AP_RND_CONV,AP_SAT,0> bit_block_1_attn_Wk_t;
typedef ap_fixed<19,11> bit_block_1_attn_scores_accum_t;
typedef ap_fixed<19,11> bit_block_1_attn_scores_t;
typedef ap_ufixed<12,1,AP_RND_CONV,AP_SAT,0> bit_block_1_attn_softmax_exp_table_t;
typedef ap_ufixed<12,1,AP_RND_CONV,AP_SAT,0> bit_block_1_attn_softmax_inv_table_t;
typedef ap_ufixed<12,4,AP_RND_CONV,AP_SAT,0> bit_block_1_attn_softmax_inv_inp_t;
typedef ap_fixed<10,7,AP_RND_CONV,AP_SAT,0> bit_block_1_attn_softmax_inp_norm_t;
typedef ap_ufixed<24,7> bit_block_1_attn_softmax_accum_t;
typedef ap_ufixed<10,1,AP_RND_CONV,AP_SAT,0> bit_block_1_attn_softmax_t;
typedef ap_fixed<18,8> bit_block_1_attn_softmax_table_t;
typedef ap_fixed<8,4> bit_block_1_attn_Wv_iq_t;
typedef ap_fixed<16,7> bit_block_1_attn_Wv_accum_t;
typedef ap_fixed<8,6,AP_RND_CONV,AP_SAT,0> bit_block_1_attn_Wv_t;
typedef ap_fixed<21,10> bit_block_1_attn_ctx_accum_t;
typedef ap_fixed<8,4,AP_RND_CONV,AP_SAT,0> bit_block_1_attn_ctx_t;
typedef ap_fixed<39,7> bit_block_1_attn_Wo_accum_t;
typedef ap_fixed<39,7> bit_block_1_attn_Wo_t;
typedef ap_fixed<42,10> bit_block_1_add_attn_t;
typedef ap_fixed<8,5> bit_block_1_ffn_fc1_iq_t;
typedef ap_fixed<40,8> bit_block_1_ffn_fc1_accum_t;
typedef ap_fixed<40,8> bit_block_1_ffn_fc1_t;
typedef ap_fixed<6,1> bit_block_1_ffn_fc1_weight_t;
typedef ap_fixed<30,-2> bit_block_1_ffn_fc1_bias_t;
typedef ap_ufixed<7,3,AP_RND_CONV,AP_SAT,0> bit_block_1_ffn_act_t;
typedef ap_ufixed<2,32> bit_block_1_ffn_act_param_t;
typedef ap_fixed<18,8> bit_block_1_ffn_act_table_t;
typedef ap_fixed<39,7> bit_block_1_ffn_fc2_accum_t;
typedef ap_fixed<39,7> bit_block_1_ffn_fc2_t;
typedef ap_fixed<6,1> bit_block_1_ffn_fc2_weight_t;
typedef ap_fixed<30,-2> bit_block_1_ffn_fc2_bias_t;
typedef ap_fixed<43,11> bit_block_1_add_ffn_t;
typedef ap_fixed<49,14> gap_accum_t;
typedef ap_fixed<8,4,AP_RND_CONV,AP_SAT,0> gap_t;
typedef ap_fixed<39,7> head_fc1_accum_t;
typedef ap_fixed<39,7> head_fc1_t;
typedef ap_fixed<6,1> head_fc1_weight_t;
typedef ap_fixed<30,-2> head_fc1_bias_t;
typedef ap_uint<1> layer50_index;
typedef ap_ufixed<7,3,AP_RND_CONV,AP_SAT,0> head_act_t;
typedef ap_ufixed<2,32> head_act_param_t;
typedef ap_fixed<18,8> head_act_table_t;
typedef ap_fixed<36,7> head_fc2_accum_t;
typedef ap_fixed<36,7> result_t;
typedef ap_fixed<6,1> head_fc2_weight_t;
typedef ap_fixed<25,-4> head_fc2_bias_t;
typedef ap_uint<1> layer53_index;

// hls-fpga-machine-learning insert emulator-defines


#endif
