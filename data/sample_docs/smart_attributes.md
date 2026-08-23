# SSD SMART Attributes Reference

SMART (Self-Monitoring, Analysis and Reporting Technology) attributes expose the
internal health of an SSD. The attributes below are the most predictive of
impending failure for NAND flash drives.

## SMART 5 — Reallocated Sectors Count
The raw value is the number of sectors the controller has retired and remapped to
spare area after detecting errors. On a healthy SSD this value stays at or near
zero for most of the drive's life. A sudden, sustained increase in reallocated
sectors is one of the strongest predictors of near-term failure: once the spare
pool is exhausted the drive can no longer remap bad blocks and will fail.

## SMART 9 — Power-On Hours
Total time the drive has been powered on. Useful as an age/wear proxy but weakly
predictive on its own — a high power-on-hours drive can still be healthy.

## SMART 194 — Temperature
Drive temperature in degrees Celsius. Sustained operation above roughly 60-70 °C
accelerates wear and correlates with error-rate spikes. A rising temperature
trend in the weeks before failure is common as controller activity increases
while it struggles to remap failing cells.

## SMART 233 / 177 — Media Wearout Indicator
A normalized estimate of remaining (or consumed) endurance based on program/erase
cycles. As the drive approaches its rated endurance the wearout indicator climbs
toward 100% consumed. Drives past ~90% consumed should be scheduled for
proactive replacement.

## SMART 241 — Total LBAs Written
Cumulative host writes. Combined with the drive's rated TBW (terabytes written)
this gives a direct endurance-utilization figure.
