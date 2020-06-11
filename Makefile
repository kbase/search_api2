.PHONY: start test reset

test:
	docker-compose down
	docker-compose run test sh scripts/run_tests.sh

reset:
	docker-compose down -v --remove-orphans --rmi all
	docker-compose build --no-cache
