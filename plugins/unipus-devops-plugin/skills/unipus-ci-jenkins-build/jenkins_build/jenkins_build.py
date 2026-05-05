"""
Jenkins Build Skill
通用的 Jenkins 远程构建工具，支持触发构建、等待构建启动、轮询构建结果。
"""

import time
import requests
from requests.auth import HTTPBasicAuth


class JenkinsBuildSkill:
    def __init__(self, jenkins_url: str, username: str, api_token: str = None, password: str = None):
        """
        :param jenkins_url: Jenkins 地址
        :param username: 用户名
        :param api_token: API Token（优先使用）
        :param password: 密码（api_token 为空时使用）
        """
        self.jenkins_url = jenkins_url.rstrip("/")
        self.session = requests.Session()
        credential = api_token or password
        if not credential:
            raise ValueError("api_token 或 password 必须提供其中一个")
        self.session.auth = HTTPBasicAuth(username, credential)

    def _get_crumb(self) -> dict:
        """获取 Jenkins CSRF crumb"""
        resp = self.session.get(f"{self.jenkins_url}/crumbIssuer/api/json")
        if resp.status_code == 200:
            data = resp.json()
            return {data["crumbRequestField"]: data["crumb"]}
        return {}

    def get_last_build_number(self, job_path: str) -> int:
        """获取 job 当前最新构建号"""
        url = f"{self.jenkins_url}/{job_path}/lastBuild/api/json"
        resp = self.session.get(url)
        return resp.json().get("number", 0) if resp.status_code == 200 else 0

    def trigger(self, job_path: str, params: dict = None) -> int | None:
        """
        触发构建，返回触发前的最新构建号（用于后续检测新构建）
        :param job_path: job 路径，如 "job/MyProject" 或 "view/xxx/job/yyy"
        :param params: 构建参数字典，无参数传 None
        """
        last_number = self.get_last_build_number(job_path)
        crumb = self._get_crumb()

        if params:
            url = f"{self.jenkins_url}/{job_path}/buildWithParameters"
        else:
            url = f"{self.jenkins_url}/{job_path}/build?delay=0sec"

        resp = self.session.post(url, headers=crumb, params=params)
        if resp.status_code in (200, 201):
            print(f"[✓] 构建触发成功（状态码：{resp.status_code}）")
            return last_number
        else:
            print(f"[✗] 构建触发失败，状态码：{resp.status_code}")
            print(f"    响应：{resp.text[:200]}")
            return None

    def wait_for_new_build(self, job_path: str, last_number: int, timeout: int = 30) -> int | None:
        """等待新构建出现，返回新构建号"""
        print("[~] 等待构建启动", end="", flush=True)
        deadline = time.time() + timeout
        while time.time() < deadline:
            resp = self.session.get(f"{self.jenkins_url}/{job_path}/lastBuild/api/json")
            if resp.status_code == 200:
                number = resp.json().get("number", 0)
                if number > last_number:
                    print(f" → 构建 #{number} 已启动")
                    return number
            print(".", end="", flush=True)
            time.sleep(3)
        print(" [超时]")
        return None

    def poll_status(self, job_path: str, build_number: int, interval: int = 10) -> tuple[str | None, list[str]]:
        """
        轮询构建状态直到完成。
        :return: (result, commit_messages) — result 为 SUCCESS/FAILURE/ABORTED 等，
                 commit_messages 为本次构建的 commit message 列表
        """
        print(f"[~] 轮询构建 #{build_number} 状态...")
        while True:
            resp = self.session.get(
                f"{self.jenkins_url}/{job_path}/{build_number}/api/json"
            )
            if resp.status_code != 200:
                print(f"[✗] 查询失败，状态码：{resp.status_code}")
                return None, []

            info = resp.json()
            if not info.get("building", False):
                result = info.get("result")
                duration = info.get("duration", 0) // 1000
                icon = "✓" if result == "SUCCESS" else "✗"
                print(f"[{icon}] 构建完成 | 结果：{result} | 耗时：{duration}s")
                commit_messages = [
                    item.get("msg") or item.get("comment", "")
                    for item in info.get("changeSet", {}).get("items", [])
                    if item.get("msg") or item.get("comment")
                ]
                return result, commit_messages

            duration = info.get("duration", 0) // 1000
            estimated = info.get("estimatedDuration", 0) // 1000
            print(f"    构建中... 已耗时 {duration}s / 预计 {estimated}s")
            time.sleep(interval)

    def run(self, job_path: str, params: dict = None, wait_timeout: int = 30, poll_interval: int = 10) -> tuple[str | None, list[str]]:
        """
        完整执行：触发构建 → 等待启动 → 轮询结果
        :param job_path: job 路径
        :param params: 构建参数
        :param wait_timeout: 等待构建启动的超时秒数
        :param poll_interval: 轮询间隔秒数
        :return: (result, commit_messages)，触发失败返回 (None, [])
        """
        last_number = self.trigger(job_path, params)
        if last_number is None:
            return None, []

        build_number = self.wait_for_new_build(job_path, last_number, timeout=wait_timeout)
        if build_number is None:
            return None, []

        return self.poll_status(job_path, build_number, interval=poll_interval)
