# DAX measures

Measures used (or recommended) for the Superstore dashboard. Explicit measures are easier to reuse and audit than dragging raw columns onto visuals.

```dax
Total Sales = SUM ( SampleSuperstore[Sales] )

Total Profit = SUM ( SampleSuperstore[Profit] )

Profit Margin % = DIVIDE ( [Total Profit], [Total Sales] )

Units Sold = SUM ( SampleSuperstore[Quantity] )

Loss-Making Sales =
CALCULATE ( [Total Sales], SampleSuperstore[Profit] < 0 )

Average Discount = AVERAGE ( SampleSuperstore[Discount] )
```

## A card to remove

The first version of the dashboard had a card labelled **Total Revenue** ($2.58M), but it was calculated as Sales + Profit. Profit is part of the money that came in from sales, so adding the two counts it twice, and the result doesn't describe anything real. The **Profit Margin** card was divided by the same figure, so it showed 11.09% instead of 12.5%:

```dax
-- first version (wrong): 286,397 / 2,583,598 = 11.09%
-- corrected:             286,397 / 2,297,201 = 12.47%
```

Use **Total Sales** ($2.30M) and **Total Profit** ($286k) as separate cards, with **Profit Margin %** (12.5%) alongside.

## Suggested additions

- A **Discount band** calculated column, to show margin by discount level:

```dax
Discount Band =
SWITCH (
    TRUE (),
    SampleSuperstore[Discount] = 0, "No discount",
    SampleSuperstore[Discount] <= 0.2, "1-20%",
    SampleSuperstore[Discount] <= 0.4, "21-40%",
    "Over 40%"
)
```

- **Conditional formatting** on profit visuals (red below zero), so loss-making states and sub-categories stand out.
