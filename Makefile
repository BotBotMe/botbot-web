# Developer Makefile

### Default Configuration.  Override in a make.config file

# the path to the lib folder in the venv
LOCAL_LIB=$(VIRTUAL_ENV)/lib

# where executables are stored
LOCAL_BIN=$(VIRTUAL_ENV)/bin

# where source files are stored
LOCAL_SRC=$(VIRTUAL_ENV)/src

# where misc files are stored
LOCAL_VAR=$(VIRTUAL_ENV)/var

NPM_BIN := $(or $(shell command -v npm),$(LOCAL_BIN)/npm)
LESS_BIN := $(or $(shell command -v lessc),$(LOCAL_BIN)/lessc)
JSHINT_BIN := $(or $(shell command -v jshint),$(LOCAL_BIN)/jshint)
WATCHMEDO_BIN := $(or $(shell command -v watchmedo),$(LOCAL_BIN)/watchmedo)

# allows a file make.config to override the above variables
-include make.config

### PIP
.pip-timestamp: requirements.txt
	pip install -r requirements.txt
	touch .pip-timestamp

pip-install: .pip-timestamp

$(LOCAL_BIN)/sphinx-build:
	pip install Sphinx

### GENERAL PYTHON COMMANDS
clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

### GO SUPPORT

$(LOCAL_BIN)/botbot-bot:
	GOPATH=$(VIRTUAL_ENV) go get github.com/BotBotMe/botbot-bot

test-bot:
	GOPATH=$(VIRTUAL_ENV) go test github.com/BotBotMe/botbot-bot

$(LOCAL_BIN)/botbot-eventsource:
	GOPATH=$(VIRTUAL_ENV) go get github.com/BotBotMe/botbot-eventsource

### LOCAL LESS SUPPORT
$(NPM_BIN):
	@echo "Installing node.js..."
	cd $(VIRTUAL_ENV) && mkdir -p "src"
	cd $(LOCAL_LIB) && curl http://nodejs.org/dist/node-latest.tar.gz | tar xvz
	cd $(LOCAL_LIB)/node-v* && ./configure --prefix=$(VIRTUAL_ENV) && make install
	@echo "Installed npm"

$(LESS_BIN): $(NPM_BIN)
	NPM_CONFIG_PREFIX=$(VIRTUAL_ENV) npm install "less@<1.4" -g

less-install: $(LESS_BIN)

less-compile:
	lessc botbot/less/screen.less > botbot/static/css/screen.css

$(WATCHMEDO_BIN):
	# Install watchdog to run commands when files change
	pip install watchdog argcomplete

less-watch: $(WATCHMEDO_BIN)
	watchmedo shell-command --patterns=*.less --recursive --command="make less-compile" botbot/less

### Local JSHint

$(JSHINT_BIN): $(NPM_BIN)
	NPM_CONFIG_PREFIX=$(VIRTUAL_ENV) npm install jshint -g

jshint-install: $(JSHINT_BIN)

jshint:
	jshint botbot/static/js/app/

### Local Settings

.env:
	cp .env.example $@

local-settings: .env

### General Tasks
dependencies: less-install pip-install local-settings $(LOCAL_BIN)/botbot-bot $(LOCAL_BIN)/botbot-eventsource

$(LOCAL_VAR)/GeoLite2-City.mmdb:
	curl http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.mmdb.gz | gunzip -c > $@

geoip-db: $(LOCAL_VAR)/GeoLite2-City.mmdb

run: dependencies
	honcho start

docs: $(LOCAL_BIN)/sphinx-build
	cd docs && make html

.PHONY: clean-pyc run pip-install less-install jshint-install dependencies local-settings docs geoip-db
