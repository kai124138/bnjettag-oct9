import h5py, numpy as np, glob, os

files = sorted(glob.glob('data/val/*.h5'))
print(f'files: {len(files)}')

f = h5py.File(files[0], 'r')
print('\n--- keys in', os.path.basename(files[0]), '---')
for k in f.keys():
    d = f[k]
    print(f'  {k}: shape={d.shape} dtype={d.dtype}')

for key in ['jetFeatureNames', 'particleFeatureNames']:
    if key in f:
        print(f'\n{key}:')
        print([n.decode() if isinstance(n, bytes) else str(n) for n in f[key][:]])

# aggregate labels + basic stats across all files
tot = 0
label_sum = None
nconst_all = []
pt_all = []
for fn in files:
    with h5py.File(fn, 'r') as h:
        jets = h['jets'][:]
        tot += jets.shape[0]
        labels = jets[:, -6:-1]  # typical: last cols are target labels; verify via names
        if label_sum is None:
            names = [n.decode() for n in h['jetFeatureNames'][:]]
        ls = labels.sum(axis=0)
        label_sum = ls if label_sum is None else label_sum + ls
        plist = h['jetConstituentList']
        # count nonzero constituents per jet using pt (feature index find later); use energy col 3? just nonzero rows
        arr = plist[:]
        nconst_all.append((np.abs(arr).sum(axis=2) > 0).sum(axis=1))
print(f'\ntotal jets: {tot}')
print('jetFeatureNames:', names)
label_names = names[-6:-1]
print('label columns (assumed):', label_names)
print('label counts:', dict(zip(label_names, label_sum.astype(int))))
nc = np.concatenate(nconst_all)
print(f'\nconstituents per jet: mean={nc.mean():.1f} median={np.median(nc):.0f} min={nc.min()} max={nc.max()}')
print('percentiles 5/25/75/95:', np.percentile(nc, [5,25,75,95]))
