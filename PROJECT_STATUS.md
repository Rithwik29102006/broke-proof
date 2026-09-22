# Broke-Proof implementation status

This checklist maps the final specification to the code in this repository.

| Specification item | Status | Implementation |
|---|---|---|
| Broke Date Prediction | ✅ | `backend/app/services/spending.py::projected_broke_date` |
| 60/40 weighted discretionary rate | ✅ | `discretionary_daily_rate` |
| Fixed/recurring spend excluded from burn rate | ✅ | category flags + recurring detector |
| Scheduled future recurring deductions | ✅ | `RecurringExpense` projected in Broke Date loop |
| Safe-to-Spend/Day | ✅ | `safe_to_spend_today` |
| Round-Up Savings Jar | ✅ | per-transaction `jar_contribution` + protected balance |
| Per-purchase overspend nudge | ✅ | transaction commit creates `NudgeHistory` |
| Log anyway / Auto-trim tomorrow | ✅ | controller nudge response endpoint + next-day adjustment |
| No-Spend Weekend | ✅ | user mode + Fri–Sun configured cap |
| Visible Learn stat | ✅ | acceptance %, days gained, adaptive suggestion aggressiveness |
| Subscription detection | ✅ | repeated merchant cadence + amount similarity + fixed categories |
| SMS regex parser | ✅ | multiple amount/date/merchant patterns |
| LLM parser fallback | ✅ optional | provider configured through environment variables |
| SMS batch paste | ✅ | parser API returns multiple previews; UI confirms batch |
| Manual entry | ✅ | quick-add + merchant category memory |
| Screenshot OCR | ✅ | Tesseract + transaction parser |
| OCR/LLM review before commit | ✅ | parse endpoints only return previews; confirm endpoint persists |
| Unified transaction schema | ✅ | all sources create the same `Transaction` model |
| React + Vite + Tailwind | ✅ | responsive frontend |
| Recharts | ✅ | category-spend chart |
| FastAPI + SQLAlchemy | ✅ | backend/API layer |
| MySQL | ✅ | production Docker Compose config |
| Local zero-setup database | ✅ extra | SQLite fallback for dev/tests |
| JWT + refresh tokens | ✅ | auth module |
| Password hashing | ✅ | PBKDF2-SHA256 |
| Input validation | ✅ | Pydantic + fixed-precision decimals |
| PWA basics | ✅ | manifest + service worker |
| Daily recompute job | ✅ | cron-friendly maintenance script |
| Tests | ✅ | parser, jar math, auth/transaction/dashboard integration |
| Account Aggregator linking | ⏭ deferred | deliberately excluded by final specification |
| Full ML model | ⏭ deferred | deliberately excluded by final specification |
| Additional vibe budgets | ⏭ deferred | future scope |
| Group expenses | ⏭ deferred | future scope |
| Gamified streaks | ⏭ deferred | future scope |

## Verification performed in the build environment

- Backend test suite: **4/4 tests passing**.
- JSX/JavaScript source syntax checked with the available TypeScript parser.
- Tesseract OCR manually exercised against a generated payment-text image; extraction successfully flowed into the transaction parser. The date OCR had a character-level error in the synthetic sample, which is exactly why the UI requires the specification's review/confirm step.
- A full `npm install`/Vite production build could not be executed in the build sandbox because outbound access to the npm registry was unavailable. The frontend package manifest and source are ready to build in a normal networked development environment.
