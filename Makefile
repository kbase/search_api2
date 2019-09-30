.PHONY: test reset

test:
	docker-compose run web sh scripts/run_tests.sh

reset:
	docker-compose down -v --remove-orphans --rmi all
	docker-compose build --no-cache
