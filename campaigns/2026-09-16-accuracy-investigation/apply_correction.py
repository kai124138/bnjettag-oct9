"""Apply the validation-selected correction to matching model logits.

Example:
  python apply_correction.py --logits logits.npy --output classes.npy \
    --checkpoint-sha256 <SHA256 of the model that produced the logits>
"""
import argparse
import json
from pathlib import Path
import numpy as np


def corrected_classes(logits, parameters, checkpoint_sha256):
    if checkpoint_sha256 != parameters['checkpoint_sha256']:
        raise ValueError('Correction belongs to a different model checkpoint')
    logits = np.asarray(logits, dtype=np.float32)
    if logits.ndim != 2 or logits.shape[1] != 5 or not np.isfinite(logits).all():
        raise ValueError('Expected finite N x 5 logits in g/q/W/Z/t order')
    scale = np.asarray(parameters['scale'], dtype=np.float32)
    bias = np.asarray(parameters['bias'], dtype=np.float32)
    # Explicit staged float32 arithmetic, matching the deployment-stability test.
    corrected = np.multiply(logits, scale, dtype=np.float32)
    np.add(corrected, bias, out=corrected)
    return corrected.argmax(axis=1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--logits', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--checkpoint-sha256', required=True)
    p.add_argument('--parameters', type=Path, default=Path(__file__).parent/'results/selected_correction.json')
    args = p.parse_args()
    params = json.loads(args.parameters.read_text())
    np.save(args.output, corrected_classes(np.load(args.logits), params, args.checkpoint_sha256))


if __name__ == '__main__':
    main()
