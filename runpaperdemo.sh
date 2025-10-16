#!/bin/bash

# Comprehensive PAPER_MODE demonstration script for the meme-coin trading bot
# This script validates the environment, runs tests, and executes a complete demo

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DEMO_DURATION=${1:-5}  # Default 5 minutes
VENV_DIR="venv"
REQUIREMENTS_FILE="requirements.txt"
ENV_FILE=".env"
ENV_EXAMPLE="env.example"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to validate environment
validate_environment() {
    print_status "Validating environment..."
    
    # Check Python version
    if ! command_exists python3; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
    required_version="3.11"
    
    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
        print_error "Python 3.11+ is required. Found: $python_version"
        exit 1
    fi
    
    print_success "Python version check passed: $python_version"
    
    # Check if virtual environment exists
    if [ ! -d "$VENV_DIR" ]; then
        print_warning "Virtual environment not found. Creating..."
        python3 -m venv "$VENV_DIR"
        print_success "Virtual environment created"
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    print_success "Virtual environment activated"
    
    # Check if requirements file exists
    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        print_error "Requirements file not found: $REQUIREMENTS_FILE"
        exit 1
    fi
    
    # Install/update dependencies
    print_status "Installing dependencies..."
    pip install --upgrade pip
    pip install -r "$REQUIREMENTS_FILE"
    print_success "Dependencies installed"
    
    # Check if .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        print_warning "Environment file not found. Creating from example..."
        if [ -f "$ENV_EXAMPLE" ]; then
            cp "$ENV_EXAMPLE" "$ENV_FILE"
            print_success "Environment file created from example"
            print_warning "Please edit $ENV_FILE with your actual values before running live mode"
        else
            print_error "Environment example file not found: $ENV_EXAMPLE"
            exit 1
        fi
    fi
    
    print_success "Environment validation completed"
}

# Function to run unit tests
run_tests() {
    print_status "Running unit tests..."
    
    # Check if pytest is available
    if ! command_exists pytest; then
        print_warning "pytest not found. Installing..."
        pip install pytest
    fi
    
    # Run tests
    if [ -d "tests" ]; then
        pytest tests/ -v --tb=short
        print_success "Unit tests completed"
    else
        print_warning "No tests directory found. Skipping tests."
    fi
}

# Function to run component tests
run_component_tests() {
    print_status "Running component tests..."
    
    # Run the test_bot.py script
    if [ -f "test_bot.py" ]; then
        python test_bot.py
        print_success "Component tests completed"
    else
        print_warning "test_bot.py not found. Skipping component tests."
    fi
}

# Function to create dumps directory
create_dumps_directory() {
    print_status "Creating dumps directory..."
    
    if [ ! -d "dumps" ]; then
        mkdir -p dumps
        print_success "Dumps directory created"
    else
        print_status "Dumps directory already exists"
    fi
}

# Function to run the paper mode demo
run_paper_demo() {
    print_status "Starting PAPER_MODE demonstration..."
    print_status "Duration: $DEMO_DURATION minutes"
    print_status "This will simulate the complete bot functionality without real trading"
    
    # Run the demo
    python run_paper_demo.py "$DEMO_DURATION"
    
    print_success "PAPER_MODE demonstration completed"
}

# Function to display results
display_results() {
    print_status "Displaying results..."
    
    if [ -d "dumps" ]; then
        echo ""
        echo "Generated files:"
        ls -la dumps/
        echo ""
        
        if [ -f "dumps/paperdemo_summary.json" ]; then
            echo "Demo Summary:"
            cat dumps/paperdemo_summary.json | python -m json.tool
            echo ""
        fi
    fi
}

# Function to cleanup
cleanup() {
    print_status "Cleaning up..."
    
    # Deactivate virtual environment if active
    if [ -n "$VIRTUAL_ENV" ]; then
        deactivate
        print_success "Virtual environment deactivated"
    fi
    
    print_success "Cleanup completed"
}

# Function to display help
display_help() {
    echo "Usage: $0 [duration_minutes]"
    echo ""
    echo "Arguments:"
    echo "  duration_minutes    Duration of the demo in minutes (default: 5)"
    echo ""
    echo "Examples:"
    echo "  $0                 # Run 5-minute demo"
    echo "  $0 10              # Run 10-minute demo"
    echo "  $0 1               # Run 1-minute demo"
    echo ""
    echo "This script will:"
    echo "  1. Validate the environment"
    echo "  2. Run unit tests"
    echo "  3. Run component tests"
    echo "  4. Start PAPER_MODE demonstration"
    echo "  5. Generate detailed reports"
    echo ""
    echo "Results will be saved in the dumps/ directory"
}

# Main execution
main() {
    # Check for help flag
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        display_help
        exit 0
    fi
    
    print_status "Starting PAPER_MODE demonstration script"
    print_status "Demo duration: $DEMO_DURATION minutes"
    echo ""
    
    # Set up trap for cleanup on exit
    trap cleanup EXIT
    
    # Execute steps
    validate_environment
    run_tests
    run_component_tests
    create_dumps_directory
    run_paper_demo
    display_results
    
    print_success "PAPER_MODE demonstration script completed successfully"
    echo ""
    print_status "Next steps:"
    print_status "  1. Review the generated reports in dumps/ directory"
    print_status "  2. Check the compliance results and trading simulations"
    print_status "  3. If satisfied, configure .env file for live trading"
    print_status "  4. Run 'python main.py --paper-mode' for extended testing"
    print_status "  5. When ready, run 'python main.py' for live trading"
}

# Run main function
main "$@"
