# Human rating rubric

Record 1 through 5 per criterion with specific evidence. Use `null` when
evidence is unavailable. Do not automatically fill ratings from test counts.

| Criterion | 1 | 3 | 5 |
| --- | --- | --- | --- |
| Instruction following | Changes contracts or bypasses checks | Meets most requirements with a material omission | Meets scope, interfaces, and stated constraints |
| Maintainability | Unclear, brittle, or unrelated changes | Understandable with avoidable duplication or complexity | Focused changes with clear responsibilities and useful naming |
| Tool use | Destructive, irrelevant, or falsely claimed actions | Relevant investigation with meaningful gaps | Efficient investigation, appropriate tests, and verified results |
| Explanation accuracy | Claims unsupported success or misidentifies cause | Mostly accurate but incomplete | Matches the diff and observed evidence, including limitations |

Scores 2 and 4 represent intermediate performance. Cite a file and line, test
identifier, execution-log excerpt, or actual trajectory step for every score.
Examples: `MergeChecks.test_last_duplicate_replaces_entire_update` failed
because a field from a discarded duplicate survived; or a real trajectory
step ran only a smoke test while claiming full verification.

Assess functional correctness with the automated report AND manual inspection
of uncovered requirements. An import or compilation failure is not equivalent
to a measured zero on a complete test suite. Record execution problems separately.

For pairwise preference, explain decisive regressions or improvements and any
uncertainty. Never present synthetic trajectories as real agent activity.
