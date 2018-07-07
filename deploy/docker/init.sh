#!/bin/bash

#    Copyright 2018 Simon Biggs

#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at

#        http://www.apache.org/licenses/LICENSE-2.0

#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

echo "Running Docker Init Script"

echo 'deb http://apt.postgresql.org/pub/repos/apt/ stretch-pgdg main' > /etc/apt/sources.list.d/pgdg.list
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
apt-get update
apt-get install -y postgresql-client-10

PGPASSWORD=postgres

touch /root/.is_inside_docker

pip install virtualenv
mkdir -p deploy/docker/user-data/python-virtualenv
virtualenv deploy/docker/user-data/python-virtualenv
source deploy/docker/user-data/python-virtualenv/bin/activate

pip install -r requirements.postgres.txt

path_append="
import sys
sys.path.append('/usr/src/qatrackplus/deploy/docker')
"

backup_restore="
$path_append
import docker_utilities
docker_utilities.run_backup()
docker_utilities.run_restore()
"

echo "$backup_restore" | python

initialisation="
$path_append
import docker_initialisation
docker_initialisation.initialisation()
"

echo "$initialisation" | python /usr/src/qatrackplus/manage.py shell

chown -R `stat -c "%u:%g" /usr/src/qatrackplus` /usr/src/qatrackplus/deploy/docker/user-data/backup-management

# /usr/bin/crontab deploy/docker/crontab
gunicorn qatrack.wsgi:application -w 2 -b :8000
