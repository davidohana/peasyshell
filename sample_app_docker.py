#!/usr/bin/env python2

from peasyshell import *

# initialize logging to stdout in colors by severity level
init_logging()

container_name = "ES"
image_name = "elasticsearch:6.8.13"

get_latest = yes_or_no("get latest version?")
if get_latest:
    out = sh("docker image pull {}".format(image_name)).stdout

container_id = sh("docker ps -q -a -f name=^/{}$".format(container_name), capture_out=True).stdout
if container_id:
    logger.info("removing old container with ID " + container_id)
    sh("docker rm -f " + container_id)
else:
    logger.info("container does not exist")

container_id = sh("docker run -d --name {} {}".format(container_name, image_name), capture_out=True).stdout

sh("docker logs {} -f".format(container_id), timeout_sec=5)

logger.info("done")
