"""Small frozen-backbone head experiment; train only on training features.

Select 4/8-bit heads on internal validation under measured 350k EBOP budget.
All earlier layers remain binary. This is explicitly a mixed-precision model.
"""
import json
import os
from pathlib import Path
import time
import hashlib
import numpy as np
from scipy.optimize import minimize
from scipy.special import logsumexp, softmax


def fit_head(x, y, kernel, bias, ridge):
    mean, std = x.mean(0), x.std(0)
    std = np.where(std < 1e-6, 1., std)
    x = (x-mean)/std
    start = np.r_[(kernel*std[:, None]).ravel(), bias+mean@kernel]
    def objective(p):
        w, b = p[:-5].reshape(-1, 5), p[-5:]
        z = x@w+b
        loss = np.mean(logsumexp(z, axis=1)-z[np.arange(len(y)), y]) + ridge*np.sum(w*w)/2
        residual = softmax(z, axis=1)
        residual[np.arange(len(y)), y] -= 1
        gradient = np.r_[(x.T@residual/len(y)+ridge*w).ravel(), residual.mean(0)]
        return loss, gradient
    result = minimize(objective, start, method='L-BFGS-B', jac=True,
                      options={'maxiter': 150, 'ftol': 1e-9})
    w = result.x[:-5].reshape(-1, 5)/std[:, None]
    b = result.x[-5:]-mean@w
    return w, b, {'success': bool(result.success), 'message': str(result.message),
                  'iterations': int(result.nit), 'final_objective': float(result.fun)}


def main():
    import tensorflow as tf
    import keras
    from hgq.layers import QDense
    from hgq.quantizer import QuantizerConfig
    from bnhgq2.compat import apply_keras_compat
    from bnhgq2.subln import register_subln
    from bnhgq2.ebops_calc import compute_ebops
    import bnhgq2.qat
    from calibrate_outputs import metrics, paired_ci
    tf.config.threading.set_intra_op_parallelism_threads(4)
    tf.config.threading.set_inter_op_parallelism_threads(2)
    apply_keras_compat(); register_subln()
    root = Path(os.environ.get('HEAD_OUTPUT', '/data/accuracy-head-features-20260917'))
    start = time.perf_counter()
    with np.load(root/'features.npz') as d:
        xt = d['train_x'].astype(float)
        xv = d['validation_x'].astype('float32')
        xs = d['test_x'].astype('float32')
        yt, yv, ys = [d[k].argmax(1) if d[k].ndim == 2 else d[k] for k in ('train_y','validation_y','test_y')]
        w0, b0 = d['original_kernel'], d['original_bias']
    source = Path('/data/accuracy-diagnostics-20260917/snapshots/r1-channel/model_best.keras')
    model = keras.models.load_model(source, compile=False)
    old = model.get_layer('head_fc2')
    cfg = old.get_config()
    raw_val = np.load('/data/ebops-n8-20260912-ablation/data/x_val.npy', mmap_mode='r')
    base_cost = compute_ebops(model, np.asarray(raw_val[:256]))['total']
    assert base_cost == 317890
    baseline_v = np.asarray(old(xv, training=False))
    baseline_s = np.asarray(old(xs, training=False))
    np.testing.assert_allclose(baseline_v[:256], model(np.asarray(raw_val[:256]), training=False), atol=1e-5, rtol=1e-5)
    candidates = []
    best = {'name':'original_binary', 'validation_accuracy':float((baseline_v.argmax(1)==yv).mean()), 'ebops':base_cost, 'bits':1}
    best_model, best_logits = model, baseline_s
    report = {'protocol': '100k train-only frozen features; two prespecified ridge strengths and final-head bit widths 4/8; select by full internal validation accuracy subject to native HGQ2 EBOPs <=350k. Test is never used for selection.',
              'checkpoint_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'n_train':len(yt), 'n_validation':len(yv), 'n_test':len(ys),
              'baseline_test':metrics(ys,baseline_s), 'baseline_validation_accuracy':best['validation_accuracy'],
              'baseline_ebops':base_cost, 'candidates':candidates}
    for ridge in (1e-4, 1e-2):
        w, b, fit = fit_head(xt, yt, w0, b0, ridge)
        if not fit['success']:
            candidates.append({'ridge':ridge, 'fit':fit, 'excluded':'optimizer did not converge'})
            continue
        for bits in (4, 8):
            step_exponent = int(np.ceil(np.log2(max(np.max(np.abs(w)),1e-12)/(2**(bits-1)-1))))
            f0, i0 = -step_exponent, bits-1+step_exponent
            quant = QuantizerConfig('kif','weight',k0=1,i0=i0,f0=f0,
                                     round_mode='RND_CONV',overflow_mode='SAT',trainable=False,heterogeneous_axis=())
            layer_cfg = dict(cfg)
            layer_cfg['name'] = f'head_fc2_w{bits}_r{str(ridge).replace(".","p")}'
            layer_cfg['kq_conf'] = keras.saving.serialize_keras_object(quant)
            head = QDense.from_config(layer_cfg)
            output = head(old.input)
            candidate_model = keras.Model(model.inputs,output)
            head.iq.set_weights(old.iq.get_weights())
            head._kernel.assign(w.astype('float32')); head.bias.assign(b.astype('float32'))
            val_logits = np.asarray(head(xv,training=False))
            np.testing.assert_allclose(val_logits[:256], candidate_model(np.asarray(raw_val[:256]),training=False),atol=1e-5,rtol=1e-5)
            cost = compute_ebops(candidate_model,np.asarray(raw_val[:256]))
            rec = {'name':head.name,'ridge':ridge,'bits':bits,'integer_bits_excluding_sign':i0,'fractional_bits':f0,
                   'validation_accuracy':float((val_logits.argmax(1)==yv).mean()),'ebops':cost['total'],
                   'feasible':cost['total']<=350000,'fit':fit, 'per_layer_ebops':cost['per_layer']}
            candidates.append(rec)
            print('[candidate]',json.dumps(rec),flush=True)
            if rec['feasible'] and (rec['validation_accuracy'],-rec['ebops']) > (best['validation_accuracy'],-best['ebops']):
                best, best_model = rec, candidate_model
                # Cache chosen weights; test evaluation happens after all choices.
    if best['name'] != 'original_binary':
        head = best_model.layers[-1]
        best_logits = np.asarray(head(xs,training=False))
        best_model.save(root/'selected_model.keras')
        reload = keras.models.load_model(root/'selected_model.keras',compile=False)
        np.testing.assert_allclose(reload(np.asarray(raw_val[:256]),training=False), best_model(np.asarray(raw_val[:256]),training=False),atol=1e-6,rtol=1e-6)
        reloaded_cost = compute_ebops(reload,np.asarray(raw_val[:256]))['total']
        assert reloaded_cost == best['ebops']
        np.savez_compressed(root/'selected_head.npz',kernel=np.asarray(head.qkernel),bias=np.asarray(head.qbias))
        report['selected_checkpoint_sha256']=hashlib.sha256((root/'selected_model.keras').read_bytes()).hexdigest()
    report.update(selected=best,selected_test=metrics(ys,best_logits),
                  paired_improvement=paired_ci(ys,baseline_s,best_logits),seconds=time.perf_counter()-start,
                  limitation='One seed,100k training subset; head weights are now mixed precision if selected. Native EBOPs verified; FPGA synthesis, accumulator/export equivalence and actual hardware latency remain unmeasured.')
    np.savez_compressed(root/'head_test_predictions.npz',labels=ys,baseline=baseline_s,selected=best_logits)
    (root/'head_report.json').write_text(json.dumps(report,indent=2))
    print('[HEAD_DONE]',json.dumps({k:v for k,v in report.items() if k not in ('candidates','baseline_test','selected_test')}),flush=True)


if __name__=='__main__':
    main()
