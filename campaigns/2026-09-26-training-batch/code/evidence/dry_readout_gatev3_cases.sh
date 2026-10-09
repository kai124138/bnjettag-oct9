set -u
cd <scratch>
run(){ tag=$1; job=$2; { echo "CWD $(pwd) $(date -u) case $tag"; python3 /Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-26-training-batch/code/evidence/dry_readout_run.py /Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-26-training-batch/manifests/$job <scratch>/dry /Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-26-training-batch/manifests/chang0926-code.tar.gz <scratch>/uvpy; } > <scratch>/dry_readout_$tag.log 2>&1; echo "$tag exit $?"; }
run b5_gatev3 readout-b5-job.json
run b3_gatev3_mismatch readout-b3-job.json
mv <scratch>/dry/chang-n64-20260926/pilot-b/runs/chang0926-e1-n64-s1/snapshots/epoch-0500 <scratch>/e1-snap-aside
echo '{"note": "dry-run plant"}' > <scratch>/dry/chang-n64-20260926/pilot-b/runs/chang0926-e1-n64-s1/RSS_GATE_FAIL.json
mv <scratch>/dry/chang-n64-20260926/pilot-b/runs/chang0926-d-n64-s1/snapshots/epoch-0500 <scratch>/d-snap-aside
run b5_gatev3_partial readout-b5-job.json
for n in a-n64-s1 a-n64-s2 cprime-n64-s1; do mv <scratch>/dry/chang-n64-20260926/pilot-b/runs/chang0926-$n/snapshots/epoch-0500 <scratch>/$n-snap-aside; done
run b5_gatev3_none readout-b5-job.json
echo ALL_DONE
