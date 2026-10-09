"""Read and hash the existing cache, then build four production-sized models on CPU."""
import fcntl
import json
from pathlib import Path
import numpy as np
import run_engram


def main():
    cache = Path('/data/batch20260917/n16/data')
    out = Path('/data/engram-study-20260918/preflight')
    out.mkdir(parents=True, exist_ok=True)
    ablation, engram = run_engram.runtime()
    import keras
    reports = []
    with (cache / 'prepare.lock').open('r') as lock:
        fcntl.flock(lock, fcntl.LOCK_SH)
        for index in range(4):
            name = f'engram-e{index:02d}-s1'
            cfg = json.loads((Path('/work/code/configs/engram') / f'{name}.json').read_text())
            run_engram.validate_cfg(cfg)
            arrays, info = run_engram.load_cache(cache, cfg)
            keras.backend.clear_session()
            sample = np.asarray(arrays[0][:4096])
            model, evidence = run_engram.builder_for(info)(cfg, sample, 1)
            ablation.binary_gate(model, cfg)
            trace = ablation.compute_ebops(model, sample[:256])
            memory = run_engram.enforce_memory(cfg, engram)
            reports.append({'run': name, 'parameters': model.count_params(),
                'data_info': info, 'initialization': evidence,
                'initial_cost': engram.accounting(model, trace), 'memory': memory,
                'initial_diagnostics': engram.diagnostic_observer()(model, sample[:256], 0)})
            print(f'PRODUCTION_BUILD_PASS {name} parameters={model.count_params()}', flush=True)
    run_engram.write_json(out / 'production.json', {'status': 'PASS', 'arms': reports,
        'source_manifest': run_engram.source_manifest(), 'test_set_used': False})
    print('PREFLIGHT_ALL_PASS', flush=True)


if __name__ == '__main__':
    main()
