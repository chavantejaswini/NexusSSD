# SSD Failure Signatures

Most SSD failures are preceded by observable telemetry patterns. Recognizing
these signatures lets operators replace drives during a maintenance window rather
than reacting to an outage.

## Reallocated-sector ramp
The classic pre-failure signature: SMART 5 (reallocated sectors) climbs from near
zero to hundreds or thousands over days to a few weeks. Once the ramp begins,
failure typically follows within the prediction horizon. Any non-trivial upward
trend should raise a warning.

## Rising temperature under stable load
When temperature (SMART 194) trends upward without a corresponding change in
workload or ambient conditions, the controller is often working harder to remap
failing cells. A temperature climb combined with reallocated-sector growth is a
high-confidence failure signal.

## Endurance exhaustion
Media wearout indicator or NVMe Percentage Used approaching 100% means the drive
is at end of rated life. Failures in this regime are expected and should be
pre-empted by scheduled replacement.

## Sudden uncorrectable errors
A spike in uncorrectable ECC errors or pending sectors indicates the drive can no
longer reliably store data and should be evacuated immediately.

## Correlated fleet failures
Drives from the same model, batch, and firmware can fail together. If several
drives of one model begin showing signatures simultaneously, treat the whole
cohort as at-risk.
