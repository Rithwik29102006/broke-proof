# Architecture

```text
Manual entry ─────┐
SMS paste ────────┼─> Transaction Extraction ─> Categorizer ─> Spending Engine ─┬─> Broke Date
Screenshot + OCR ─┘       regex + optional LLM        rules                    ├─> Safe-to-spend
                                                                                ├─> Round-up Jar
                                                                                └─> Recurring detection
                                                                                         │
                                                                                         v
                                                                               AI Controller
                                                                               nudges / weekend
                                                                               accept-reject learn stat
```

The API deliberately computes balance, Safe-to-Spend and Broke Date from source transactions instead of persisting mutable derived totals. This prevents drift when transactions are edited or recurring status changes.

## Broke Date

1. Separate recurring/fixed categories from discretionary transactions.
2. Calculate the 7-day discretionary average and full-cycle discretionary average.
3. Weight them 60/40.
4. Project forward one day at a time from the current spendable balance.
5. Apply known recurring expenses on their predicted due dates.
6. The first projected day with non-positive balance is the Broke Date.

## Round-up Jar

Each confirmed transaction is rounded up to the next ₹10. The difference is recorded as `jar_contribution`. Spendable balance is computed as:

`starting_balance - transaction_spend - protected_jar`

The jar remains visible but is excluded from money available for normal spending.
