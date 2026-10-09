#include <iostream>

#include "myproject.h"
#include "parameters.h"


extern "C" void myproject(
    input_1_t input_1[8*3],
    result_t layer83_out[5]
) {

    // hls-fpga-machine-learning insert IO
    #pragma HLS ARRAY_RESHAPE variable=input_1 complete dim=0
    #pragma HLS ARRAY_PARTITION variable=layer83_out complete dim=0
    #pragma HLS INTERFACE ap_vld port=input_1
    #pragma HLS INTERFACE ap_vld port=layer83_out 
    #pragma HLS PIPELINE

    // hls-fpga-machine-learning insert load weights
#ifndef __SYNTHESIS__
    static bool loaded_weights = false;
    if (!loaded_weights) {
        nnet::load_weights_from_txt<input_proj_weight_t, 96>(w3, "w3.txt");
        nnet::load_weights_from_txt<input_proj_bias_t, 256>(b3, "b3.txt");
        nnet::load_weights_from_txt<input_proj_affine_scale_t, 32>(s5, "s5.txt");
        nnet::load_weights_from_txt<input_proj_affine_bias_t, 32>(b5, "b5.txt");
        nnet::load_weights_from_txt<model_default_t, 1024>(w7, "w7.txt");
        nnet::load_weights_from_txt<model_default_t, 256>(b7, "b7.txt");
        nnet::load_weights_from_txt<model_default_t, 1024>(w9, "w9.txt");
        nnet::load_weights_from_txt<model_default_t, 256>(b9, "b9.txt");
        nnet::load_weights_from_txt<bit_block_0_attn_Wq_affine_scale_t, 8>(s11, "s11.txt");
        nnet::load_weights_from_txt<bit_block_0_attn_Wq_affine_bias_t, 8>(b11, "b11.txt");
        nnet::load_weights_from_txt<bit_block_0_attn_Wk_affine_scale_t, 8>(s13, "s13.txt");
        nnet::load_weights_from_txt<bit_block_0_attn_Wk_affine_bias_t, 8>(b13, "b13.txt");
        nnet::load_weights_from_txt<model_default_t, 1024>(w18, "w18.txt");
        nnet::load_weights_from_txt<model_default_t, 256>(b18, "b18.txt");
        nnet::load_weights_from_txt<bit_block_0_attn_Wv_affine_scale_t, 8>(s21, "s21.txt");
        nnet::load_weights_from_txt<bit_block_0_attn_Wv_affine_bias_t, 8>(b21, "b21.txt");
        nnet::load_weights_from_txt<model_default_t, 1024>(w26, "w26.txt");
        nnet::load_weights_from_txt<model_default_t, 256>(b26, "b26.txt");
        nnet::load_weights_from_txt<bit_block_0_attn_Wo_affine_scale_t, 32>(s28, "s28.txt");
        nnet::load_weights_from_txt<bit_block_0_attn_Wo_affine_bias_t, 32>(b28, "b28.txt");
        nnet::load_weights_from_txt<bit_block_0_ffn_fc1_weight_t, 2048>(w31, "w31.txt");
        nnet::load_weights_from_txt<bit_block_0_ffn_fc1_bias_t, 512>(b31, "b31.txt");
        nnet::load_weights_from_txt<bit_block_0_ffn_fc1_affine_scale_t, 64>(s33, "s33.txt");
        nnet::load_weights_from_txt<bit_block_0_ffn_fc1_affine_bias_t, 64>(b33, "b33.txt");
        nnet::load_weights_from_txt<bit_block_0_ffn_fc2_weight_t, 2048>(w36, "w36.txt");
        nnet::load_weights_from_txt<bit_block_0_ffn_fc2_bias_t, 256>(b36, "b36.txt");
        nnet::load_weights_from_txt<bit_block_0_ffn_fc2_affine_scale_t, 32>(s38, "s38.txt");
        nnet::load_weights_from_txt<bit_block_0_ffn_fc2_affine_bias_t, 32>(b38, "b38.txt");
        nnet::load_weights_from_txt<model_default_t, 1024>(w41, "w41.txt");
        nnet::load_weights_from_txt<model_default_t, 256>(b41, "b41.txt");
        nnet::load_weights_from_txt<model_default_t, 1024>(w43, "w43.txt");
        nnet::load_weights_from_txt<model_default_t, 256>(b43, "b43.txt");
        nnet::load_weights_from_txt<bit_block_1_attn_Wq_affine_scale_t, 8>(s45, "s45.txt");
        nnet::load_weights_from_txt<bit_block_1_attn_Wq_affine_bias_t, 8>(b45, "b45.txt");
        nnet::load_weights_from_txt<bit_block_1_attn_Wk_affine_scale_t, 8>(s47, "s47.txt");
        nnet::load_weights_from_txt<bit_block_1_attn_Wk_affine_bias_t, 8>(b47, "b47.txt");
        nnet::load_weights_from_txt<model_default_t, 1024>(w52, "w52.txt");
        nnet::load_weights_from_txt<model_default_t, 256>(b52, "b52.txt");
        nnet::load_weights_from_txt<bit_block_1_attn_Wv_affine_scale_t, 8>(s55, "s55.txt");
        nnet::load_weights_from_txt<bit_block_1_attn_Wv_affine_bias_t, 8>(b55, "b55.txt");
        nnet::load_weights_from_txt<model_default_t, 1024>(w60, "w60.txt");
        nnet::load_weights_from_txt<model_default_t, 256>(b60, "b60.txt");
        nnet::load_weights_from_txt<bit_block_1_attn_Wo_affine_scale_t, 32>(s62, "s62.txt");
        nnet::load_weights_from_txt<bit_block_1_attn_Wo_affine_bias_t, 32>(b62, "b62.txt");
        nnet::load_weights_from_txt<bit_block_1_ffn_fc1_weight_t, 2048>(w65, "w65.txt");
        nnet::load_weights_from_txt<bit_block_1_ffn_fc1_bias_t, 512>(b65, "b65.txt");
        nnet::load_weights_from_txt<bit_block_1_ffn_fc1_affine_scale_t, 64>(s67, "s67.txt");
        nnet::load_weights_from_txt<bit_block_1_ffn_fc1_affine_bias_t, 64>(b67, "b67.txt");
        nnet::load_weights_from_txt<bit_block_1_ffn_fc2_weight_t, 2048>(w70, "w70.txt");
        nnet::load_weights_from_txt<bit_block_1_ffn_fc2_bias_t, 256>(b70, "b70.txt");
        nnet::load_weights_from_txt<bit_block_1_ffn_fc2_affine_scale_t, 32>(s72, "s72.txt");
        nnet::load_weights_from_txt<bit_block_1_ffn_fc2_affine_bias_t, 32>(b72, "b72.txt");
        nnet::load_weights_from_txt<head_fc1_weight_t, 1024>(w76, "w76.txt");
        nnet::load_weights_from_txt<head_fc1_bias_t, 32>(b76, "b76.txt");
        nnet::load_weights_from_txt<head_fc1_affine_scale_t, 32>(s78, "s78.txt");
        nnet::load_weights_from_txt<head_fc1_affine_bias_t, 32>(b78, "b78.txt");
        nnet::load_weights_from_txt<head_fc2_weight_t, 160>(w81, "w81.txt");
        nnet::load_weights_from_txt<head_fc2_bias_t, 5>(b81, "b81.txt");
        nnet::load_weights_from_txt<head_fc2_affine_scale_t, 5>(s83, "s83.txt");
        nnet::load_weights_from_txt<head_fc2_affine_bias_t, 5>(b83, "b83.txt");
        loaded_weights = true;    }
#endif
    // ****************************************
    // NETWORK INSTANTIATION
    // ****************************************

    // hls-fpga-machine-learning insert layers

    input_proj_t layer3_out[8*32];
    #pragma HLS ARRAY_PARTITION variable=layer3_out complete dim=0

    input_proj_affine_t layer5_out[8*32];
    #pragma HLS ARRAY_PARTITION variable=layer5_out complete dim=0

    bit_block_0_attn_Wq_iq_t layer6_out[8*32];
    #pragma HLS ARRAY_PARTITION variable=layer6_out complete dim=0

    bit_block_0_attn_Wq_t layer7_out[8*4*8];
    #pragma HLS ARRAY_PARTITION variable=layer7_out complete dim=0

    bit_block_0_attn_Wk_iq_t layer8_out[8*32];
    #pragma HLS ARRAY_PARTITION variable=layer8_out complete dim=0

    bit_block_0_attn_Wk_t layer9_out[8*4*8];
    #pragma HLS ARRAY_PARTITION variable=layer9_out complete dim=0

    bit_block_0_attn_Wq_affine_t layer11_out[8*4*8];
    #pragma HLS ARRAY_PARTITION variable=layer11_out complete dim=0

    bit_block_0_attn_Wk_affine_t layer13_out[8*4*8];
    #pragma HLS ARRAY_PARTITION variable=layer13_out complete dim=0

    bit_block_0_attn_scores_t layer16_out[4*8*8];
    #pragma HLS ARRAY_PARTITION variable=layer16_out complete dim=0

    bit_block_0_attn_Wv_iq_t layer17_out[8*32];
    #pragma HLS ARRAY_PARTITION variable=layer17_out complete dim=0

    bit_block_0_attn_Wv_t layer18_out[8*4*8];
    #pragma HLS ARRAY_PARTITION variable=layer18_out complete dim=0

    bit_block_0_attn_softmax_t layer19_out[4*8*8];
    #pragma HLS ARRAY_PARTITION variable=layer19_out complete dim=0

    bit_block_0_attn_Wv_affine_t layer21_out[8*4*8];
    #pragma HLS ARRAY_PARTITION variable=layer21_out complete dim=0

    bit_block_0_attn_ctx_t layer24_out[8*4*8];
    #pragma HLS ARRAY_PARTITION variable=layer24_out complete dim=0

    bit_block_0_attn_Wo_t layer26_out[8*32];
    #pragma HLS ARRAY_PARTITION variable=layer26_out complete dim=0

    bit_block_0_attn_Wo_affine_t layer28_out[8*32];
    #pragma HLS ARRAY_PARTITION variable=layer28_out complete dim=0

    bit_block_0_add_attn_t layer29_out[8*32];
    #pragma HLS ARRAY_PARTITION variable=layer29_out complete dim=0

    bit_block_0_ffn_fc1_iq_t layer30_out[8*32];
    #pragma HLS ARRAY_PARTITION variable=layer30_out complete dim=0

    bit_block_0_ffn_fc1_t layer31_out[8*64];
    #pragma HLS ARRAY_PARTITION variable=layer31_out complete dim=0

    bit_block_0_ffn_fc1_affine_t layer33_out[8*64];
    #pragma HLS ARRAY_PARTITION variable=layer33_out complete dim=0

    bit_block_0_ffn_act_t layer34_out[8*64];
    #pragma HLS ARRAY_PARTITION variable=layer34_out complete dim=0

    bit_block_0_ffn_fc2_t layer36_out[8*32];
    #pragma HLS ARRAY_PARTITION variable=layer36_out complete dim=0

    bit_block_0_ffn_fc2_affine_t layer38_out[8*32];
    #pragma HLS ARRAY_PARTITION variable=layer38_out complete dim=0

    bit_block_0_add_ffn_t layer39_out[8*32];
    #pragma HLS ARRAY_PARTITION variable=layer39_out complete dim=0

    bit_block_1_attn_Wq_iq_t layer40_out[8*32];
    #pragma HLS ARRAY_PARTITION variable=layer40_out complete dim=0

    bit_block_1_attn_Wq_t layer41_out[8*4*8];
    #pragma HLS ARRAY_PARTITION variable=layer41_out complete dim=0

    bit_block_1_attn_Wk_iq_t layer42_out[8*32];
    #pragma HLS ARRAY_PARTITION variable=layer42_out complete dim=0

    bit_block_1_attn_Wk_t layer43_out[8*4*8];
    #pragma HLS ARRAY_PARTITION variable=layer43_out complete dim=0

    bit_block_1_attn_Wq_affine_t layer45_out[8*4*8];
    #pragma HLS ARRAY_PARTITION variable=layer45_out complete dim=0

    bit_block_1_attn_Wk_affine_t layer47_out[8*4*8];
    #pragma HLS ARRAY_PARTITION variable=layer47_out complete dim=0

    bit_block_1_attn_scores_t layer50_out[4*8*8];
    #pragma HLS ARRAY_PARTITION variable=layer50_out complete dim=0

    bit_block_1_attn_Wv_iq_t layer51_out[8*32];
    #pragma HLS ARRAY_PARTITION variable=layer51_out complete dim=0

    bit_block_1_attn_Wv_t layer52_out[8*4*8];
    #pragma HLS ARRAY_PARTITION variable=layer52_out complete dim=0

    bit_block_1_attn_softmax_t layer53_out[4*8*8];
    #pragma HLS ARRAY_PARTITION variable=layer53_out complete dim=0

    bit_block_1_attn_Wv_affine_t layer55_out[8*4*8];
    #pragma HLS ARRAY_PARTITION variable=layer55_out complete dim=0

    bit_block_1_attn_ctx_t layer58_out[8*4*8];
    #pragma HLS ARRAY_PARTITION variable=layer58_out complete dim=0

    bit_block_1_attn_Wo_t layer60_out[8*32];
    #pragma HLS ARRAY_PARTITION variable=layer60_out complete dim=0

    bit_block_1_attn_Wo_affine_t layer62_out[8*32];
    #pragma HLS ARRAY_PARTITION variable=layer62_out complete dim=0

    bit_block_1_add_attn_t layer63_out[8*32];
    #pragma HLS ARRAY_PARTITION variable=layer63_out complete dim=0

    bit_block_1_ffn_fc1_iq_t layer64_out[8*32];
    #pragma HLS ARRAY_PARTITION variable=layer64_out complete dim=0

    bit_block_1_ffn_fc1_t layer65_out[8*64];
    #pragma HLS ARRAY_PARTITION variable=layer65_out complete dim=0

    bit_block_1_ffn_fc1_affine_t layer67_out[8*64];
    #pragma HLS ARRAY_PARTITION variable=layer67_out complete dim=0

    bit_block_1_ffn_act_t layer68_out[8*64];
    #pragma HLS ARRAY_PARTITION variable=layer68_out complete dim=0

    bit_block_1_ffn_fc2_t layer70_out[8*32];
    #pragma HLS ARRAY_PARTITION variable=layer70_out complete dim=0

    bit_block_1_ffn_fc2_affine_t layer72_out[8*32];
    #pragma HLS ARRAY_PARTITION variable=layer72_out complete dim=0

    bit_block_1_add_ffn_t layer73_out[8*32];
    #pragma HLS ARRAY_PARTITION variable=layer73_out complete dim=0

    gap_t layer74_out[32];
    #pragma HLS ARRAY_PARTITION variable=layer74_out complete dim=0

    head_fc1_t layer76_out[32];
    #pragma HLS ARRAY_PARTITION variable=layer76_out complete dim=0

    head_fc1_affine_t layer78_out[32];
    #pragma HLS ARRAY_PARTITION variable=layer78_out complete dim=0

    head_act_t layer79_out[32];
    #pragma HLS ARRAY_PARTITION variable=layer79_out complete dim=0

    head_fc2_t layer81_out[5];
    #pragma HLS ARRAY_PARTITION variable=layer81_out complete dim=0

    nnet::einsum_dense<input_1_t, input_proj_t, config3>(input_1, layer3_out, w3, b3); // input_proj

    nnet::normalize<input_proj_t, input_proj_affine_t, config5>(layer3_out, layer5_out, s5, b5); // input_proj_affine

    nnet::bit_block_0_attn_Wq_iq<input_proj_affine_t, bit_block_0_attn_Wq_iq_t>(layer5_out, layer6_out); // bit_block_0_attn_Wq_iq

    nnet::einsum_dense<bit_block_0_attn_Wq_iq_t, bit_block_0_attn_Wq_t, config7>(layer6_out, layer7_out, w7, b7); // bit_block_0_attn_Wq

    nnet::bit_block_0_attn_Wk_iq<input_proj_affine_t, bit_block_0_attn_Wk_iq_t>(layer5_out, layer8_out); // bit_block_0_attn_Wk_iq

    nnet::einsum_dense<bit_block_0_attn_Wk_iq_t, bit_block_0_attn_Wk_t, config9>(layer8_out, layer9_out, w9, b9); // bit_block_0_attn_Wk

    nnet::normalize<bit_block_0_attn_Wq_t, bit_block_0_attn_Wq_affine_t, config11>(layer7_out, layer11_out, s11, b11); // bit_block_0_attn_Wq_affine

    nnet::normalize<bit_block_0_attn_Wk_t, bit_block_0_attn_Wk_affine_t, config13>(layer9_out, layer13_out, s13, b13); // bit_block_0_attn_Wk_affine

    nnet::einsum<bit_block_0_attn_Wq_affine_t, bit_block_0_attn_Wk_affine_t, bit_block_0_attn_scores_t, config16>(layer11_out, layer13_out, layer16_out); // bit_block_0_attn_scores

    nnet::bit_block_0_attn_Wv_iq<input_proj_affine_t, bit_block_0_attn_Wv_iq_t>(layer5_out, layer17_out); // bit_block_0_attn_Wv_iq

    nnet::einsum_dense<bit_block_0_attn_Wv_iq_t, bit_block_0_attn_Wv_t, config18>(layer17_out, layer18_out, w18, b18); // bit_block_0_attn_Wv

    nnet::softmax_multidim<bit_block_0_attn_scores_t, bit_block_0_attn_softmax_t, softmax_config19>(layer16_out, layer19_out); // bit_block_0_attn_softmax

    nnet::normalize<bit_block_0_attn_Wv_t, bit_block_0_attn_Wv_affine_t, config21>(layer18_out, layer21_out, s21, b21); // bit_block_0_attn_Wv_affine

    nnet::einsum<bit_block_0_attn_softmax_t, bit_block_0_attn_Wv_affine_t, bit_block_0_attn_ctx_t, config24>(layer19_out, layer21_out, layer24_out); // bit_block_0_attn_ctx

    nnet::einsum_dense<bit_block_0_attn_ctx_t, bit_block_0_attn_Wo_t, config26>(layer24_out, layer26_out, w26, b26); // bit_block_0_attn_Wo

    nnet::normalize<bit_block_0_attn_Wo_t, bit_block_0_attn_Wo_affine_t, config28>(layer26_out, layer28_out, s28, b28); // bit_block_0_attn_Wo_affine

    nnet::add<input_proj_affine_t, bit_block_0_attn_Wo_affine_t, bit_block_0_add_attn_t, config29>(layer5_out, layer28_out, layer29_out); // bit_block_0_add_attn

    nnet::bit_block_0_ffn_fc1_iq<bit_block_0_add_attn_t, bit_block_0_ffn_fc1_iq_t>(layer29_out, layer30_out); // bit_block_0_ffn_fc1_iq

    nnet::einsum_dense<bit_block_0_ffn_fc1_iq_t, bit_block_0_ffn_fc1_t, config31>(layer30_out, layer31_out, w31, b31); // bit_block_0_ffn_fc1

    nnet::normalize<bit_block_0_ffn_fc1_t, bit_block_0_ffn_fc1_affine_t, config33>(layer31_out, layer33_out, s33, b33); // bit_block_0_ffn_fc1_affine

    nnet::relu<bit_block_0_ffn_fc1_affine_t, bit_block_0_ffn_act_t, relu_config34>(layer33_out, layer34_out); // bit_block_0_ffn_act

    nnet::einsum_dense<bit_block_0_ffn_act_t, bit_block_0_ffn_fc2_t, config36>(layer34_out, layer36_out, w36, b36); // bit_block_0_ffn_fc2

    nnet::normalize<bit_block_0_ffn_fc2_t, bit_block_0_ffn_fc2_affine_t, config38>(layer36_out, layer38_out, s38, b38); // bit_block_0_ffn_fc2_affine

    nnet::add<bit_block_0_add_attn_t, bit_block_0_ffn_fc2_affine_t, bit_block_0_add_ffn_t, config39>(layer29_out, layer38_out, layer39_out); // bit_block_0_add_ffn

    nnet::bit_block_1_attn_Wq_iq<bit_block_0_add_ffn_t, bit_block_1_attn_Wq_iq_t>(layer39_out, layer40_out); // bit_block_1_attn_Wq_iq

    nnet::einsum_dense<bit_block_1_attn_Wq_iq_t, bit_block_1_attn_Wq_t, config41>(layer40_out, layer41_out, w41, b41); // bit_block_1_attn_Wq

    nnet::bit_block_1_attn_Wk_iq<bit_block_0_add_ffn_t, bit_block_1_attn_Wk_iq_t>(layer39_out, layer42_out); // bit_block_1_attn_Wk_iq

    nnet::einsum_dense<bit_block_1_attn_Wk_iq_t, bit_block_1_attn_Wk_t, config43>(layer42_out, layer43_out, w43, b43); // bit_block_1_attn_Wk

    nnet::normalize<bit_block_1_attn_Wq_t, bit_block_1_attn_Wq_affine_t, config45>(layer41_out, layer45_out, s45, b45); // bit_block_1_attn_Wq_affine

    nnet::normalize<bit_block_1_attn_Wk_t, bit_block_1_attn_Wk_affine_t, config47>(layer43_out, layer47_out, s47, b47); // bit_block_1_attn_Wk_affine

    nnet::einsum<bit_block_1_attn_Wq_affine_t, bit_block_1_attn_Wk_affine_t, bit_block_1_attn_scores_t, config50>(layer45_out, layer47_out, layer50_out); // bit_block_1_attn_scores

    nnet::bit_block_1_attn_Wv_iq<bit_block_0_add_ffn_t, bit_block_1_attn_Wv_iq_t>(layer39_out, layer51_out); // bit_block_1_attn_Wv_iq

    nnet::einsum_dense<bit_block_1_attn_Wv_iq_t, bit_block_1_attn_Wv_t, config52>(layer51_out, layer52_out, w52, b52); // bit_block_1_attn_Wv

    nnet::softmax_multidim<bit_block_1_attn_scores_t, bit_block_1_attn_softmax_t, softmax_config53>(layer50_out, layer53_out); // bit_block_1_attn_softmax

    nnet::normalize<bit_block_1_attn_Wv_t, bit_block_1_attn_Wv_affine_t, config55>(layer52_out, layer55_out, s55, b55); // bit_block_1_attn_Wv_affine

    nnet::einsum<bit_block_1_attn_softmax_t, bit_block_1_attn_Wv_affine_t, bit_block_1_attn_ctx_t, config58>(layer53_out, layer55_out, layer58_out); // bit_block_1_attn_ctx

    nnet::einsum_dense<bit_block_1_attn_ctx_t, bit_block_1_attn_Wo_t, config60>(layer58_out, layer60_out, w60, b60); // bit_block_1_attn_Wo

    nnet::normalize<bit_block_1_attn_Wo_t, bit_block_1_attn_Wo_affine_t, config62>(layer60_out, layer62_out, s62, b62); // bit_block_1_attn_Wo_affine

    nnet::add<bit_block_0_add_ffn_t, bit_block_1_attn_Wo_affine_t, bit_block_1_add_attn_t, config63>(layer39_out, layer62_out, layer63_out); // bit_block_1_add_attn

    nnet::bit_block_1_ffn_fc1_iq<bit_block_1_add_attn_t, bit_block_1_ffn_fc1_iq_t>(layer63_out, layer64_out); // bit_block_1_ffn_fc1_iq

    nnet::einsum_dense<bit_block_1_ffn_fc1_iq_t, bit_block_1_ffn_fc1_t, config65>(layer64_out, layer65_out, w65, b65); // bit_block_1_ffn_fc1

    nnet::normalize<bit_block_1_ffn_fc1_t, bit_block_1_ffn_fc1_affine_t, config67>(layer65_out, layer67_out, s67, b67); // bit_block_1_ffn_fc1_affine

    nnet::relu<bit_block_1_ffn_fc1_affine_t, bit_block_1_ffn_act_t, relu_config68>(layer67_out, layer68_out); // bit_block_1_ffn_act

    nnet::einsum_dense<bit_block_1_ffn_act_t, bit_block_1_ffn_fc2_t, config70>(layer68_out, layer70_out, w70, b70); // bit_block_1_ffn_fc2

    nnet::normalize<bit_block_1_ffn_fc2_t, bit_block_1_ffn_fc2_affine_t, config72>(layer70_out, layer72_out, s72, b72); // bit_block_1_ffn_fc2_affine

    nnet::add<bit_block_1_add_attn_t, bit_block_1_ffn_fc2_affine_t, bit_block_1_add_ffn_t, config73>(layer63_out, layer72_out, layer73_out); // bit_block_1_add_ffn

    nnet::global_pooling1d_cl<bit_block_1_add_ffn_t, gap_t, config74>(layer73_out, layer74_out); // gap

    nnet::dense<gap_t, head_fc1_t, config76>(layer74_out, layer76_out, w76, b76); // head_fc1

    nnet::normalize<head_fc1_t, head_fc1_affine_t, config78>(layer76_out, layer78_out, s78, b78); // head_fc1_affine

    nnet::relu<head_fc1_affine_t, head_act_t, relu_config79>(layer78_out, layer79_out); // head_act

    nnet::dense<head_act_t, head_fc2_t, config81>(layer79_out, layer81_out, w81, b81); // head_fc2

    nnet::normalize<head_fc2_t, result_t, config83>(layer81_out, layer83_out, s83, b83); // head_fc2_affine

}

