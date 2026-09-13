这是直接躺在 evals/ 根下的 prompt.md，**不构成一个 case**。

门禁应当仍然判红——判据是「evals/ 下有**子目录**含 case.yaml 或 prompt.md」，
而不是「evals/ 目录非空」，也不是「evals/ 下有 prompt.md」。

这正是本仓 trigger-eval.json 的原形态：文件躺在 evals/ 下，
而 claude plugin eval 按 <eval dir>/**/prompt.md 发现 case，在它上面找到 0 个。
一个只查「evals/ 非空」的门禁会在这里亮绿灯，而 eval 实际跑不出任何 case。

对应单测：.githooks/test_check_new_skill_eval_case.py
  TestHasEvalCase.test_loose_file_directly_under_evals_does_not_count
