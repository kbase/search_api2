# Makefile for search_api2
.PHONY: all test docs

test:
	sh scripts/run_tests

build-dev-images:
	@echo Building integration test images...
	sh scripts/build-integration-test-images.sh
	@echo Integration test images built

integration-tests: 
	@echo Running Integration Tests...
	sh scripts/run_integration_tests

run-dev-server:
	@echo Starting dev server...
	sh scripts/run-dev-server.sh
