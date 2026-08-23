# SSD Wear and Endurance

NAND flash cells wear out after a finite number of program/erase (P/E) cycles.
Endurance is rated as TBW (terabytes written) or DWPD (drive writes per day) over
the warranty period. Understanding wear is central to predicting failures before
they happen.

## Endurance metrics
- **TBW**: total host data that can be written over the drive's life.
- **DWPD**: how many times the full capacity can be overwritten per day for the
  warranty term. Enterprise mixed-use drives are typically 1-3 DWPD;
  read-intensive drives are often 0.5-1 DWPD.
- **Percentage Used** (NVMe): the controller's own estimate of consumed
  endurance, 0% when new and climbing past 100% once the rated endurance is
  exceeded. Values above 90% warrant replacement planning.

## Write amplification
Writes to flash are amplified by garbage collection and wear-leveling. A write
amplification factor (WAF) above ~3-4 shortens drive life significantly. Random
small writes and a nearly full drive both increase WAF. Keeping 10-20% of the
drive unprovisioned reduces WAF and extends endurance.

## Wear-leveling
The controller spreads writes evenly across all blocks so no single block wears
out prematurely. When wear-leveling can no longer find fresh blocks, reallocated
sector counts rise and the media wearout indicator approaches its limit —
signalling end of life.
