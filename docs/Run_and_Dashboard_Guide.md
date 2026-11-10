# Refined Dashboard Guide

## Pages

1. **Executive Overview:** selected-period KPIs, daily contacts with a seven-day moving average, monthly vault unlocks, and the full-year channel mix.
2. **Demand Analysis:** selected-period contact volume by hour, weekday averages, daily trend with a seven-day moving average, a weekday/hour heatmap, and downloadable activity data.
3. **Channel Economics:** full-year channel contacts, estimated contact costs, average handling time, formatted summary table, and downloadable channel summary.
4. **Staffing Scenarios:** alternative utilization assumptions, estimated agent-hours, modeled labor costs, and downloadable scenario comparison.

## Date filter

The date filter applies to the daily/hourly activity on Executive Overview and Demand Analysis. It does not alter the annual channel economics or staffing scenario summary tables. A single selected date is treated as a one-day period.

The seven-day moving average is calculated across the full daily series before the selected display period is applied. This avoids artificially restarting the rolling window at the first displayed date.

## Cost interpretation

Estimated channel contact costs and estimated staffing labor costs are separate outputs. They are not summed because the project's assumptions do not establish whether the cost components overlap.

## Model limitations

The staffing scenarios are hourly capacity estimates. They are not queueing simulations or employee shift schedules and do not establish service levels, wait times, or abandonment rates. All data and cost assumptions are synthetic.
