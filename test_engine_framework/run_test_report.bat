@echo off
echo ==============================================
echo 1. pytest begin...
echo ==============================================

if "%~1"=="" (
    echo Running all tests...
    pytest runner/test_driver.py --alluredir=./output/report/allure-results
) else (
    echo Running tests with tags: %*
    pytest runner/test_driver.py --alluredir=./output/report/allure-results --tags %*
)

echo.
echo ==============================================
echo 2. generating Allure report...
echo ==============================================
allure generate ./output/report/allure-results -o ./output/report/allure-report --clean

@REM echo.
@REM echo ==============================================
@REM echo 3. opening Allure report...
@REM echo ==============================================
@REM allure open ./output/report/allure-report

@REM echo.
@REM echo please check on web browser...
@REM pause