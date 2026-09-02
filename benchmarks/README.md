# Benchmark evidence

Committed summaries in this directory must state the execution host, workload provenance, model/artifact identity, measurement method, and claim boundary. Machine-readable run output goes under ignored `benchmarks/results/` so repeated runs do not pollute source control.

The deterministic transport benchmark exercises the encoded packet → bounded receiver → window → synthetic classifier → temporal-policy path across clean, 5% loss/moderate jitter, and 20% loss/severe jitter profiles:

```bash
PYTHONPATH=linux python3 benchmarks/simulated_transport.py \
  --output benchmarks/results/simulated-transport.json --quiet
```

Its synthetic signatures were authored to test plumbing. Detection rate from this benchmark is not a real-audio model metric or a wireless/RF result.

Evidence tiers are not interchangeable:

- **simulated workload / development computer:** software integration and host latency only;
- **licensed real audio / development computer:** dataset-scoped model metrics, not device performance;
- **UNO Q replay:** target inference performance from provenance-complete prerecorded clips;
- **physical CuePod end to end:** microphone, wireless, target, and cue measurements from the actual assembly.

Never promote a result to a stronger tier without running that setup and retaining its protocol in `HARDWARE_TESTS.md` plus its reviewed summary in `HARDWARE_RESULTS.md`.
