
# Makefile for building the python-inliner executable

# Toolchain
PYLINER = python-inliner

# Targets
BUILD_DIR = build
TARGET ?= /opt/local/bin

# Source files
MAIN_FILE = main.py

# INLINE MODULES
INLINE_MODULES = modules,string_space_completer,string_space_client

# Executable name
EXECUTABLE = llm_api_chat.py

# Default target
all: debug

setup:
		mkdir -p $(BUILD_DIR)

# Build the project in debug mode
debug: setup
		$(PYLINER) $(MAIN_FILE) $(BUILD_DIR)/$(EXECUTABLE) $(INLINE_MODULES) -v
		chmod +x $(BUILD_DIR)/$(EXECUTABLE)
		@echo "Debug build completed. Executable is located at $(BUILD_DIR)/$(EXECUTABLE)"

# Build the project in release mode
release: setup test
		$(PYLINER) $(MAIN_FILE) $(BUILD_DIR)/$(EXECUTABLE) $(INLINE_MODULES) --release
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
