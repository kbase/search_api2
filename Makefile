.PHONY: test reset

# Run tests
test:
	docker-compose down
	docker-compose run web sh scripts/run_tests.sh
	docker-compose down

# Shutdown and remove test containers
reset-test:
	docker-compose down -v --remove-orphans

# Build test image
build-test:
	docker-compose down -v --remove-orphans
	docker-compose build --no-cache

# Remove all test artifacts from docker
teardown-test:
	docker-compose down -v --remove-orphans --rmi all

reset:
	docker-compose down -v --remove-orphans --rmi all
	docker-compose build --no-cache
