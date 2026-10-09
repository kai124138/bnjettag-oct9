# Epoch-10/20 RSS stop rule, pilot-b (PREFLIGHT gate v3 A2; Kai, decisions.md 2026-09-28).
# Per arm: STOP if rss20 + (rss20 - rss10) / 10 * 85 > 8192 MiB, where rssN is host_rss_mb on the
# N-th "[epoch" line of the arm's current process (counted after the last "==== ARM_ATTEMPT").
# The projection reaches process epoch 105, where the in-code RSS gate gives its verdict.
# Input: one arm log (/data/chang-n64-20260926/pilot-b/logs/<run>-<pod>.log), streamed with
#   kubectl -n cms-ml exec <pod> -c train -- cat <log> | awk -v arm=<run> -f rss_rule_epoch10_20.awk
# Output: one line, RSS_RULE <arm> OK|STOP|PENDING|UNREADABLE rss10 rss20 projection_mib limit_mib.
# A check read by cluster-ops, not a result.
# 2026-09-28: limit 6144 -> 8192 MiB with the 8 GiB per-arm resize (decisions.md 2026-09-28).
# 2026-09-28 (PREFLIGHT gate v6): 8192 is a default only; `-v limit=6144` now overrides it.
BEGIN { if (limit == "") limit = 8192; n = 0; r10 = ""; r20 = "" }
/^==== ARM_ATTEMPT/ { n = 0; r10 = ""; r20 = ""; next }
/^\[epoch / {
    n++
    v = "na"
    if (match($0, /host_rss_mb=[0-9.]+/)) v = substr($0, RSTART + 12, RLENGTH - 12)
    if (n == 10) r10 = v
    if (n == 20) r20 = v
}
END {
    if (arm == "") arm = "arm"
    if (r20 == "") { printf "RSS_RULE %s PENDING process_epochs %d\n", arm, n; exit 0 }
    if (r10 == "na" || r20 == "na") { printf "RSS_RULE %s UNREADABLE rss10 %s rss20 %s (count as STOP)\n", arm, r10, r20; exit 1 }
    proj = r20 + (r20 - r10) / 10 * 85
    verdict = (proj > limit) ? "STOP" : "OK"
    printf "RSS_RULE %s %s rss10 %.0f rss20 %.0f projection_mib %.0f limit_mib %d\n", arm, verdict, r10, r20, proj, limit
    exit (verdict == "STOP")
}
