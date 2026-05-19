"""
DevOps platform API client.
All endpoints verified against test_interface.yaml.
"""

import base64
import logging
import httpx
from Crypto.Cipher import DES

logger = logging.getLogger(__name__)

# DES encryption for login password
_DES_KEY = b"jly_auth"  # 8 bytes key


def _des_encrypt(text: str) -> str:
    """Encrypt password with DES-ECB + PKCS5 + base64."""
    cipher = DES.new(_DES_KEY, DES.MODE_ECB)
    data = text.encode("utf-8")
    # PKCS5 padding
    pad_len = 8 - (len(data) % 8)
    data = data + bytes([pad_len]) * pad_len
    encrypted = cipher.encrypt(data)
    return base64.b64encode(encrypted).decode("utf-8")


class DevOpsClient:
    """Client for interacting with the DevOps test management API."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.token = ""
        self.user_id = ""
        self.username = ""
        self.headers = {"Content-Type": "application/json", "tenantid": "1"}

    async def _post(self, path: str, data: dict) -> dict:
        url = f"{self.base_url}{path}"
        headers = {**self.headers}
        if self.token:
            headers["authorization"] = self.token  # no Bearer prefix
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=data, headers=headers)
            resp.raise_for_status()
            return resp.json()

    # --- Auth ---

    async def login(self, username: str, password: str) -> str:
        """Login with DES-encrypted password. Stores token + userId."""
        encrypted_pwd = _des_encrypt(password)
        resp = await self._post("/api/auth/public/login", {
            "username": username,
            "password": encrypted_pwd,
            "provider": "DEVOPS",
            "validFlag": True,
        })
        data = resp.get("data", {})
        self.token = data.get("token", "")
        auth_user = data.get("authUser", {})
        self.user_id = auth_user.get("userId", "")
        self.username = auth_user.get("username", "")
        return self.token

    # --- Product ---

    async def find_product_id(self, product_name: str) -> str | None:
        resp = await self._post("/api/scrum/product/productTreeList", {
            "obj": {"status": "PROGRESS", "myCollectFlag": 0},
            "page": {"pageSize": 100, "pageNo": 1},
        })
        items = resp.get("data", {}).get("items", []) or resp.get("data", [])
        for item in items:
            if item.get("name") == product_name:
                return item.get("id")
        return None

    # --- Test Group ---

    async def create_group(self, biz_id: str, name: str, group_type: str, parent_id: str = "") -> dict:
        data = {
            "acceptformValues": {"name": name},
            "bizId": biz_id,
            "bizType": "product",
            "name": name,
            "type": group_type,
        }
        if parent_id:
            data["parentId"] = parent_id
            data["acceptformValues"]["parentId"] = parent_id
        return await self._post("/api/test/group/createTestGroup", data)

    async def query_group_tree(self, biz_id: str, group_type: str) -> list:
        data = {"bizId": biz_id, "bizType": "product", "needIssue": False, "type": group_type}
        if group_type == "testCase":
            data["testUsedPlace"] = "case"
        result = await self._post("/api/test/group/queryTestGroupTree", data)
        return result.get("data", [])

    async def find_group_id(self, biz_id: str, name: str, group_type: str) -> str | None:
        groups = await self.query_group_tree(biz_id, group_type)
        for g in groups:
            if g.get("title") == name:
                return g.get("id")
            for child in g.get("children", []):
                if child.get("title") == name:
                    return child.get("id")
        return None

    # --- Test Story ---

    async def create_story(self, biz_id: str, title: str, description: str = "",
                           group_id: str = "", principal_id: str = "",
                           priority: int = 3, edition_id: str = "") -> dict:
        data = {
            "bizId": biz_id, "bizType": "product",
            "title": title, "description": description or f"<p>{title}</p>",
            "priority": priority,
        }
        if group_id: data["groupId"] = group_id
        if principal_id: data["principalId"] = principal_id
        if edition_id: data["editionId"] = edition_id
        return await self._post("/api/test/story/createTestStory", data)

    # --- Test Case ---

    async def create_case(self, biz_id: str, title: str, steps: list,
                          importance: str = "L1", test_group_id: str = "",
                          maintenance: str = "", case_type: str = "manual") -> dict:
        data = {
            "bizId": biz_id, "bizType": "product",
            "title": title, "importance": importance,
            "type": case_type, "steps": steps,
        }
        if test_group_id: data["testGroupId"] = test_group_id
        if maintenance: data["maintenance"] = maintenance
        return await self._post("/api/test/case/createTestCase", data)

    # --- Bind case to requirement ---

    async def bind_case_to_issue(self, issue_id: str, test_case_ids: list) -> dict:
        return await self._post("/api/test/case/bindTestCaseAndIssue", {
            "issueId": [issue_id], "testCaseIds": test_case_ids,
        })

    # --- Test Plan ---

    async def create_plan(self, biz_id: str, title: str, principal_id: str = "",
                          sprint_id: str = "", edition_id: str = "",
                          start_date: str = "", end_date: str = "") -> dict:
        data = {"bizId": biz_id, "bizType": "product", "title": title}
        if principal_id: data["principalId"] = principal_id
        if sprint_id: data["sprintId"] = sprint_id
        if edition_id: data["editionId"] = edition_id
        if start_date: data["startDate"] = start_date
        if end_date: data["endDate"] = end_date
        return await self._post("/api/test/bizplan/createBizPlan", data)

    # --- Add cases to plan ---

    async def set_cases_to_plan(self, plan_id: str, case_ids: list) -> dict:
        return await self._post("/api/test/bizplan/setTestCaseOfPlan", {
            "testBizPlanId": plan_id, "testCaseIds": case_ids,
        })

    # --- Test Task ---

    async def create_task(self, plan_id: str, name: str, case_ids: list,
                          case_execute_method: str = "manual") -> dict:
        return await self._post("/api/test/bizplan/executeTestCaseAddTask", {
            "testBizPlanId": plan_id, "name": name,
            "caseExecuteMethod": case_execute_method,
            "executeAllCase": False, "testCaseIds": case_ids,
        })


# --- Full push workflow ---

async def push_plan_to_devops(
    client: DevOpsClient,
    product_name: str,
    plan_title: str = "测试计划",
    requirements: list = None,
    progress_callback=None,
) -> dict:
    requirements = requirements or []
    total_steps = 8
    result = {"stories": [], "cases": [], "plan_id": "", "task_id": ""}

    def step_msg(step, msg):
        if progress_callback:
            progress_callback(step, total_steps, msg)

    # 1. Resolve product
    step_msg(1, f"查找产品「{product_name}」...")
    biz_id = await client.find_product_id(product_name)
    if not biz_id:
        raise ValueError(f"未找到产品「{product_name}」")
    result["biz_id"] = biz_id

    principal_id = client.user_id if client.user_id else "1"

    # 2. Create requirement groups + stories
    step_msg(2, "创建需求分组...")
    req_groups = {}
    for req in requirements:
        gname = req.get("group") or "默认分组"
        if gname not in req_groups:
            gid = await client.find_group_id(biz_id, gname, "testStory")
            if not gid:
                gid = (await client.create_group(biz_id, gname, "testStory")).get("data")
            req_groups[gname] = gid

    step_msg(3, f"创建测试需求 (共 {len(requirements)} 个)...")
    story_ids = []
    for req in requirements:
        gname = req.get("group") or "默认分组"
        desc = req.get("description") or f"<p>{req.get('name', '')}</p>"
        resp = await client.create_story(
            biz_id=biz_id, title=req.get("name", "未命名需求"),
            description=desc, group_id=req_groups.get(gname, ""),
            principal_id=principal_id, priority=3,
        )
        sid = resp.get("data")
        if sid:
            story_ids.append(sid)
            result["stories"].append({"name": req.get("name"), "id": sid})

    # 3. Create case groups
    step_msg(4, "创建用例分组...")
    case_groups = {}
    for req in requirements:
        gname = req.get("group") or "默认分组"
        if gname not in case_groups:
            gid = await client.find_group_id(biz_id, gname, "testCase")
            if not gid:
                gid = (await client.create_group(biz_id, gname, "testCase")).get("data")
            case_groups[gname] = gid

    # 4. Create test cases
    step_msg(5, "创建测试用例...")
    all_case_ids = []
    case_story_map = []
    for i, req in enumerate(requirements):
        story_id = story_ids[i] if i < len(story_ids) else ""
        gname = req.get("group") or "默认分组"
        case_group_id = case_groups.get(gname, "")
        req_case_ids = []
        for tc in req.get("testCases", []):
            steps = [{"description": s.get("step", ""), "expectResult": s.get("expected", "")}
                     for s in tc.get("steps", [])]
            if not steps:
                steps = [{"description": tc.get("title", ""), "expectResult": "验证通过"}]
            imp = "L0" if tc.get("priority") == "L0" else "L1"
            cid = (await client.create_case(
                biz_id=biz_id, title=tc.get("title", "未命名用例"),
                steps=steps, importance=imp, test_group_id=case_group_id,
                maintenance=principal_id,
            )).get("data")
            if cid:
                all_case_ids.append(cid)
                req_case_ids.append(cid)
                result["cases"].append({"title": tc.get("title"), "id": cid})
        if story_id and req_case_ids:
            case_story_map.append({"story_id": story_id, "case_ids": req_case_ids})

    # 5. Bind
    step_msg(6, f"关联用例到需求 (共 {len(case_story_map)} 组)...")
    for m in case_story_map:
        await client.bind_case_to_issue(m["story_id"], m["case_ids"])

    # 6. Create plan
    step_msg(7, "创建测试计划...")
    plan_id = (await client.create_plan(biz_id=biz_id, title=plan_title, principal_id=principal_id)).get("data")
    result["plan_id"] = plan_id

    # 7. Add cases to plan
    if plan_id and all_case_ids:
        step_msg(7, f"添加用例到计划 (共 {len(all_case_ids)} 条)...")
        await client.set_cases_to_plan(plan_id, all_case_ids)

    # 8. Create task
    step_msg(8, "创建测试任务...")
    if plan_id and all_case_ids:
        tid = (await client.create_task(plan_id=plan_id, name=f"{plan_title} - 测试任务",
                                         case_ids=all_case_ids)).get("data")
        result["task_id"] = tid

    return result
