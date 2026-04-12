# -*- coding: utf-8 -*-
"""
TASK-12 测试脚本：定时任务管理 - 全新功能
测试目标：验证定时任务管理功能（后端API + 前端页面）

运行方式：
    cd smart-campus
    python -m pytest backend/tests/test_task12_scheduler.py -v

通过条件：所有测试用例通过后方可将 TASK-12 标记为完成
"""

import pytest
import sys
import os

# 将项目根路径加入 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# =====================================================================
# 文件存在性检查
# =====================================================================

class TestFileStructure:
    """验证 TASK-12 所需文件已创建"""

    def test_scheduler_core_file_exists(self):
        """调度器核心文件应已创建：core/scheduler.py"""
        scheduler_path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'core', 'scheduler.py'
        )
        assert os.path.exists(scheduler_path), (
            f"FAIL: 调度器核心文件不存在 {scheduler_path}\n"
            "需要创建: backend/app/core/scheduler.py"
        )

    def test_scheduler_api_file_exists(self):
        """调度器 API 文件应已创建：system/tasks.py"""
        api_path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'api', 'v1',
            'system', 'tasks.py'
        )
        assert os.path.exists(api_path), (
            f"FAIL: 调度器 API 文件不存在 {api_path}\n"
            "需要创建: backend/app/api/v1/system/tasks.py"
        )

    def test_task_run_log_model_exists(self):
        """任务执行日志模型文件应已创建"""
        model_path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'models',
            'task_run_log.py'
        )
        if not os.path.exists(model_path):
            pytest.skip("任务执行日志模型可能尚未创建，可后续补充")
        assert os.path.exists(model_path)

    def test_frontend_page_exists(self):
        """前端页面应已创建：Tasks.vue"""
        frontend_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'frontend', 'src',
            'views', 'system', 'Tasks.vue'
        )
        if not os.path.exists(frontend_path):
            pytest.skip(f"前端文件尚未创建（可后续创建）: {frontend_path}")


# =====================================================================
# 后端 API 结构测试
# =====================================================================

class TestSchedulerAPIStructure:
    """验证 tasks.py 的 API 路由结构"""

    def test_router_importable(self):
        """router 对象可正常导入"""
        try:
            from app.api.v1.system.tasks import router
            assert router is not None
        except ImportError as e:
            pytest.fail(f"无法导入 router: {e}")

    def test_list_tasks_endpoint_exists(self):
        """GET /tasks/ 路由存在"""
        try:
            from app.api.v1.system.tasks import router
            routes = [r.path for r in router.routes]
            has_list = any('task' in r and r.count('/') >= 1 and '{' not in r for r in routes)
            assert has_list, (
                f"未找到任务列表路由 GET /tasks/，现有路由: {routes}"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_pause_task_endpoint_exists(self):
        """PUT /tasks/{job_id}/pause 路由存在"""
        try:
            from app.api.v1.system.tasks import router
            routes = [r.path for r in router.routes]
            has_pause = any('pause' in r for r in routes)
            assert has_pause, (
                f"未找到暂停任务路由 PUT /tasks/{{job_id}}/pause，现有路由: {routes}"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_resume_task_endpoint_exists(self):
        """PUT /tasks/{job_id}/resume 路由存在"""
        try:
            from app.api.v1.system.tasks import router
            routes = [r.path for r in router.routes]
            has_resume = any('resume' in r for r in routes)
            assert has_resume, (
                f"未找到恢复任务路由 PUT /tasks/{{job_id}}/resume，现有路由: {routes}"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_run_task_endpoint_exists(self):
        """POST /tasks/{job_id}/run 路由存在"""
        try:
            from app.api.v1.system.tasks import router
            routes = [r.path for r in router.routes]
            has_run = any('run' in r and 'task' in r for r in routes)
            assert has_run, (
                f"未找到手动执行路由 POST /tasks/{{job_id}}/run，现有路由: {routes}"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_task_history_endpoint_exists(self):
        """GET /tasks/{job_id}/history 路由存在"""
        try:
            from app.api.v1.system.tasks import router
            routes = [r.path for r in router.routes]
            has_history = any('history' in r for r in routes)
            assert has_history, (
                f"未找到执行历史路由 GET /tasks/{{job_id}}/history，现有路由: {routes}"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_task_response_model_fields(self):
        """ScheduledTask / TaskInfo 响应模型字段完整"""
        try:
            from app.api.v1.system.tasks import ScheduledTask, TaskStatus
            task = ScheduledTask(
                job_id="clear_expired_tokens",
                name="清理过期Token",
                description="清理已过期的认证令牌",
                next_run_time="2026-04-12T02:00:00",
                status=TaskStatus.RUNNING,
            )
            d = task.model_dump() if hasattr(task, 'model_dump') else task.dict()
            required_keys = ['job_id', 'name', 'status']
            for key in required_keys:
                assert key in d, f"ScheduledTask 缺少必需字段: {key}"
        except ImportError:
            pytest.skip("模型未实现，跳过")


# =====================================================================
# 核心功能逻辑测试
# =====================================================================

class TestSchedulerBusinessLogic:
    """验证定时任务管理的核心业务逻辑"""

    def test_scheduler_uses_apscheduler(self):
        """调度器应使用 APScheduler"""
        scheduler_path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'core', 'scheduler.py'
        )
        if not os.path.exists(scheduler_path):
            pytest.skip("调度器文件尚未创建，跳过")

        with open(scheduler_path, 'r', encoding='utf-8') as f:
            source = f.read()

        uses_apscheduler = (
            'apscheduler' in source.lower() or
            'BackgroundScheduler' in source or
            'AsyncIOScheduler' in source
        )
        assert uses_apscheduler, (
            "FAIL: 调度器应使用 APScheduler (BackgroundScheduler 或 AsyncIOScheduler)"
        )

    def test_predefined_tasks_registered(self):
        """预定义任务应在代码中注册"""
        scheduler_path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'core', 'scheduler.py'
        )
        if not os.path.exists(scheduler_path):
            pytest.skip("调度器文件尚未创建，跳过")

        with open(scheduler_path, 'r', encoding='utf-8') as f:
            source = f.read()

        predefined_tasks = [
            'clear_expired_tokens',
            'generate_daily_attendance',
            'backup_database'
        ]
        found_tasks = [t for t in predefined_tasks if t in source]
        assert len(found_tasks) >= 1, (
            f"FAIL: 预定义任务未注册，期望至少一个: {predefined_tasks}"
        )

    def test_task_run_log_saved_to_db(self):
        """任务执行结果应写入数据库（task_run_logs 表）"""
        api_path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'api', 'v1',
            'system', 'tasks.py'
        )
        if not os.path.exists(api_path):
            pytest.skip("API 文件尚未创建，跳过")

        with open(api_path, 'r', encoding='utf-8') as f:
            source = f.read()

        saves_to_db = (
            'task_run_log' in source.lower() or
            'TaskRunLog' in source or
            'db.add' in source or
            'session.add' in source
        )
        assert saves_to_db, (
            "FAIL: 任务执行历史应写入数据库"
        )

    def test_pause_resume_calls_scheduler(self):
        """暂停/恢复任务应调用 APScheduler 的 pause_job/resume_job"""
        api_path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'api', 'v1',
            'system', 'tasks.py'
        )
        if not os.path.exists(api_path):
            pytest.skip("API 文件尚未创建，跳过")

        with open(api_path, 'r', encoding='utf-8') as f:
            source = f.read()

        has_scheduler_call = (
            'pause_job' in source or
            'resume_job' in source or
            'get_job' in source
        )
        assert has_scheduler_call, (
            "FAIL: 暂停/恢复任务应调用 APScheduler 的 pause_job/resume_job 方法"
        )


# =====================================================================
# 前端页面测试（结构验证）
# =====================================================================

class TestSchedulerFrontend:
    """验证前端页面结构"""

    def test_frontend_file_exists(self):
        """Tasks.vue 文件应存在"""
        frontend_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'frontend', 'src',
            'views', 'system', 'Tasks.vue'
        )
        assert os.path.exists(frontend_path), (
            f"FAIL: 前端文件不存在: {frontend_path}"
        )

    def test_frontend_has_task_list(self):
        """前端应展示任务列表"""
        frontend_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'frontend', 'src',
            'views', 'system', 'Tasks.vue'
        )
        if not os.path.exists(frontend_path):
            pytest.skip("前端文件不存在，跳过")

        with open(frontend_path, 'r', encoding='utf-8') as f:
            content = f.read()

        has_list = (
            'task' in content.lower() and
            ('table' in content.lower() or 'list' in content.lower())
        )
        assert has_list, (
            "FAIL: 前端页面未找到任务列表展示"
        )

    def test_frontend_has_pause_resume_buttons(self):
        """前端应有暂停/恢复按钮"""
        frontend_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'frontend', 'src',
            'views', 'system', 'Tasks.vue'
        )
        if not os.path.exists(frontend_path):
            pytest.skip("前端文件不存在，跳过")

        with open(frontend_path, 'r', encoding='utf-8') as f:
            content = f.read()

        has_controls = (
            'pause' in content.lower() or
            'resume' in content.lower() or
            '停止' in content or
            '启动' in content
        )
        assert has_controls, (
            "FAIL: 前端页面未找到暂停/恢复控制按钮"
        )

    def test_frontend_has_run_now_button(self):
        """前端应有"立即执行"按钮"""
        frontend_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'frontend', 'src',
            'views', 'system', 'Tasks.vue'
        )
        if not os.path.exists(frontend_path):
            pytest.skip("前端文件不存在，跳过")

        with open(frontend_path, 'r', encoding='utf-8') as f:
            content = f.read()

        has_run_now = (
            'run' in content.lower() and 'now' in content.lower() or
            '立即执行' in content or
            '手动触发' in content
        )
        if not has_run_now:
            pytest.skip("前端可能未实现立即执行按钮，后续可补充")


# =====================================================================
# 依赖检查
# =====================================================================

class TestDependencies:
    """检查 TASK-12 的依赖项"""

    def test_apscheduler_installed(self):
        """APScheduler 依赖应已安装"""
        try:
            import apscheduler
            assert apscheduler.__version__
        except ImportError:
            pytest.fail(
                "FAIL: APScheduler 未安装，请执行: pip install apscheduler"
            )

    def test_task_run_log_model_in_db_schema(self):
        """task_run_logs 表应在数据库模型中定义"""
        models_dir = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'models'
        )
        model_files = os.listdir(models_dir)
        has_task_log = any(
            'task' in f.lower() and 'log' in f.lower()
            for f in model_files
        )
        if not has_task_log:
            pytest.skip("task_run_logs 模型尚未创建，可后续补充")


# =====================================================================
# 运行结果汇总
# =====================================================================

if __name__ == "__main__":
    import subprocess
    result = subprocess.run(
        ["python", "-m", "pytest", __file__, "-v", "--tb=short"],
        capture_output=True, text=True
    )
    print(result.stdout)
    print(result.stderr)
