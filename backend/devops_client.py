"""
DevOps platform API client.
Wraps all test management API calls for pushing test plans, requirements, and cases.

Configuration: platform URL + username + password
Login flow: POST login → get token
Product resolution: query product by name → get bizId
"""

import logging
import httpx

logger = logging.getLogger(__name__)


class DevOpsClient:
    """Client for interacting with the DevOps test management API."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.token = ""
        self.headers = {"Content-Type": "application/json"}

    async def _post(self, path: str, data: dict) -> dict:
        url = f"{self.base_url}{path}"
        headers = {**self.headers}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=data, headers=headers)
            resp.raise_for_status()
            return resp.json()

    async def _get(self, path: str, params: dict = None) -> dict:
        url = f"{self.base_url}{path}"
        headers = {**self.headers}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            return resp.json()

    # --- Auth ---

    async def login(self, username: str, password: str) -> str:
        """Login and store token. Returns the token."""
        resp = await self._post("/api/auth/public/login", {
            "username": username,
            "password": password,
            "provider": "DEVOPS",
            "validFlag": True,
        })
        token = resp.get("data", {}).get("token", "")
        self.token = token
        return token

    # --- Product (resolve bizId by name) ---

    async def find_product_id(self, product_name: str) -> str | None:
        """Find product bizId by product name via productTreeList API."""
        resp = await self._post("/api/scrum/product/productTreeList", {
            "obj": {"status": "PROGRESS", "myCollectFlag": 0},
            "page": {"pageSize": 100, "pageNo": 1},
        })
        items = resp.get("data", {}).get("items", []) or resp.get("data", [])
        for item in items:
            if item.get("name") == product_name:
                return item.get("id")
        return None

    # --- Edition / Sprint (resolve by name) ---

    async def find_edition_id(self, biz_id: str, edition_name: str = "") -> str | None:
        """Find edition/version ID. If no name given, return the latest."""
        try:
            resp = await self._post("/api/edition/getEditionList", {
                "obj": {"bizId": biz_id, "bizType": "product"},
                "page": {"pageNo": 1, "pageSize": 50},
            })
            items = resp.get("data", {}).get("items", []) or resp.get("data", [])
            if not edition_name:
                return items[0].get("id") if items else None
            for item in items:
                if item.get("name") == edition_name or item.get("title") == edition_name:
                    return item.get("id") or item.get("ID")
        except Exception:
            pass
        return None

    async def find_sprint_id(self, biz_id: str, sprint_name: str = "") -> str | None:
        """Find sprint ID by name."""
        try:
            resp = await self._post("/api/sprint/getSprintList", {
                "obj": {"bizId": biz_id, "bizType": "product"},
                "page": {"pageNo": 1, "pageSize": 50},
            })
            items = resp.get("data", {}).get("items", []) or resp.get("data", [])
            if not sprint_name:
                return items[0].get("id") if items else None
            for item in items:
                name = item.get("name") or item.get("title") or ""
                if sprint_name.lower() in name.lower() or name.lower() in sprint_name.lower():
                    return item.get("id") or item.get("ID")
        except Exception:
            pass
        return None

    # --- User (resolve principalId) ---

    async def find_user_id(self, username: str = "") -> str | None:
        """Find user ID by username. If empty, return the current logged-in user."""
        try:
            resp = await self._post("/api/user/getUserInfo", {})
            user = resp.get("data", {})
            return user.get("id") or user.get("ID") or user.get("userId")
        except Exception:
            pass
        return None

    # --- Test Group ---

    async def create_group(self, biz_id: str, name: str, type: str, parent_id: str = "") -> dict:
        """Create a test group (testStory or testCase type)."""
        data = {
            "bizId": biz_id,
            "bizType": "product",
            "name": name,
            "type": type,
            "acceptformValues": {"name": name},
        }
        if parent_id:
            data["parentId"] = parent_id
            data["acceptformValues"]["parentId"] = parent_id
        return await self._post("/api/test/group/createTestGroup", data)

    async def query_group_tree(self, biz_id: str, type: str, test_used_place: str = "") -> list:
        """Query test group tree, return data list."""
        data = {
            "bizId": biz_id,
            "bizType": "product",
            "needIssue": False,
            "type": type,
        }
        if test_used_place:
            data["testUsedPlace"] = test_used_place
        result = await self._post("/api/test/group/queryTestGroupTree", data)
        return result.get("data", [])

    async def find_group_id(self, biz_id: str, name: str, type: str, parent_title: str = "") -> str | None:
        """Find a group ID by name in the group tree."""
        groups = await self.query_group_tree(biz_id, type, "case" if type == "testCase" else "")
        for g in groups:
            if g.get("title") == name:
                return g.get("id")
            for child in g.get("children", []):
                if child.get("title") == name:
                    return child.get("id")
        return None

    # --- Test Story (Requirements) ---

    async def create_story(self, biz_id: str, title: str, description: str = "",
                           group_id: str = "", principal_id: str = "",
                           priority: int = 3, edition_id: str = "") -> dict:
        """Create a test requirement story."""
        data = {
            "bizId": biz_id,
            "bizType": "product",
            "title": title,
            "description": description or f"<p>{title}</p>",
            "priority": priority,
        }
        if group_id:
            data["groupId"] = group_id
        if principal_id:
            data["principalId"] = principal_id
        if edition_id:
            data["editionId"] = edition_id
        return await self._post("/api/test/story/createTestStory", data)

    # --- Test Case ---

    async def create_case(self, biz_id: str, title: str, steps: list,
                          importance: str = "L1", test_group_id: str = "",
                          maintenance: str = "", preconditions: str = "",
                          case_type: str = "manual") -> dict:
        """Create a test case with steps."""
        data = {
            "bizId": biz_id,
            "bizType": "product",
            "title": title,
            "importance": importance,
            "type": case_type,
            "steps": steps,
        }
        if test_group_id:
            data["testGroupId"] = test_group_id
        if maintenance:
            data["maintenance"] = maintenance
        if preconditions:
            data["preconditions"] = preconditions
        return await self._post("/api/test/case/createTestCase", data)

    # --- Bind case to requirement ---

    async def bind_case_to_issue(self, issue_id: str, test_case_ids: list) -> dict:
        """Bind test cases to a requirement (issue)."""
        data = {
            "issueId": [issue_id],
            "testCaseIds": test_case_ids,
        }
        return await self._post("/api/test/case/bindTestCaseAndIssue", data)

    # --- Test Plan ---

    async def create_plan(self, biz_id: str, title: str, principal_id: str = "",
                          sprint_id: str = "", edition_id: str = "",
                          start_date: str = "", end_date: str = "") -> dict:
        """Create a test plan."""
        data = {
            "bizId": biz_id,
            "bizType": "product",
            "title": title,
        }
        if principal_id:
            data["principalId"] = principal_id
        if sprint_id:
            data["sprintId"] = sprint_id
        if edition_id:
            data["editionId"] = edition_id
        if start_date:
            data["startDate"] = start_date
        if end_date:
            data["endDate"] = end_date
        return await self._post("/api/test/bizplan/createBizPlan", data)

    # --- Add cases to plan ---

    async def set_cases_to_plan(self, plan_id: str, case_ids: list) -> dict:
        """Add test cases to a test plan."""
        data = {
            "testBizPlanId": plan_id,
            "testCaseIds": case_ids,
            "addRelationTestStory": True,
        }
        return await self._post("/api/test/bizplan/setTestCaseOfPlan", data)

    # --- Test Task ---

    async def create_task(self, plan_id: str, name: str, case_ids: list,
                          case_execute_method: str = "manual") -> dict:
        """Create a test task under a plan."""
        data = {
            "testBizPlanId": plan_id,
            "name": name,
            "caseExecuteMethod": case_execute_method,
            "executeAllCase": False,
            "testCaseIds": case_ids,
        }
        return await self._post("/api/test/bizplan/executeTestCaseAddTask", data)


# --- Full push workflow ---

async def push_plan_to_devops(
    client: DevOpsClient,
    product_name: str,
    plan_title: str = "测试计划",
    requirements: list = None,
    progress_callback=None,
) -> dict:
    """
    Full workflow: push a local test plan to DevOps.

    Steps:
    0. Resolve bizId by product name
    0.1 Resolve principalId (current user)
    1. Create/find requirement groups (by requirement.group or "默认分组")
    2. Create test stories (one per requirement)
    3. Create/find case groups (by requirement.group or "默认分组")
    4. Create test cases (all cases under each requirement)
    5. Bind cases to stories
    6. Create test plan
    7. Add cases to plan
    8. Create test task
    """
    requirements = requirements or []
    total_steps = 10
    result = {"stories": [], "cases": [], "plan_id": "", "task_id": ""}

    def step_msg(step, msg):
        if progress_callback:
            return progress_callback(step, total_steps, msg)

    # Step 0: Resolve product ID
    step_msg(1, f"查找产品「{product_name}」...")
    biz_id = await client.find_product_id(product_name)
    if not biz_id:
        raise ValueError(f"未找到产品「{product_name}」，请确认产品名称是否正确")
    result["biz_id"] = biz_id

    # Step 0.1: Resolve current user as principal
    step_msg(2, "获取用户信息...")
    principal_id = await client.find_user_id()

    # Step 1: Create requirement groups
    step_msg(3, "创建需求分组...")
    req_groups = {}
    for req in requirements:
        group_name = req.get("group") or "默认分组"
        if group_name not in req_groups:
            gid = await client.find_group_id(biz_id, group_name, "testStory")
            if not gid:
                resp = await client.create_group(biz_id, group_name, "testStory")
                gid = resp.get("data")
            req_groups[group_name] = gid

    # Step 2: Create test stories
    step_msg(4, f"创建测试需求 (共 {len(requirements)} 个)...")
    story_ids = []
    for req in requirements:
        group_name = req.get("group") or "默认分组"
        group_id = req_groups.get(group_name, "")
        description = req.get("description") or f"<p>{req.get('name', '')}</p>"
        resp = await client.create_story(
            biz_id=biz_id,
            title=req.get("name", "未命名需求"),
            description=description,
            group_id=group_id,
            principal_id=principal_id,
            priority=3,
        )
        story_id = resp.get("data")
        if story_id:
            story_ids.append(story_id)
            result["stories"].append({"name": req.get("name"), "id": story_id})

    # Step 3: Create case groups
    step_msg(5, "创建用例分组...")
    case_groups = {}
    for req in requirements:
        group_name = req.get("group") or "默认分组"
        if group_name not in case_groups:
            gid = await client.find_group_id(biz_id, group_name, "testCase")
            if not gid:
                resp = await client.create_group(biz_id, group_name, "testCase")
                gid = resp.get("data")
            case_groups[group_name] = gid

    # Step 4: Create test cases
    step_msg(6, f"创建测试用例...")
    all_case_ids = []
    case_story_map = []
    for i, req in enumerate(requirements):
        story_id = story_ids[i] if i < len(story_ids) else ""
        group_name = req.get("group") or "默认分组"
        case_group_id = case_groups.get(group_name, "")
        cases = req.get("testCases", [])
        req_case_ids = []

        for tc in cases:
            steps = []
            for s in tc.get("steps", []):
                steps.append({
                    "description": s.get("step", ""),
                    "expectResult": s.get("expected", ""),
                })
            if not steps:
                steps = [{"description": tc.get("title", ""), "expectResult": "验证通过"}]

            importance = "L0" if tc.get("priority") == "L0" else "L1"
            resp = await client.create_case(
                biz_id=biz_id,
                title=tc.get("title", "未命名用例"),
                steps=steps,
                importance=importance,
                test_group_id=case_group_id,
                maintenance=principal_id,
                preconditions=tc.get("precondition", ""),
            )
            case_id = resp.get("data")
            if case_id:
                all_case_ids.append(case_id)
                req_case_ids.append(case_id)
                result["cases"].append({"title": tc.get("title"), "id": case_id})

        if story_id and req_case_ids:
            case_story_map.append({"story_id": story_id, "case_ids": req_case_ids})

    # Step 5: Bind cases to stories
    step_msg(7, f"关联用例到需求 (共 {len(case_story_map)} 组)...")
    for mapping in case_story_map:
        await client.bind_case_to_issue(mapping["story_id"], mapping["case_ids"])

    # Step 6: Create test plan
    step_msg(8, "创建测试计划...")
    plan_resp = await client.create_plan(
        biz_id=biz_id,
        title=plan_title,
        principal_id=principal_id,
    )
    plan_id = plan_resp.get("data")
    result["plan_id"] = plan_id

    # Step 7: Add cases to plan
    step_msg(9, f"添加用例到计划 (共 {len(all_case_ids)} 条)...")
    if plan_id and all_case_ids:
        await client.set_cases_to_plan(plan_id, all_case_ids)

    # Step 8: Create test task
    step_msg(10, "创建测试任务...")
    if plan_id and all_case_ids:
        task_resp = await client.create_task(
            plan_id=plan_id,
            name=f"{plan_title} - 测试任务",
            case_ids=all_case_ids,
            case_execute_method="manual",
        )
        result["task_id"] = task_resp.get("data")

    return result
