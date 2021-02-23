# Makefile for search_api2
.PHONY: all test docs

test:
	sh scripts/run_tests

build-integration-test-images:
	@echo Building integration test images...
	cd tests/integration/docker
	docker-compose build
	cd ../../..
	@echo Integration test images built

integration-tests: 
	@echo Running Integraion Tests...
	sh scripts/run_integration_tests
