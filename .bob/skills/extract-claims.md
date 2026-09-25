Skill name: extract-claims

Purpose:
Given a PR's diff and its linked issue/spec, produce a list of concrete,
falsifiable behavior claims the PR makes. A claim is falsifiable if a single
test could prove it true or false — not a vague statement like "handles
coupons correctly."

Instructions:
1. Read the diff. Read the linked issue or spec if one is referenced (e.g.
   "closes #42" -> read docs/ISSUE-42.md or the linked issue).
2. From the issue's stated requirements AND the diff's actual behavior,
   write one claim per requirement, each as a single testable sentence.
   Example: "The order total never goes below 0.00, even when combined
   coupon discounts exceed the subtotal."
3. Also write one claim for any requirement the issue states but the diff
   does NOT appear to implement, if you can spot one — flag it separately
   as "possibly unimplemented" rather than dropping it silently.
4. Do not write claims about code style, naming, or anything untestable.
   Every claim must be checkable by running one test against the code.
5. Output ONLY a JSON array, one object per claim:
   {"id": "claim-1", "text": "...", "source": "ISSUE-42 requirement 3"}

Do not attempt to write or run tests in this skill. That is a separate step.
