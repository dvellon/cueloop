# CuePod simulator

The canonical simulator implementation is `linux/cueloop/simulator.py`; `cuepod_sim.py` is a source-tree wrapper. It uses the exact production packet encoder and supports:

- deterministic synthetic event signatures;
- mono PCM16 16 kHz WAV replay;
- random packet loss;
- bounded timing jitter and fixed initial latency;
- adjacent-packet reordering;
- periodic stream restart with sequence/sample-clock reset;
- finite runs for automated smoke tests.

Synthetic signatures are deliberately easy for the simulation classifier and are labeled `simulated`. They validate plumbing and uncertainty policy, not model accuracy.

```bash
PYTHONPATH=linux python3 simulator/cuepod_sim.py \
  --sequence 'background:2,door_knock:4,background:2,alarm_beep:4' \
  --loss 0.05 --jitter-ms 15 --reorder-rate 0.02
```

Recordings are ignored by Git. Only use self-recorded or legally reusable audio with a completed provenance manifest.

