
# Makefile for building the python-inliner executable

# Toolchain
PYLINER = python-inliner

# Targets
BUILD_DIR = build
TARGET ?= $(HOME)/bin

# Source files
MAIN_FILE = main.py

# Executable name
EXECUTABLE = llm_api_chat.py

# Default target
all: debug

setup:
		mkdir -p $(BUILD_DIR)

# Build the project in debug mode
debug: setup
		$(PYLINER) $(MAIN_FILE) $(BUILD_DIR)/$(EXECUTABLE)
		chmod +x $(BUILD_DIR)/$(EXECUTABLE)
		@echo "Debug build completed. Executable is located at $(BUILD_DIR)/$(EXECUTABLE)"

# Build the project in release mode
release: setup test
		$(PYLINER) $(MAIN_FILE) $(BUILD_DIR)/$(EXECUTABLE) --release
		chmod +x $(BUILD_DIR)/$(EXECUTABLE)
		@echo "Release build completed. Executable is located at $(BUILD_DIR)/$(EXECUTABLE)"

# Clean up build artifacts
clean:
		rm -f "$(BUILD_DIR)/*""

test:
		pytest

install: release
		cp $(BUILD_DIR)/$(EXECUTABLE) $(TARGET)
		@echo "Executable installed to $(TARGET)"

# Phony targets
.PHONY: all debug release clean test
