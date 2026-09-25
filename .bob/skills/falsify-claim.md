Skill name: falsify-claim

Purpose:
Given ONE claim (from extract-claims) and the PR's changed code, write and
RUN an adversarial test that tries to prove the claim false. Report the
real result — never assume or guess what a test would do.

Instructions:
1. Read the claim and the relevant changed code (not the whole repo —
   just the files/functions the claim is about).
2. Think of the most likely way this claim could be violated. Favor edge
   cases: boundary values, zero, negative numbers, empty inputs, combined
   inputs that interact (e.g. two discounts stacking), ordering effects.
3. Write ONE small pytest test that encodes that edge case as an assertion
   matching what the claim promises.
4. Actually run the test. Do not skip this step or predict the outcome.
5. Report exactly one of:
   - FALSIFIED: the test failed, meaning the claim is false. Include the
     actual failing output (input values, expected vs. actual).
   - HELD: the test passed. State clearly this does not prove the claim is
     true in general — only that this one test didn't find a
     counterexample.
6. Do not modify the PR's source code. You are only allowed to write test
   code, and only for the purpose of checking the claim.

Output format: one JSON object —
{"claim_id": "...", "verdict": "FALSIFIED|HELD", "test_code": "...",
 "result": "..."}
