# Epoch-20 terminal projection, pilot-b (RUN.md "Regime-B pilot: operating rules", 8 GiB resize
# timing rule, 2026-09-28). Per arm: least-squares fit of host_rss_mb against process epoch over
# process epochs 5-20 (16 points, counted after the last "==== ARM_ATTEMPT"), the same form as the
# in-code RSS gate on a shorter window; projection = fitted RSS at epoch 5 + slope x 7000.
# Verdict against both limits: OVER6144 means a pod still on the 6 GiB manifests would fail its
# in-code gate at process epoch 105; OVER8192 means the 8 GiB manifests would fail it too.
#   kubectl -n cms-ml exec <pod> -c train -- cat <log> | awk -v arm=<run> -f rss_proj7000_epoch20.awk
# Output: RSS_PROJ7000 <arm> OK|OVER6144|OVER8192|PENDING|UNREADABLE slope_mb_per_epoch baseline_mb projection_mb.
# Exit 1 on OVER6144, OVER8192 or UNREADABLE. A check read by cluster-ops, not a result.
BEGIN { total = 7000; w = 5; e = 20; n = 0; bad = 0 }
/^==== ARM_ATTEMPT/ { n = 0; bad = 0; delete r; next }
/^\[epoch / {
    n++
    if (match($0, /host_rss_mb=[0-9.]+/)) r[n] = substr($0, RSTART + 12, RLENGTH - 12) + 0
    else if (n >= w && n <= e) bad = 1
}
END {
    if (arm == "") arm = "arm"
    if (n < e) { printf "RSS_PROJ7000 %s PENDING process_epochs %d\n", arm, n; exit 0 }
    if (bad) { printf "RSS_PROJ7000 %s UNREADABLE (host_rss_mb missing in epochs %d-%d)\n", arm, w, e; exit 1 }
    k = 0; sx = 0; sy = 0; sxx = 0; sxy = 0
    for (i = w; i <= e; i++) { x = i - w; k++; sx += x; sy += r[i]; sxx += x * x; sxy += x * r[i] }
    slope = (k * sxy - sx * sy) / (k * sxx - sx * sx)
    base = (sy - slope * sx) / k
    proj = base + slope * total
    v = (proj > 8192) ? "OVER8192" : (proj > 6144) ? "OVER6144" : "OK"
    printf "RSS_PROJ7000 %s %s slope_mb_per_epoch %.3f baseline_mb %.0f projection_mb %.0f limits 6144/8192\n", arm, v, slope, base, proj
    exit (v != "OK")
}
