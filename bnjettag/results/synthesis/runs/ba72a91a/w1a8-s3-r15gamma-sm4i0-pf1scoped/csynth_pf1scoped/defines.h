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
typedef ap_fixed<22,6> input_proj_accum_t;
typedef ap_fixed<14,7,AP_RND_CONV,AP_SAT,0> input_proj_t;
typedef ap_fixed<2,2> input_proj_weight_t;
typedef ap_fixed<19,3> input_proj_bias_t;
typedef ap_fixed<19,6> input_proj_affine_t;
typedef ap_ufixed<5,-1> input_proj_affine_scale_t;
typedef ap_ufixed<2,32> input_proj_affine_bias_t;
typedef ap_fixed<8,2> bit_block_0_attn_Wq_iq_t;
typedef ap_fixed<13,7> bit_block_0_attn_Wq_accum_t;
typedef ap_fixed<13,7,AP_RND_CONV,AP_SAT,0> bit_block_0_attn_Wq_t;
typedef ap_fixed<24,12> model_default_t;
typedef ap_fixed<8,2> bit_block_0_attn_Wk_iq_t;
typedef ap_fixed<13,7> bit_block_0_attn_Wk_accum_t;
typedef ap_fixed<13,7,AP_RND_CONV,AP_SAT,0> bit_block_0_attn_Wk_t;
typedef ap_fixed<8,3,AP_RND_CONV,AP_SAT,0> bit_block_0_attn_Wq_affine_t;
typedef ap_ufixed<6,-2> bit_block_0_attn_Wq_affine_scale_t;
typedef ap_ufixed<2,32> bit_block_0_attn_Wq_affine_bias_t;
typedef ap_fixed<8,3,AP_RND_CONV,AP_SAT,0> bit_block_0_attn_Wk_affine_t;
typedef ap_ufixed<6,-2> bit_block_0_attn_Wk_affine_scale_t;
typedef ap_ufixed<2,32> bit_block_0_attn_Wk_affine_bias_t;
typedef ap_fixed<19,9> bit_block_0_attn_scores_accum_t;
typedef ap_fixed<19,9> bit_block_0_attn_scores_t;
typedef ap_fixed<8,2> bit_block_0_attn_Wv_iq_t;
typedef ap_fixed<13,7> bit_block_0_attn_Wv_accum_t;
typedef ap_fixed<13,7,AP_RND_CONV,AP_SAT,0> bit_block_0_attn_Wv_t;
typedef ap_ufixed<12,1,AP_RND_CONV,AP_SAT,0> bit_block_0_attn_softmax_exp_table_t;
typedef ap_ufixed<12,1,AP_RND_CONV,AP_SAT,0> bit_block_0_attn_softmax_inv_table_t;
typedef ap_ufixed<12,4,AP_RND_CONV,AP_SAT,0> bit_block_0_attn_softmax_inv_inp_t;
typedef ap_fixed<10,7,AP_RND_CONV,AP_SAT,0> bit_block_0_attn_softmax_inp_norm_t;
typedef ap_ufixed<24,7> bit_block_0_attn_softmax_accum_t;
typedef ap_ufixed<4,0,AP_RND_CONV,AP_SAT,0> bit_block_0_attn_softmax_t;
typedef ap_fixed<18,8> bit_block_0_attn_softmax_table_t;
typedef ap_fixed<8,6,AP_RND_CONV,AP_SAT,0> bit_block_0_attn_Wv_affine_t;
typedef ap_ufixed<6,-2> bit_block_0_attn_Wv_affine_scale_t;
typedef ap_ufixed<2,32> bit_block_0_attn_Wv_affine_bias_t;
typedef ap_fixed<15,9> bit_block_0_attn_ctx_accum_t;
typedef ap_fixed<8,3,AP_RND_CONV,AP_SAT,0> bit_block_0_attn_ctx_t;
typedef ap_fixed<13,8> bit_block_0_attn_Wo_accum_t;
typedef ap_fixed<13,8,AP_RND_CONV,AP_SAT,0> bit_block_0_attn_Wo_t;
typedef ap_fixed<22,6> bit_block_0_attn_Wo_affine_t;
typedef ap_ufixed<5,-2> bit_block_0_attn_Wo_affine_scale_t;
typedef ap_fixed<14,-2> bit_block_0_attn_Wo_affine_bias_t;
typedef ap_fixed<23,7> bit_block_0_add_attn_t;
typedef ap_fixed<8,3> bit_block_0_ffn_fc1_iq_t;
typedef ap_fixed<13,8> bit_block_0_ffn_fc1_accum_t;
typedef ap_fixed<13,8,AP_RND_CONV,AP_SAT,0> bit_block_0_ffn_fc1_t;
typedef ap_fixed<2,2> bit_block_0_ffn_fc1_weight_t;
typedef ap_ufixed<2,32> bit_block_0_ffn_fc1_bias_t;
typedef ap_fixed<22,6> bit_block_0_ffn_fc1_affine_t;
typedef ap_ufixed<6,-2> bit_block_0_ffn_fc1_affine_scale_t;
typedef ap_fixed<15,-1> bit_block_0_ffn_fc1_affine_bias_t;
typedef ap_ufixed<7,2,AP_RND_CONV,AP_SAT,0> bit_block_0_ffn_act_t;
typedef ap_ufixed<2,32> bit_block_0_ffn_act_param_t;
typedef ap_fixed<18,8> bit_block_0_ffn_act_table_t;
typedef ap_fixed<14,9> bit_block_0_ffn_fc2_accum_t;
typedef ap_fixed<14,9,AP_RND_CONV,AP_SAT,0> bit_block_0_ffn_fc2_t;
typedef ap_fixed<2,2> bit_block_0_ffn_fc2_weight_t;
typedef ap_ufixed<2,32> bit_block_0_ffn_fc2_bias_t;
typedef ap_fixed<23,7> bit_block_0_ffn_fc2_affine_t;
typedef ap_ufixed<4,-2> bit_block_0_ffn_fc2_affine_scale_t;
typedef ap_fixed<14,-2> bit_block_0_ffn_fc2_affine_bias_t;
typedef ap_fixed<24,8> bit_block_0_add_ffn_t;
typedef ap_fixed<8,3> bit_block_1_attn_Wq_iq_t;
typedef ap_fixed<13,8> bit_block_1_attn_Wq_accum_t;
typedef ap_fixed<13,8,AP_RND_CONV,AP_SAT,0> bit_block_1_attn_Wq_t;
typedef ap_fixed<8,3> bit_block_1_attn_Wk_iq_t;
typedef ap_fixed<13,8> bit_block_1_attn_Wk_accum_t;
typedef ap_fixed<13,8,AP_RND_CONV,AP_SAT,0> bit_block_1_attn_Wk_t;
typedef ap_fixed<8,3,AP_RND_CONV,AP_SAT,0> bit_block_1_attn_Wq_affine_t;
typedef ap_ufixed<5,-2> bit_block_1_attn_Wq_affine_scale_t;
typedef ap_ufixed<2,32> bit_block_1_attn_Wq_affine_bias_t;
typedef ap_fixed<8,3,AP_RND_CONV,AP_SAT,0> bit_block_1_attn_Wk_affine_t;
typedef ap_ufixed<6,-2> bit_block_1_attn_Wk_affine_scale_t;
typedef ap_ufixed<2,32> bit_block_1_attn_Wk_affine_bias_t;
typedef ap_fixed<19,9> bit_block_1_attn_scores_accum_t;
typedef ap_fixed<19,9> bit_block_1_attn_scores_t;
typedef ap_fixed<8,3> bit_block_1_attn_Wv_iq_t;
typedef ap_fixed<13,8> bit_block_1_attn_Wv_accum_t;
typedef ap_fixed<13,8,AP_RND_CONV,AP_SAT,0> bit_block_1_attn_Wv_t;
typedef ap_ufixed<12,1,AP_RND_CONV,AP_SAT,0> bit_block_1_attn_softmax_exp_table_t;
typedef ap_ufixed<12,1,AP_RND_CONV,AP_SAT,0> bit_block_1_attn_softmax_inv_table_t;
typedef ap_ufixed<12,4,AP_RND_CONV,AP_SAT,0> bit_block_1_attn_softmax_inv_inp_t;
typedef ap_fixed<10,7,AP_RND_CONV,AP_SAT,0> bit_block_1_attn_softmax_inp_norm_t;
typedef ap_ufixed<24,7> bit_block_1_attn_softmax_accum_t;
typedef ap_ufixed<4,0,AP_RND_CONV,AP_SAT,0> bit_block_1_attn_softmax_t;
typedef ap_fixed<18,8> bit_block_1_attn_softmax_table_t;
typedef ap_fixed<8,6,AP_RND_CONV,AP_SAT,0> bit_block_1_attn_Wv_affine_t;
typedef ap_ufixed<6,-2> bit_block_1_attn_Wv_affine_scale_t;
typedef ap_ufixed<2,32> bit_block_1_attn_Wv_affine_bias_t;
typedef ap_fixed<15,9> bit_block_1_attn_ctx_accum_t;
typedef ap_fixed<8,3,AP_RND_CONV,AP_SAT,0> bit_block_1_attn_ctx_t;
typedef ap_fixed<13,8> bit_block_1_attn_Wo_accum_t;
typedef ap_fixed<13,8,AP_RND_CONV,AP_SAT,0> bit_block_1_attn_Wo_t;
typedef ap_fixed<22,6> bit_block_1_attn_Wo_affine_t;
typedef ap_ufixed<5,-2> bit_block_1_attn_Wo_affine_scale_t;
typedef ap_fixed<14,-2> bit_block_1_attn_Wo_affine_bias_t;
typedef ap_fixed<25,9> bit_block_1_add_attn_t;
typedef ap_fixed<8,3> bit_block_1_ffn_fc1_iq_t;
typedef ap_fixed<13,8> bit_block_1_ffn_fc1_accum_t;
typedef ap_fixed<13,8,AP_RND_CONV,AP_SAT,0> bit_block_1_ffn_fc1_t;
typedef ap_fixed<2,2> bit_block_1_ffn_fc1_weight_t;
typedef ap_ufixed<2,32> bit_block_1_ffn_fc1_bias_t;
typedef ap_fixed<22,6> bit_block_1_ffn_fc1_affine_t;
typedef ap_ufixed<5,-2> bit_block_1_ffn_fc1_affine_scale_t;
typedef ap_fixed<15,-1> bit_block_1_ffn_fc1_affine_bias_t;
typedef ap_ufixed<7,1,AP_RND_CONV,AP_SAT,0> bit_block_1_ffn_act_t;
typedef ap_ufixed<2,32> bit_block_1_ffn_act_param_t;
typedef ap_fixed<18,8> bit_block_1_ffn_act_table_t;
typedef ap_fixed<14,8> bit_block_1_ffn_fc2_accum_t;
typedef ap_fixed<14,8,AP_RND_CONV,AP_SAT,0> bit_block_1_ffn_fc2_t;
typedef ap_fixed<2,2> bit_block_1_ffn_fc2_weight_t;
typedef ap_ufixed<2,32> bit_block_1_ffn_fc2_bias_t;
typedef ap_fixed<22,6> bit_block_1_ffn_fc2_affine_t;
typedef ap_ufixed<6,-2> bit_block_1_ffn_fc2_affine_scale_t;
typedef ap_fixed<15,-1> bit_block_1_ffn_fc2_affine_bias_t;
typedef ap_fixed<26,10> bit_block_1_add_ffn_t;
typedef ap_fixed<32,13> gap_accum_t;
typedef ap_fixed<8,2,AP_RND_CONV,AP_SAT,0> gap_t;
typedef ap_fixed<13,7> head_fc1_accum_t;
typedef ap_fixed<13,7,AP_RND_CONV,AP_SAT,0> head_fc1_t;
typedef ap_fixed<2,2> head_fc1_weight_t;
typedef ap_ufixed<2,32> head_fc1_bias_t;
typedef ap_uint<1> layer76_index;
typedef ap_fixed<21,5> head_fc1_affine_t;
typedef ap_ufixed<2,-2> head_fc1_affine_scale_t;
typedef ap_fixed<15,-1> head_fc1_affine_bias_t;
typedef ap_ufixed<7,1,AP_RND_CONV,AP_SAT,0> head_act_t;
typedef ap_ufixed<2,32> head_act_param_t;
typedef ap_fixed<18,8> head_act_table_t;
typedef ap_fixed<13,7> head_fc2_accum_t;
typedef ap_fixed<13,7,AP_RND_CONV,AP_SAT,0> head_fc2_t;
typedef ap_fixed<2,2> head_fc2_weight_t;
typedef ap_ufixed<2,32> head_fc2_bias_t;
typedef ap_uint<1> layer81_index;
typedef ap_fixed<22,6> result_t;
typedef ap_ufixed<7,-1> head_fc2_affine_scale_t;
typedef ap_fixed<15,-1> head_fc2_affine_bias_t;

// hls-fpga-machine-learning insert emulator-defines


#endif
