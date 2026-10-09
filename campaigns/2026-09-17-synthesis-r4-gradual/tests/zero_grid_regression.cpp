// Regression for hls4ml 1.3.0 zero-width quantizer fusion after ReLU.
// Run from this directory against the generated project's ap_types headers:
// c++ -std=c++14 -I../export/hls_prj_rf1/firmware/ap_types \
//     zero_grid_regression.cpp -o /tmp/r4-zero-grid-regression
// /tmp/r4-zero-grid-regression
// No vendor tools, model inference, or remote resources are required.
#include <algorithm>
#include <cassert>
#include <iostream>
#include "ap_fixed.h"

using Original = ap_fixed<1, 1, AP_RND_CONV, AP_SAT>;
using Broken = ap_ufixed<1, 0, AP_RND_CONV, AP_SAT>;
using Repaired = ap_fixed<1, 1, AP_RND_CONV, AP_SAT>;

int main() {
    constexpr double eps = 1.0 / 65536.0;
    const double cases[] = {
        -32.0, -1.0, -0.75, -0.5-eps, -0.5, -0.5+eps,
        -0.25, -eps, -0.0, 0.0, eps,
        0.25-eps, 0.25, 0.25+eps,
        0.5-eps, 0.5, 0.5+eps, 0.75, 1.0, 32.0
    };
    unsigned mismatches = 0;
    for (double x : cases) {
        // Mirror nnet::relu: clamp before casting to the fused result type.
        const double relu = std::max(x, 0.0);
        Original original = relu;
        Broken broken = relu;
        Repaired repaired = relu;
        // Signed KIF(1,0,0) has exactly {-1,0}; nonnegative inputs saturate to 0.
        assert(original.to_double() == 0.0);
        assert(repaired.to_double() == original.to_double());
        // Incorrectly forcing zero-width unsigned KIF to width 1 adds level 0.5.
        const double expected_broken = relu > 0.25 ? 0.5 : 0.0;
        assert(broken.to_double() == expected_broken);
        mismatches += broken.to_double() != original.to_double();
        std::cout << x << ' ' << original.to_double() << ' '
                  << broken.to_double() << ' ' << repaired.to_double() << '\n';
    }
    assert(mismatches > 0);
    // Confirm signed grid itself retains its negative level before ReLU.
    Original negative = -1.0;
    assert(negative.to_double() == -1.0);
    std::cout << "ZERO_GRID_REGRESSION_PASS cases="
              << sizeof(cases) / sizeof(cases[0])
              << " reproduced_broken_cases=" << mismatches << '\n';
}
