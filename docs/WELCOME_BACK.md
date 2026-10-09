# Welcome back: the lab in plain language

Written 2026-10-05 for Kai after a month away. Read top to bottom once; the glossary at the
end is for looking things up. No number here is a validated result.

## 1. What we are trying to do

CMS's Level-1 trigger has about a microsecond to decide whether to keep a collision. We want
a small neural network that looks at a jet (a spray of particles) and says which of 5 kinds
of particle made it. It has to run on an FPGA chip, fast and cheap.

Our twist: every weight in the network is either **+1 or −1** ("binary"). Multiplying by ±1 is
almost free on a chip, so the bet is that a binary network is far cheaper in hardware while
staying nearly as accurate. That bet is **the thesis**.

## 2. The yardstick: Chang's paper

A group (Laatu, Sun, … ; we call it "Chang") published a small transformer for the same job
(arXiv:2510.24784). Their weights are not binary; each weight's bit width is learned. They
kept the network's size under a budget of **350k EBOPs** (EBOPs ≈ a count of the bit-level
work the network does; a proxy for chip cost).

In **August** we ran their released code ourselves, the "replication". It matched or beat
their paper at 7 of 8 sizes (for example 80.56 % at N=64). That was one seed and picked on
the test set, so it is a sanity check, not a result we can quote.

## 3. Our plan: same recipe, binary weights

We copied Chang's training recipe exactly ("the Chang recipe"): 7,000 epochs, batch 2,790, a
learning rate of 3e-3, the 350k budget, jets with 64 particles (N=64), and 3 numbers per
particle. The only intended difference is binary weights. Then we compare.

A **controller** (a "PID") runs during training. It turns a size penalty up or down so the
network shrinks until it hits the 350k budget. Think of it as a thermostat for network size.

## 4. What happened from Sept 26 to Oct 2

Running 7,000 epochs is slow: days per run. So before committing a big batch of runs, we ran
**pilots**: short, cheap test runs (stopped at epoch 500) to check that things behave.

- **Pilot 1 (regime A):** the network size was measured exactly every epoch, which made each run far too slow (projected 17–24 days). Killed after about 9 hours.
- **Pilots 2 and 3 (regime B, Sept 28–29):** measure the size exactly only every 10 epochs. These finished their 500 epochs.
- **What the pilots showed:** at the 350k budget, the binary networks **collapse**. Their attention part stops doing anything (every head looks at every particle equally), and some networks just guess the same class for everything. Larger budgets (5M) worked much better.
- **K1** is a pre-agreed alarm rule written before the pilots. It **fired**, which blocks the big batch of runs until the cause is fixed or understood.
- One suspected cause: the thermostat was reading a **rough size estimate** (about 7 % off) instead of the **exact measurement**. **Option (c)**, which you chose on Oct 1, makes it read the exact measurement. A deeper look suggests this probably isn't the whole story, so option (c) may not cure the collapse. We have to test it.

## 5. Delta, on hold

**Delta** is a separate, pre-planned menu of 103 tweaks to try on the binary network (different
activations, architectures, recipes). So far only test jobs have run: memory checks, one bad
cluster node found and excluded. No real Delta experiment has run. It waits until the main
question is settled.

## 6. Where things stand today (Oct 5)

1. **Running now:** the option (c) **CPU gate**, a code check on a plain CPU (no GPU, no training) that runs the tests and builds every config. It started at 00:11 UTC and has 4 hours at most.
2. **Next if it passes:** three option (c) **pilots** to epoch 500 (about 1–1.5 days) and a **readout** (an analysis job that summarises them). Then we decide whether production can go.
3. **Production:** the real runs. Each arm runs 8 times with different random **seeds**, the full 7,000 epochs. Only production results can go in a paper.
4. **The key comparison is not built yet.** **NB** is the same network but with learned bit widths instead of ±1. "Binary vs NB at the same size" is the experiment that tests the thesis. Its code has to be written.

## 7. When we can write a paper

The nearest paper is a **workshop note**. It needs:
- binary and NB, 8 seeds each, full length, checked and reviewed;
- a cost estimate from chip synthesis on **mulder** (the machine with the FPGA tools, reached through your MacBook).

If binary keeps collapsing, the fallback paper explains why. That is still publishable, but it
also needs NB.

Timelines:
- **ROADMAP.md:** the normal pace gets there mid-November to December.
- **SPRINT_PLAN.md:** if you make the open decisions in one sitting and we run everything in parallel, about a week.

## 8. How work moves through the lab (the "loop")

Every experiment is a **campaign**: a folder `campaigns/<date>-<name>/` that moves through
five phases, one document each:

| phase | document | in plain words |
| --- | --- | --- |
| design | STUDY.md | the question, the runs, the rules for reading results, all written before running |
| preflight | PREFLIGHT.md | build the code, test it, prepare the cluster jobs |
| run | RUN.md | launch, and log what happened |
| verify | VERIFY.md | recompute every number from the saved outputs, with error bars |
| report | REPORT.md | the write-up |

Between phases, reviewer agents check the document and return **PASS**, **ITERATE** (fix and
re-check) or **ESCALATE** (ask you). The main Claude session is the **orchestrator**: it
assigns work to specialist agents and doesn't do the work itself. That arrangement is **JFC**.
Two things always need you: a number entering the official record, and anything leaving the
lab (a push, an email, a publication).

## 9. Where to look

| file | what it is |
| --- | --- |
| `docs/WELCOME_BACK.md` | this page |
| `docs/ROADMAP.md` | the big picture, paper tiers, normal-pace timeline |
| `docs/SPRINT_PLAN.md` | the fastest plan and what blocks speed |
| `local/2026-10-04-session/SESSION.md` | detailed tables of every Chang and Delta run |
| `.claude/memory/decisions.md` | every decision you made, newest on top |
| `campaigns/2026-10-02-chang-option-c/RUN.md` | the job running now |

To check the running job, in a new session:
```
kubectl get job kai-chang1002c-cpugate-691946 -n cms-ml
kubectl logs job/kai-chang1002c-cpugate-691946 -n cms-ml --tail=50
```

## 10. Glossary

**Training words**
- **Epoch:** one full pass of training over all 558,000 training jets. 7,000 epochs means seeing the data 7,000 times.
- **Seed:** the random starting number. Same setup with different seeds shows how much results wobble by luck. We use 8 seeds per arm.
- **Arm:** one recipe variant in an experiment. One arm × 8 seeds = 8 runs.
- **Run:** one arm with one seed, trained once.
- **Validation set (62,000 jets):** data used to pick the best checkpoint during training.
- **Test set (260,000 jets):** data used once at the very end. Picking anything on it is cheating.
- **Checkpoint:** a saved copy of the network at some epoch.
- **Accuracy / AUC:** two ways to score a classifier. Always say which data set the score came from.
- **Telemetry:** numbers printed while training runs. Useful for monitoring; never quotable.
- **Quotable / "in the record":** a number that passed VERIFY and you approved.

**Size and hardware words**
- **EBOPs:** an estimate of how much bit-level work the network does; a proxy for chip cost. The target is 350k.
- **Traced vs in-training EBOPs:** the exact measurement (slow, every 10 epochs) vs the quick running estimate.
- **Feasible:** the network is at or under the EBOP budget.
- **Degenerate:** the network gives the same answer for everything (useless).
- **PID / beta:** the thermostat and its knob that push the network toward the budget.
- **Option (c):** make the thermostat read the exact (traced) EBOPs. Being tested now.
- **FPGA:** a reprogrammable chip, the target hardware.
- **hls4ml:** the tool that converts a network into an FPGA design.
- **csynth, post-route, LUT, DSP:** stages and resource counts from chip-design tools. A LUT is the basic logic cell; DSPs are multiplier blocks (binary should need none).
- **mulder:** the machine with the chip tools; you reach it through your MacBook.
- **II and latency:** how often the chip accepts a new jet, and how long it takes to answer. It must keep up with 40 MHz collisions (25 ns).

**Experiment words**
- **Pilot:** a short test run (500 epochs) to check behaviour before the expensive real runs.
- **Production:** the full-length, 8-seed runs that can go in a paper.
- **Readout:** an analysis job that summarises pilot results against the pre-written rules.
- **K1:** a pre-written alarm rule from the STUDY. It fired, so production is blocked.
- **Regime A / B:** pilots measuring EBOPs exactly every epoch (A, too slow) or every 10 epochs (B, what we use).
- **Canary:** a tiny run just to check memory and speed on a GPU.
- **CPU gate:** a test job with no GPU that checks the code before any training.

**Network and arm names**
- **N=64:** each jet is given to the network as its 64 highest-energy particles.
- **E:** our small transformer: width 24, 2 attention heads.
- **A07:** a larger one: width 32, 4 heads.
- **A:** E, binary weights, Chang's recipe, 350k budget. The main arm.
- **NB:** same as A but with learned-width weights instead of ±1. The comparison that tests the thesis. Not built yet.
- **H:** Chang's own released model run on our data split.
- **FP32-E:** E at full precision, no budget. The accuracy ceiling.
- **B:** A at a 250k budget.
- **C:** A07 at a 5M budget. Worked best in the pilots.
- **C′:** C with a different quantizer.
- **D:** A with our optimizer.
- **F:** E plus position information.
- **E1:** E with 1 head.
- **R:** our older, shorter recipe (1,000 epochs).
- **Delta:** the separate menu of 103 tweaks, on hold.

**Cluster words**
- **NRP / Nautilus:** the shared GPU cluster where training runs. Our namespace is `cms-ml`.
- **Job / pod:** a Job is a request to run something; a pod is the running instance on one machine.
- **K (arms per pod):** how many runs share one GPU. More K means better use of the GPU, but each run is slower.
- **A10, 3090, 4090, A100:** GPU models. A100 is the biggest, but our quota has 1 free; 3090s are plentiful.
- **40 % floor:** NRP flags any pod whose GPU averages under 40 % busy over 3 hours. Three strikes flags the account.
- **Lint / nrp_doctor:** a checker every job file must pass before it can be sent to the cluster.
- **Handoff (`run_handoff.py`):** the tool that freezes a job's exact code and settings, then submits it.
- **Bad node:** a machine with a broken GPU, excluded by name (c6017 is one).

**Lab-process words**
- **Campaign:** one experiment's folder and its 5 phase documents.
- **JFC:** our working style. The orchestrator assigns, specialist agents do, reviewers check.
- **Orchestrator:** the main Claude session.
- **Reviewers:** critical (finds faults), physics (an outside referee's view), constructive (what would strengthen it), arbiter (decides).
- **PASS / ITERATE / ESCALATE:** a reviewer's verdict.
- **Jev:** a helper AI that gives second opinions, such as "is this claim supported by that source?". It never decides anything and never launches jobs.
- **Gate:** a check that must pass before the next step.
