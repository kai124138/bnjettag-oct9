"""Independent train/validation synthetic head regression and gradient audit."""
import importlib.util
import json
from pathlib import Path
import time

import numpy as np
from scipy.special import logsumexp

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('refit_head_under_test', root/'refit_head.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
rng = np.random.default_rng(72913)
n_features = 32
n_train, n_val = 3000, 1000
scales = np.geomspace(.03, 30., n_features)
offsets = rng.normal(size=n_features)*8
standard_train = rng.normal(size=(n_train, n_features))
standard_val = rng.normal(size=(n_val, n_features))
truth = rng.normal(size=(n_features, 5))
truth[10:] = 0
true_bias = rng.normal(size=5)*.15
train_y = (standard_train@truth+true_bias).argmax(1)
val_y = (standard_val@truth+true_bias).argmax(1)
train_x = standard_train*scales+offsets
val_x = standard_val*scales+offsets
train_x[:, -1] = val_x[:, -1] = 5.  # constant input tests scale fallback
kernel = rng.normal(size=(n_features, 5))*.01
bias = rng.normal(size=5)*.01

captured = {}
actual_minimize = module.minimize

def check_objective(objective, initial, **kwargs):
    mean, std = train_x.mean(0), train_x.std(0)
    std = np.where(std < 1e-6, 1., std)
    normalized = (train_x-mean)/std
    warm_logits = normalized@initial[:-5].reshape(-1,5)+initial[-5:]
    np.testing.assert_allclose(warm_logits, train_x@kernel+bias, atol=1e-11, rtol=1e-11)
    _, gradient = objective(initial)
    relative_errors = []
    for index in rng.choice(len(initial), 20, replace=False):
        delta = np.zeros_like(initial); delta[index] = 1e-6
        numerical = (objective(initial+delta)[0]-objective(initial-delta)[0])/2e-6
        relative_errors.append(abs(numerical-gradient[index]) / max(1.,abs(numerical),abs(gradient[index])))
    assert max(relative_errors) < 1e-7, max(relative_errors)
    result = actual_minimize(objective, initial, **kwargs)
    captured['normalization_mean'] = mean
    captured['normalization_std'] = std
    captured['optimized_parameters'] = result.x
    captured['gradient_max_relative_error'] = max(relative_errors)
    captured['initial_objective'] = objective(initial)[0]
    captured['final_gradient_norm'] = float(np.linalg.norm(objective(result.x)[1]))
    return result

module.minimize = check_objective
start = time.perf_counter()
w, b, fit = module.fit_head(train_x, train_y, kernel, bias, 1e-4)
assert fit['success'], fit
optimized = captured['optimized_parameters']
normalized_val = (val_x-captured['normalization_mean'])/captured['normalization_std']
expected_val_logits = normalized_val@optimized[:-5].reshape(-1,5)+optimized[-5:]
actual_val_logits = val_x@w+b
np.testing.assert_allclose(actual_val_logits, expected_val_logits, atol=1e-10, rtol=1e-10)
validation_accuracy = float((actual_val_logits.argmax(1)==val_y).mean())
assert validation_accuracy > .94, validation_accuracy
assert fit['final_objective'] < captured['initial_objective']*.2
assert captured['final_gradient_norm'] < 1e-3
report = {
    'synthetic_only': True, 'fit_success':fit['success'], 'n_train':n_train, 'n_validation':n_val,
    'train_validation_generated_independently':True, 'constant_feature_included':True,
    'validation_accuracy':validation_accuracy,
    'folded_prediction_max_abs_error':float(abs(actual_val_logits-expected_val_logits).max()),
    'gradient_max_relative_error':captured['gradient_max_relative_error'],
    'final_gradient_norm':captured['final_gradient_norm'],
    'initial_objective':captured['initial_objective'], 'fit':fit,
    'elapsed_seconds':time.perf_counter()-start,
}
(Path(__file__).parent/'head-fit-test-result.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
