SERVERLESS := node_modules/.bin/serverless

node_modules: package.json
	npm install
	touch node_modules

$(SERVERLESS): node_modules

.PHONY: deploy
deploy: $(SERVERLESS)
	$(SERVERLESS) deploy