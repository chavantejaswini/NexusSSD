# Fleet Maintenance Playbook

Operational guidance for responding to SSD health predictions and alerts.

## Risk bands and actions
- **Low (probability < 30%)**: no action. Continue routine monitoring.
- **Medium (30-70%)**: put the drive on a watchlist. Ensure backups/replication
  are current and confirm a spare of the same model is on hand.
- **High (>= 70%)**: schedule proactive replacement within the maintenance
  window. Migrate data off the drive before replacement.

## Responding to a critical alert
1. Confirm the drive still passes reads; if uncorrectable errors are present,
   evacuate data immediately.
2. Drain the drive from any RAID/erasure-coded set or rebalance the workload.
3. Replace the drive and record the action in the maintenance log.
4. RMA the failed unit if under warranty.

## Preventive maintenance
- Keep firmware current; vendors frequently ship reliability fixes.
- Maintain 10-20% free space to limit write amplification.
- Track endurance utilization; plan replacements before drives exceed 90% of
  rated TBW.
- Keep drive temperatures within the vendor's recommended range with adequate
  airflow.

## Spares strategy
Stock spares per model in proportion to fleet size and observed failure rate.
When a model shows correlated failures, increase its spare buffer and accelerate
the replacement schedule for that cohort.
