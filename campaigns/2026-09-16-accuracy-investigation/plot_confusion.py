import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from apply_correction import corrected_classes

root = Path(__file__).parent
p = json.loads((root/'results/selected_correction.json').read_text())
with np.load(root/'remote-results/r2-ffn32.npz') as d, np.load(root/'remote-results/labels.npz') as lab:
    y = lab['test'].argmax(1)
    before = d['test_logits'].argmax(1)
    after = corrected_classes(d['test_logits'], p, p['checkpoint_sha256'])
fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.3), layout='constrained')
for ax, pred, title in zip(axes, [before, after], ['Original reduced-FFN model · 58.31%', 'Five bias corrections · 59.06%']):
    cm = np.bincount(y*5+pred, minlength=25).reshape(5, 5)
    matrix = cm/cm.sum(1, keepdims=True)*100
    ax.imshow(matrix, vmin=0, vmax=80, cmap='Blues')
    for i in range(5):
        for j in range(5):
            ax.text(j, i, f'{matrix[i,j]:.1f}', ha='center', va='center',
                    color='white' if matrix[i,j] > 40 else '#17344a', fontsize=10)
    ax.set(xticks=range(5), yticks=range(5), xticklabels=['g','q','W','Z','t'],
           yticklabels=['g','q','W','Z','t'], xlabel='Predicted class', ylabel='True class', title=title)
fig.suptitle('Held-out class confusion (% of each true class, 260,000 jets)', fontsize=13)
fig.savefig(root/'results/confusion.png', dpi=180)
fig.savefig(root/'results/confusion.svg')
plt.close(fig)
