"""Seven pre-registered N8/350k/1000-epoch ablations; no launch side effects."""
import copy
import json
from pathlib import Path
from gen_ebops_n8 import make_long_budget

GROUP = 'post_conference_budget350k'
ARMS = ('tensor_quantization', 'channel_quantization', 'reduced_feedforward', 'attention_probability_8bit', 'gradual_budget', 'fixed_width_recovery', 'knowledge_distillation')
TEACHER = ''  # Set a versioned teacher artifact before distillation.


def make_ablation(arm):
    assert arm in ARMS
    cfg = copy.deepcopy(make_long_budget())
    cfg['name'] = f'{GROUP}-{arm}-w1a8'
    cfg['quant'].update(act_granularity='tensor', softmax_out_bits=10, softmax_out_i=1)
    cfg['train'].update(split_seed=1, order_seed=20260912, val_batch=1024)
    cfg['experiment'] = {'arm': arm, 'group': GROUP, 'seed': 1,
                         'checkpoint_every_epochs': 1, 'remote_every_epochs': 25}
    if arm == 'channel_quantization':
        cfg['quant']['act_granularity'] = 'channel'
    elif arm == 'reduced_feedforward':
        cfg['arch']['ffn_dim'] = 32
    elif arm == 'attention_probability_8bit':
        cfg['quant']['softmax_out_bits'] = 8
    elif arm == 'gradual_budget':
        cfg['experiment']['target_schedule'] = [[0, 1000000], [250, 750000], [500, 500000], [750, 350000]]
    elif arm == 'fixed_width_recovery':
        cfg['experiment']['recovery_after_epochs'] = 800
    elif arm == 'knowledge_distillation':
        cfg['experiment']['distillation'] = {'teacher_artifact': TEACHER, 'temperature': 2., 'coefficient': .5}
    return cfg


if __name__ == '__main__':
    for arm in ARMS:
        cfg = make_ablation(arm)
        path = Path(__file__).parent / (cfg['name'] + '.json')
        path.write_text(json.dumps(cfg, indent=2) + '\n')
        print(path.name)
