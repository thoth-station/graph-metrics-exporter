#!/usr/bin/env python3
# Graph Metrics Exporter
# Copyright(C) 2021 Francesco Murdaca
#
# This program is free software: you can redistribute it and / or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""Graph metrics exporter logic for the Thoth project."""

import logging

from prometheus_client import Gauge
from thoth.common import init_logging
from thoth.storages import GraphDatabase

from thoth.graph_metrics_exporter import __service_version__
from thoth.graph_metrics_exporter.configuration import Configuration
from thoth.graph_metrics_exporter.common import send_metrics, create_common_metrics


init_logging()
_LOGGER = logging.getLogger("thoth.graph_corruption_check")

graphdb_is_corrupted = Gauge(
    "thoth_graphdb_is_corrupted",
    "amcheck has detected corruption.",
    [],
    registry=Configuration.PROMETHEUS_REGISTRY,
)


def graph_corruption_check():
    """Perform graph metrics exporter job."""
    _LOGGER.debug("Debug mode is on.")

    create_common_metrics()

    graph = GraphDatabase()
    graph.connect()

    if graph.is_database_corrupted():
        graphdb_is_corrupted.set(1)
    else:
        graphdb_is_corrupted.set(0)
    _LOGGER.info("Graph metrics exporter task finished.")

    send_metrics()
    _LOGGER.info("Graph metrics exporter metrics for graph corruption check sent.")


if __name__ == "__main__":
    _LOGGER.info("graph-metrics-exporter (corruption check) v%s starting...", __service_version__)
    graph_corruption_check()
