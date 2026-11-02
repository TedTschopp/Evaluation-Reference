# Instructor guide

Allow about 20 minutes. Start in replay with **Candidate** selected. No model setup is needed.

## Define the job · 3 minutes

Open the December 1791 ratification case. Have learners state the intended work before opening its criteria.

The candidate says twelve. Its cited twelfth article exists in the authentic 1789 proposal. The weak checker passes, but the question concerned ten ratifications in 1791.

Switch to the proposal case. Twelve is appropriate there. The evaluation must preserve the requested event and scope.

## Follow the evidence · 4 minutes

Inspect Senate selection in 1789 and 1914. Expand the action trace and open the cited passage. Compare original Article I, Section 3 with the Seventeenth Amendment.

Explore Prohibition and taxing powers. Authenticity, relevance, authority, clause, and date are distinct considerations.

The evidence desk separates primary text and archival notes. Its trace shows what the agent received and did; it does not expose private internal reasoning.

## Change the boundary · 3 minutes

Use the Declaration-only case. Historical knowledge from memory does not satisfy the instruction to establish the answer from that supplied document.

Restore the Constitution. The assistant should now answer directly. Compare the ambiguous referent with the fully specified Bill of Rights question. Necessary clarification and unnecessary clarification are different behaviors.

Both tools enforce the evidence restriction.

## Test the grader · 3 minutes

Select a correct paraphrase, wrong-era answer, and correct answer with an unretrieved citation in the calibration table.

The local checks match eight source-checked labels. Their finite concepts and approved source references can still miss other semantic errors; the small calibration set does not establish general accuracy.

A live AI judge is separately calibrated on those responses. A mismatch or error leaves required AI assessments unresolved. Agent failure and grader failure are reported separately.

## Compare versions · 3 minutes

Baseline passes 8/12; candidate passes 11/12, with one critical failure. Revised passes the twelve reference behaviors.

These are authored decision examples, not a model benchmark. Replay has no invented timing or cost. Live results can vary, and only available measured latency/token counts are shown.

## Decide what can ship · 4 minutes

Default policy requires zero critical failures, a complete suite, and at least 90% case passes.

Lower only the percentage threshold: the candidate's critical error still blocks release. Then explicitly weaken the critical-failure rule. A changed decision here reflects a changed policy, not an improved agent.

Known critical failures remain visible if a judge also fails. A partial live run cannot complete the release suite.

Finish by examining retrieval, source boundaries, instructions, and criteria. Change the product deliberately, then rerun failures and successful controls. Evaluation itself did not train or repair the agent.

## Optional developer extension

Configure a model endpoint, test its tool support, and run one case. Inspect actual tool parameters, returned passages, and graders. Export the RunBundle and import it into the other implementation.

Try three repetitions to see variation. Configure an independent judge and inspect its calibration. Record model, prompt, corpus, grader, and policy versions.

Passing this teaching suite is bounded evidence, not UAT, stakeholder approval, or production certification.

