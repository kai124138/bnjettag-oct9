"""Seven pre-registered N8/350k/1000-epoch ablations; no launch side effects."""
import copy
import json
from pathlib import Path
from gen_ebops_n8 import make_long_budget

GROUP = 'ebops-n8-20260912-ablation'
ARMS = ('r0-baseline', 'r1-channel', 'r2-ffn32', 'r3-prob8', 'r4-gradual', 'r5-recovery', 'r6-distill')
TEACHER = 'kayamaguchi-uc-san-diego/BNJetTag-EBOPs-N8/model-ebops-n8-20260910-control-w1a8-s1:v0'


def make_ablation(arm):
    assert arm in ARMS
    cfg = copy.deepcopy(make_long_budget())
    cfg['name'] = f'{GROUP}-{arm}-w1a8'
    cfg['quant'].update(act_granularity='tensor', softmax_out_bits=10, softmax_out_i=1)
    cfg['train'].update(split_seed=1, order_seed=20260912, val_batch=1024)
    cfg['experiment'] = {'arm': arm, 'group': GROUP, 'seed': 1,
                         'checkpoint_every_epochs': 1, 'remote_every_epochs': 25}
    if arm == 'r1-channel':
        cfg['quant']['act_granularity'] = 'channel'
    elif arm == 'r2-ffn32':
        cfg['arch']['ffn_dim'] = 32
    elif arm == 'r3-prob8':
        cfg['quant']['softmax_out_bits'] = 8
    elif arm == 'r4-gradual':
        cfg['experiment']['target_schedule'] = [[0, 1000000], [250, 750000], [500, 500000], [750, 350000]]
    elif arm == 'r5-recovery':
        cfg['experiment']['recovery_after_epochs'] = 800
    elif arm == 'r6-distill':
        cfg['experiment']['distillation'] = {'teacher_artifact': TEACHER, 'temperature': 2., 'coefficient': .5}
    return cfg


if __name__ == '__main__':
    for arm in ARMS:
        cfg = make_ablation(arm)
        path = Path(__file__).parent / (cfg['name'] + '.json')
        path.write_text(json.dumps(cfg, indent=2) + '\n')
        print(path.name)
