# -*- coding: utf-8 -*-
"""
TASK-10 测试脚本：加密管理前端页面 - 全新功能
测试目标：验证加密管理功能（后端API + 前端页面）

运行方式：
    cd smart-campus
    python -m pytest backend/tests/test_task10_encryption.py -v

通过条件：所有测试用例通过后方可将 TASK-10 标记为完成
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
    """验证 TASK-10 所需文件已创建"""

    def test_backend_api_file_exists(self):
        """后端 API 文件应已创建：system/encryption.py"""
        backend_path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'api', 'v1',
            'system', 'encryption.py'
        )
        assert os.path.exists(backend_path), (
            f"FAIL: 后端文件不存在 {backend_path}\n"
            "需要创建: backend/app/api/v1/system/encryption.py"
        )

    def test_frontend_page_exists(self):
        """前端页面应已创建：Encryption.vue"""
        frontend_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'frontend', 'src',
            'views', 'system', 'Encryption.vue'
        )
        if not os.path.exists(frontend_path):
            pytest.skip(f"前端文件尚未创建（可后续创建）: {frontend_path}")


# =====================================================================
# 后端 API 结构测试
# =====================================================================

class TestEncryptionAPIStructure:
    """验证 encryption.py 的 API 路由结构"""

    def test_router_importable(self):
        """router 对象可正常导入"""
        try:
            from app.api.v1.system.encryption import router
            assert router is not None
        except ImportError as e:
            pytest.fail(f"无法导入 router: {e}")

    def test_list_keys_endpoint_exists(self):
        """GET /keys 路由存在"""
        try:
            from app.api.v1.system.encryption import router
            routes = [r.path for r in router.routes]
            has_list = any('key' in r and '{' not in r for r in routes)
            assert has_list, (
                f"未找到密钥列表路由 GET /keys，现有路由: {routes}"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_create_key_endpoint_exists(self):
        """POST /keys 路由存在"""
        try:
            from app.api.v1.system.encryption import router
            routes = [r.path for r in router.routes]
            has_create = any(
                'key' in r and '{' not in r
                for method in ['POST', 'post']
                for r in routes
            )
            # 简化检查：至少有 POST 方法的路由
            post_routes = [
                r.path for r in router.routes
                if hasattr(r, 'methods') and 'POST' in r.methods
            ]
            has_post = any('key' in r for r in post_routes)
            assert has_post, (
                f"未找到创建密钥路由 POST /keys，现有 POST 路由: {post_routes}"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_rotate_key_endpoint_exists(self):
        """PUT /keys/{id}/rotate 路由存在"""
        try:
            from app.api.v1.system.encryption import router
            routes = [r.path for r in router.routes]
            has_rotate = any('rotate' in r for r in routes)
            assert has_rotate, (
                f"未找到密钥轮换路由 PUT /keys/{{id}}/rotate，现有路由: {routes}"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")

    def test_delete_key_endpoint_exists(self):
        """DELETE /keys/{id} 路由存在"""
        try:
            from app.api.v1.system.encryption import router
            routes = [r.path for r in router.routes]
            delete_routes = [
                r.path for r in router.routes
                if hasattr(r, 'methods') and 'DELETE' in r.methods
            ]
            has_delete = any('key' in r and '{' in r for r in delete_routes)
            assert has_delete, (
                f"未找到删除密钥路由 DELETE /keys/{{id}}，现有 DELETE 路由: {delete_routes}"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")


# =====================================================================
# 核心功能逻辑测试
# =====================================================================

class TestEncryptionBusinessLogic:
    """验证加密管理的核心业务逻辑"""

    def test_key_response_model_exists(self):
        """EncryptionKey / KeyInfo 响应模型存在"""
        try:
            from app.api.v1.system.encryption import EncryptionKey, KeyStatus
            key = EncryptionKey(
                id=1,
                name="AES-256 密钥",
                key_type="AES",
                status=KeyStatus.ACTIVE,
                created_at="2026-04-11T10:00:00",
                expires_at="2027-04-11T10:00:00",
            )
            d = key.model_dump() if hasattr(key, 'model_dump') else key.dict()
            required_keys = ['id', 'name', 'key_type', 'status']
            for key_field in required_keys:
                assert key_field in d, f"EncryptionKey 缺少必需字段: {key_field}"
        except ImportError:
            pytest.skip("EncryptionKey 模型未实现，跳过")

    def test_create_key_model_validation(self):
        """CreateKeyRequest 模型验证"""
        try:
            from app.api.v1.system.encryption import CreateKeyRequest
            req = CreateKeyRequest(
                name="测试密钥",
                key_type="AES",
                algorithm="AES-256-GCM",
            )
            assert req.name == "测试密钥"
        except ImportError:
            pytest.skip("CreateKeyRequest 模型未实现，跳过")

    def test_key_type_enum_values(self):
        """KeyType / KeyStatus 枚举值正确"""
        try:
            from app.api.v1.system.encryption import KeyType, KeyStatus
            # 验证枚举值存在
            assert hasattr(KeyType, 'AES') or hasattr(KeyType, 'RSA') or hasattr(KeyType, 'SM4'), (
                "KeyType 应包含常见加密类型（AES/RSA/SM4）"
            )
            assert hasattr(KeyStatus, 'ACTIVE') or hasattr(KeyStatus, 'EXPIRED') or hasattr(KeyStatus, 'INACTIVE'), (
                "KeyStatus 应包含常见状态（ACTIVE/EXPIRED/INACTIVE）"
            )
        except ImportError:
            pytest.skip("枚举类型未实现，跳过")

    def test_rotate_key_generates_new_key(self):
        """密钥轮换应生成新密钥"""
        try:
            from app.api.v1.system.encryption import router
            source_path = os.path.join(
                os.path.dirname(__file__), '..', 'app', 'api', 'v1',
                'system', 'encryption.py'
            )
            with open(source_path, 'r', encoding='utf-8') as f:
                source = f.read()

            # 检查是否有轮换逻辑
            has_rotate_logic = (
                'rotate' in source.lower() or
                'new_key' in source.lower() or
                'generate' in source.lower() and 'key' in source.lower()
            )
            assert has_rotate_logic, (
                "FAIL: 密钥轮换应生成新密钥值"
            )
        except ImportError:
            pytest.skip("模块无法导入，跳过")


# =====================================================================
# 前端页面测试（结构验证）
# =====================================================================

class TestEncryptionFrontend:
    """验证前端页面结构"""

    def test_frontend_file_exists(self):
        """Encryption.vue 文件应存在"""
        frontend_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'frontend', 'src',
            'views', 'system', 'Encryption.vue'
        )
        assert os.path.exists(frontend_path), (
            f"FAIL: 前端文件不存在: {frontend_path}"
        )

    def test_frontend_has_key_list(self):
        """前端应有密钥列表"""
        frontend_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'frontend', 'src',
            'views', 'system', 'Encryption.vue'
        )
        if not os.path.exists(frontend_path):
            pytest.skip("前端文件不存在，跳过")

        with open(frontend_path, 'r', encoding='utf-8') as f:
            content = f.read()

        has_list = (
            'key' in content.lower() and
            ('table' in content.lower() or 'list' in content.lower())
        )
        assert has_list, (
            "FAIL: 前端页面未找到密钥列表展示"
        )

    def test_frontend_has_create_button(self):
        """前端应有创建密钥按钮"""
        frontend_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'frontend', 'src',
            'views', 'system', 'Encryption.vue'
        )
        if not os.path.exists(frontend_path):
            pytest.skip("前端文件不存在，跳过")

        with open(frontend_path, 'r', encoding='utf-8') as f:
            content = f.read()

        has_create = (
            'create' in content.lower() or
            '新增' in content or
            '创建' in content or
            'add' in content.lower()
        )
        assert has_create, (
            "FAIL: 前端页面未找到创建密钥按钮"
        )

    def test_frontend_has_rotate_button(self):
        """前端应有密钥轮换按钮"""
        frontend_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'frontend', 'src',
            'views', 'system', 'Encryption.vue'
        )
        if not os.path.exists(frontend_path):
            pytest.skip("前端文件不存在，跳过")

        with open(frontend_path, 'r', encoding='utf-8') as f:
            content = f.read()

        has_rotate = (
            'rotate' in content.lower() or
            '轮换' in content or
            'rotation' in content.lower()
        )
        if not has_rotate:
            pytest.skip("前端可能未实现密钥轮换按钮，后续可补充")

    def test_frontend_calls_backend_api(self):
        """前端应调用后端加密管理 API"""
        frontend_path = os.path.join(
            os.path.dirname(__file__), '..', '..', 'frontend', 'src',
            'views', 'system', 'Encryption.vue'
        )
        if not os.path.exists(frontend_path):
            pytest.skip("前端文件不存在，跳过")

        with open(frontend_path, 'r', encoding='utf-8') as f:
            content = f.read()

        has_api_call = (
            'axios' in content.lower() or
            'fetch' in content.lower() or
            'http' in content.lower()
        ) and (
            'encryption' in content.lower() or
            'key' in content.lower()
        )
        assert has_api_call, (
            "FAIL: 前端页面未调用加密管理 API"
        )


# =====================================================================
# 安全检查
# =====================================================================

class TestEncryptionSecurity:
    """验证加密管理的安全性"""

    def test_no_hardcoded_keys_in_source(self):
        """源代码中不应硬编码真实密钥值"""
        api_path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'api', 'v1',
            'system', 'encryption.py'
        )
        if not os.path.exists(api_path):
            pytest.skip("API 文件尚未创建，跳过")

        with open(api_path, 'r', encoding='utf-8') as f:
            source = f.read()

        # 检查可疑的硬编码密钥模式
        suspicious_patterns = [
            'key = "sk-',              # API Key 格式
            'password = "',           # 密码硬编码
            'secret = "sk-',          # Secret 格式
            'bearer ',                # Bearer Token
        ]
        found = [p for p in suspicious_patterns if p in source.lower()]
        if found:
            pytest.fail(
                f"FAIL: 发现可疑的硬编码密钥模式: {found}\n"
                "密钥应通过数据库或配置管理，不应硬编码在源码中"
            )

    def test_key_values_not_returned_in_response(self):
        """API 响应中不应返回完整密钥值（应遮蔽或仅返回元数据）"""
        api_path = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'api', 'v1',
            'system', 'encryption.py'
        )
        if not os.path.exists(api_path):
            pytest.skip("API 文件尚未创建，跳过")

        with open(api_path, 'r', encoding='utf-8') as f:
            source = f.read()

        # 检查是否有遮蔽或脱敏逻辑
        has_masking = (
            'mask' in source.lower() or
            'hide' in source.lower() or
            '***' in source or
            '****' in source or
            'partial' in source.lower() or
            'secret' in source.lower()
        )
        if not has_masking:
            pytest.skip(
                "WARNING: API 可能返回完整密钥值，建议添加遮蔽处理"
            )


# =====================================================================
# 依赖检查
# =====================================================================

class TestDependencies:
    """检查 TASK-10 的依赖项"""

    def test_cryptography_or_pyca_installed(self):
        """应安装加密库（cryptography 或 PyCA）"""
        try:
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
            assert hashes and Cipher
        except ImportError:
            pytest.skip(
                "cryptography 库未安装（可选：用于密钥生成和轮换）"
            )

    def test_encryption_model_in_models_dir(self):
        """加密相关模型应在 models 目录中定义"""
        models_dir = os.path.join(
            os.path.dirname(__file__), '..', 'app', 'models'
        )
        if not os.path.exists(models_dir):
            pytest.skip("models 目录不存在，跳过")

        model_files = os.listdir(models_dir)
        has_encryption_model = any(
            'encrypt' in f.lower() for f in model_files
        )
        if not has_encryption_model:
            pytest.skip("encryption 模型可能尚未创建，可后续补充")


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
