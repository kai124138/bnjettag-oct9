# GPU selection for Chang and Delta (decision 2026-09-28)

This policy supersedes the A10-only **future-launch** rule in the Chang and Delta campaign
documents. The A10 pilot and canary Jobs already running remain evidence of what was actually
launched; their manifests and RUN/review records are historical and must not be rewritten.

**2026-10-05 (Kai):** the Delta STUDY's ≥45 GB rule for A07 ([A1]) no longer applies. This
policy governs A07 like every other class: 24 GB cards are eligible at the measured K, subject to
the 90 % memory ceiling and NRP's 40 % utilization floor (rule PACK). See `decisions.md`.

## Objective

Minimize the time to finish the registered training runs, subject to the experiment's GPU
matching, memory, host-memory and cluster gates. Choose by **measured completed run-epochs per
GPU-hour and projected campaign finish time**, including queue delay and the number of GPUs that
can actually schedule. A product name, theoretical FLOPS, GPU-memory use, or one instantaneous
`nvidia-smi` utilization reading does not establish training speed.

## Candidate products and access

Try `NVIDIA-GeForce-RTX-4090`, `NVIDIA-L40S`, `NVIDIA-L40`,
`NVIDIA-GeForce-RTX-3090`, and `NVIDIA-A10` first. These use the ordinary
`nvidia.com/gpu` request in this cluster. Also test `NVIDIA-A100-SXM4-80GB`,
`NVIDIA-A100-80GB-PCIe`, `NVIDIA-A100-PCIE-40GB`, `NVIDIA-RTX-A6000`, and
`NVIDIA-A40` when quota and a schedulable node permit; they use product-specific resource
requests (`nvidia.com/a100`, `nvidia.com/rtxa6000`, `nvidia.com/a40`). A100 is **eligible for
benchmarking and production if it wins the measured rule**, replacing the former blanket ban.
H100, H200 and GH200 currently have zero `cms-ml` quota; reserved nodes are unavailable. Check
quota, node taints and scheduling again at launch. Node allocatable count is not free capacity.
Do not place the same Kubernetes Job across products with different resource-request keys.

## Selection gate before a new production GPU product

1. On each schedulable candidate, run the **same frozen code, input cache, batch, precision,
   trace cadence and representative E and A07 arms**. Use a separate benchmark run root and
   disable W&B or give the benchmark a distinct W&B identity. Record product, node, driver,
   code/config hashes, pack size K, CPU and host RAM,
   queue time, per-epoch wall time including trace epochs, GPU memory peak and `nvidia-smi`
   utilization sampled each minute. Benchmark at least two trace cycles after warm-up and
   report median and total elapsed seconds per completed run-epoch. This is telemetry, never a
   physics result.
2. Test pack sizes until the best safe throughput is found. Keep observed peak GPU memory at
   or below 90% of the card, pass the full-horizon host-RSS projection gate, avoid OOM/NaN,
   and verify the GPU fingerprint and EBOP certification on that product. Give each arm enough
   CPU and host RAM; larger VRAM alone does not justify adding arms. Do not change a training
   recipe or evaluation rule to make a product look faster.
3. Prefer the candidate with the earliest projected campaign finish at the number of GPUs
   that can actually schedule. If two candidates finish within 10% of each other, use the less
   scarce or smaller GPU. Do not wait for a premium GPU if its queue delay exceeds its measured
   runtime gain. Save the benchmark and calculation in PREFLIGHT before generating production
   manifests; pin the chosen product and resource key in each Job.
4. The utilization target is a **rolling three-hour mean of at least 40% during active training**,
   checked from one-minute samples. A short benchmark is a provisional screen; continue the
   three-hour check after launch. If a healthy job is below 40%, first diagnose data/CPU stalls,
   then try a safe larger pack and remeasure throughput. If it remains below 40%, move the next
   pack to a smaller suitable GPU. Stop or re-pack a running job only at a verified checkpoint;
   do not discard progress to satisfy a utilization statistic. GPU utilization is the fraction
   of sampled time with a kernel running, **not** percent of peak compute capacity ([NVIDIA
   definition](https://docs.nvidia.com/deploy/nvidia-smi/)). A 100%-busy A10 may still finish
   fewer runs per hour than a 40%-busy faster GPU; elapsed time is the primary metric.

## Scientific and operational constraints

- Chang: the existing A10 regime-B pilots finish on A10. Before a new product runs production,
  repeat the timing/memory canary and the fingerprint/certification checks on it. Keep each
  seed's paired arms on the same GPU product and record it in the evaluation and paired tables.
- Delta: keep each cell, its matched replica and placebo on the same GPU product; use one product
  per family when possible. Run an E and A07 memory/timing canary for each selected product.
  Recompute K and the pack manifest for that product. A 24-GB K is not a 48/80-GB K.
- Preserve the known-bad-node exclusions, `nrp_doctor.py lint`, the 10-Delta-pod cap, the
  pilot/readout launch gates and the registered run count. Existing A10 manifests are launch
  history; create new named manifests for a product change rather than editing a live Job.
