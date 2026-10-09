# PREFLIGHT — <campaign id>

Date: . Code sha: . ConfigMap: . Generator: .

## Configs

| arm | config file | builds on CPU | params | reload max |Δ| (tol 1e-7, TF32 off) |
| --- | --- | --- | --- | --- |

## Gates

- `preflight_final.sh`: PREFLIGHT_ALL_PASS / FAIL (log path)
- smoke (2 files, 3 epochs): ran / did not (path)

## Manifests

```
$ python3 nrp-lab/nrp_doctor.py lint <job>.yaml
<pasted output; every WARN read and answered below>
```

## Packing benchmark

K arms per pod = ; measured GPU utilisation (window, mean/median/p10) = ; cpu/memory per pod = .

## Open items before launch

- 
