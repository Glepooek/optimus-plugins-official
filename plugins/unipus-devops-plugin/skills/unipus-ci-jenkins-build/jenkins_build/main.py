"""
Jenkins Build CLI
用法：
  python main.py                        # 触发默认 job（config.yaml 第一个）
  python main.py zk-api                 # 触发指定 job
  python main.py zk-api BRANCH=main     # 触发带参数的 job
"""

import sys
import yaml
from jenkins_build import JenkinsBuildSkill


def load_config(path: str = "config.yaml") -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_args(args: list[str]) -> tuple[str | None, dict]:
    """解析命令行参数，返回 (job_name, params)"""
    job_name = None
    params = {}
    for arg in args:
        if "=" in arg:
            k, v = arg.split("=", 1)
            params[k] = v
        elif job_name is None:
            job_name = arg
    return job_name, params


def main():
    config = load_config()
    jenkins_cfg = config["jenkins"]
    jobs = config.get("jobs", {})

    skill = JenkinsBuildSkill(
        jenkins_url=jenkins_cfg["url"],
        username=jenkins_cfg["username"],
        api_token=jenkins_cfg.get("api_token"),
        password=jenkins_cfg.get("password"),
    )

    job_name, params = parse_args(sys.argv[1:])

    # 未指定 job 时使用配置文件第一个
    if job_name is None:
        job_name = next(iter(jobs))

    if job_name not in jobs:
        print(f"[✗] 未找到 job '{job_name}'，可用 job：{list(jobs.keys())}")
        sys.exit(1)

    job_path = jobs[job_name]["path"]
    print(f"[→] 触发 job: {job_name}  path: {job_path}")
    if params:
        print(f"    参数: {params}")

    result, commits = skill.run(job_path, params=params or None)
    sys.exit(0 if result == "SUCCESS" else 1)


if __name__ == "__main__":
    main()
