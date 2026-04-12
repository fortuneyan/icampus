@echo off
REM 前端构建验证脚本
cd /d "%~dp0.."

echo ========================================
echo 智慧校园管理平台 - 前端构建验证
echo ========================================

echo.
echo [1/3] 清理旧的node_modules...
if exist node_modules (
    rmdir /s /q node_modules 2>nul
)
if exist package-lock.json (
    del /f /q package-lock.json 2>nul
)

echo.
echo [2/3] 重新安装依赖（包含测试框架）...
call npm install

echo.
echo [3/3] 运行TypeScript类型检查...
call npx vue-tsc --noEmit 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo TypeScript检查发现问题，请检查代码
) else (
    echo TypeScript类型检查通过
)

echo.
echo ========================================
echo 构建验证完成
echo ========================================
pause
