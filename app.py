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

import os
import logging

from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

from thoth.common import init_logging
from thoth.storages import GraphDatabase
from thoth.storages import __version__ as __storages_version__
from thoth.common import __version__ as __common_version__


__version__ = "0.0.1"
__service_version__ = f"{__version__}+" f"common.{__common_version__}.storages.{__storages_version__}"

_LOGGER = logging.getLogger("thoth.graph_metrics_exporter")

COMPONENT_NAME = "graph-metrics-exporter"

# database
KNOWLEDGE_GRAPH_HOST = os.getenv("KNOWLEDGE_GRAPH_HOST", "localhost")
KNOWLEDGE_GRAPH_PORT = os.getenv("KNOWLEDGE_GRAPH_PORT", "5432")
KNOWLEDGE_GRAPH_USER = os.getenv("KNOWLEDGE_GRAPH_USER", "postgres")
KNOWLEDGE_GRAPH_DATABASE = os.getenv("KNOWLEDGE_GRAPH_DATABASE", "postgres")

# metrics
PROMETHEUS_REGISTRY = CollectorRegistry()
THOTH_METRICS_PUSHGATEWAY_URL = os.environ["PROMETHEUS_PUSHGATEWAY_URL"]
THOTH_DEPLOYMENT_NAME = os.environ["THOTH_DEPLOYMENT_NAME"]

GRAPH_METRICS_EXPORTER_TASK = os.environ["THOTH_GRAPH_METRICS_EXPORTER_TASK"]

init_logging()

database_schema_revision_script = Gauge(
    "thoth_database_schema_revision_script",
    "Thoth database schema revision from script",
    ["component", "revision", "env"],
    registry=PROMETHEUS_REGISTRY,
)

graphdb_is_corrupted = Gauge(
    "thoth_graphdb_is_corrupted",
    "amcheck has detected corruption.",
    [],
    registry=PROMETHEUS_REGISTRY,
)


def _create_common_metrics(component_name: str = COMPONENT_NAME):
    """Create common metrics to pushgateway."""
    deployment_name = THOTH_DEPLOYMENT_NAME

    if deployment_name:
        database_schema_revision_script.labels(
            component_name, GraphDatabase().get_script_alembic_version_head(), deployment_name
        ).inc()
    else:
        _LOGGER.warning("THOTH_DEPLOYMENT_NAME env variable is not set.")


def _send_metrics(component_name: str = COMPONENT_NAME):
    """Send metrics to pushgateway."""
    pushgateway_url = THOTH_METRICS_PUSHGATEWAY_URL
    try:
        _LOGGER.debug(f"Submitting metrics to Prometheus pushgateway {pushgateway_url}")
        push_to_gateway(
            pushgateway_url,
            job=component_name,
            registry=PROMETHEUS_REGISTRY,
        )
    except Exception as e:
        _LOGGER.exception(f"An error occurred pushing the metrics: {str(e)}")


def _graph_corruption_check(graph: GraphDatabase):
    if graph.is_database_corrupted():
        _LOGGER.info("Graph database is corrupted!")
        graphdb_is_corrupted.set(1)
    else:
        _LOGGER.info("Graph database is not corrupted.")
        graphdb_is_corrupted.set(0)


def main():
    """Perform graph metrics exporter job."""
    _LOGGER.debug("Debug mode is on.")

    _create_common_metrics()

    graph = GraphDatabase()
    graph.connect()

    if GRAPH_METRICS_EXPORTER_TASK == "graph_corruption_check":
        _graph_corruption_check(graph=graph)

    _send_metrics()
    _LOGGER.info("Graph metrics exporter task finished.")


if __name__ == "__main__":
    _LOGGER.info("graph-metrics-exporter  v%s starting...", __service_version__)
    main()
