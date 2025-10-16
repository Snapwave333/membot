@echo off
REM Comprehensive PAPER_MODE demonstration script for the meme-coin trading bot
REM This script validates the environment, runs tests, and executes a complete demo

setlocal enabledelayedexpansion

REM Configuration
set DEMO_DURATION=%1
if "%DEMO_DURATION%"=="" set DEMO_DURATION=5
set VENV_DIR=venv
set REQUIREMENTS_FILE=requirements.txt
set ENV_FILE=.env
set ENV_EXAMPLE=env.example

REM Function to print colored output
:print_status
echo [INFO] %~1
goto :eof

:print_success
echo [SUCCESS] %~1
goto :eof

:print_warning
echo [WARNING] %~1
goto :eof

:print_error
echo [ERROR] %~1
goto :eof

REM Function to validate environment
:validate_environment
call :print_status "Validating environment..."

REM Check Python version
python --version >nul 2>&1
if errorlevel 1 (
    call :print_error "Python is not installed or not in PATH"
    exit /b 1
)

REM Check if virtual environment exists
if not exist "%VENV_DIR%" (
    call :print_warning "Virtual environment not found. Creating..."
    python -m venv "%VENV_DIR%"
    call :print_success "Virtual environment created"
)

REM Activate virtual environment
call "%VENV_DIR%\Scripts\activate.bat"
call :print_success "Virtual environment activated"

REM Check if requirements file exists
if not exist "%REQUIREMENTS_FILE%" (
    call :print_error "Requirements file not found: %REQUIREMENTS_FILE%"
    exit /b 1
)

REM Install/update dependencies
call :print_status "Installing dependencies..."
python -m pip install --upgrade pip
pip install -r "%REQUIREMENTS_FILE%"
call :print_success "Dependencies installed"

REM Check if .env file exists
if not exist "%ENV_FILE%" (
    call :print_warning "Environment file not found. Creating from example..."
    if exist "%ENV_EXAMPLE%" (
        copy "%ENV_EXAMPLE%" "%ENV_FILE%"
        call :print_success "Environment file created from example"
        call :print_warning "Please edit %ENV_FILE% with your actual values before running live mode"
    ) else (
        call :print_error "Environment example file not found: %ENV_EXAMPLE%"
        exit /b 1
    )
)

call :print_success "Environment validation completed"
goto :eof

REM Function to run unit tests
:run_tests
call :print_status "Running unit tests..."

REM Check if pytest is available
pytest --version >nul 2>&1
if errorlevel 1 (
    call :print_warning "pytest not found. Installing..."
    pip install pytest
)

REM Run tests
if exist "tests" (
    pytest tests/ -v --tb=short
    call :print_success "Unit tests completed"
) else (
    call :print_warning "No tests directory found. Skipping tests."
)
goto :eof

REM Function to run component tests
:run_component_tests
call :print_status "Running component tests..."

REM Run the test_bot.py script
if exist "test_bot.py" (
    python test_bot.py
    call :print_success "Component tests completed"
) else (
    call :print_warning "test_bot.py not found. Skipping component tests."
)
goto :eof

REM Function to create dumps directory
:create_dumps_directory
call :print_status "Creating dumps directory..."

if not exist "dumps" (
    mkdir dumps
    call :print_success "Dumps directory created"
) else (
    call :print_status "Dumps directory already exists"
)
goto :eof

REM Function to run the paper mode demo
:run_paper_demo
call :print_status "Starting PAPER_MODE demonstration..."
call :print_status "Duration: %DEMO_DURATION% minutes"
call :print_status "This will simulate the complete bot functionality without real trading"

REM Run the demo
python run_paper_demo.py %DEMO_DURATION%

call :print_success "PAPER_MODE demonstration completed"
goto :eof

REM Function to display results
:display_results
call :print_status "Displaying results..."

if exist "dumps" (
    echo.
    echo Generated files:
    dir dumps
    echo.
    
    if exist "dumps\paperdemo_summary.json" (
        echo Demo Summary:
        type dumps\paperdemo_summary.json
        echo.
    )
)
goto :eof

REM Function to display help
:display_help
echo Usage: %0 [duration_minutes]
echo.
echo Arguments:
echo   duration_minutes    Duration of the demo in minutes (default: 5)
echo.
echo Examples:
echo   %0                 # Run 5-minute demo
echo   %0 10              # Run 10-minute demo
echo   %0 1               # Run 1-minute demo
echo.
echo This script will:
echo   1. Validate the environment
echo   2. Run unit tests
echo   3. Run component tests
echo   4. Start PAPER_MODE demonstration
echo   5. Generate detailed reports
echo.
echo Results will be saved in the dumps/ directory
goto :eof

REM Main execution
:main
REM Check for help flag
if "%1"=="-h" goto :display_help
if "%1"=="--help" goto :display_help

call :print_status "Starting PAPER_MODE demonstration script"
call :print_status "Demo duration: %DEMO_DURATION% minutes"
echo.

REM Execute steps
call :validate_environment
if errorlevel 1 exit /b 1

call :run_tests
call :run_component_tests
call :create_dumps_directory
call :run_paper_demo
call :display_results

call :print_success "PAPER_MODE demonstration script completed successfully"
echo.
call :print_status "Next steps:"
call :print_status "  1. Review the generated reports in dumps/ directory"
call :print_status "  2. Check the compliance results and trading simulations"
call :print_status "  3. If satisfied, configure .env file for live trading"
call :print_status "  4. Run 'python main.py --paper-mode' for extended testing"
call :print_status "  5. When ready, run 'python main.py' for live trading"

goto :eof

REM Run main function
call :main %*
