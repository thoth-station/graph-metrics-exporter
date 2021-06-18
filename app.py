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

import click
from enum import Enum

from prometheus_client import CollectorRegistry, Gauge, push_to_gateway

from thoth.common import init_logging
from thoth.storages import GraphDatabase
from thoth.storages import __version__ as __storages_version__
from thoth.common import __version__ as __common_version__


__version__ = "0.0.1"
__service_version__ = f"{__version__}+common.{__common_version__}.storages.{__storages_version__}"

_LOGGER = logging.getLogger("thoth.graph_metrics_exporter")

COMPONENT_NAME = "graph-metrics-exporter"

# metrics
PROMETHEUS_REGISTRY = CollectorRegistry()
THOTH_METRICS_PUSHGATEWAY_URL = os.environ["PROMETHEUS_PUSHGATEWAY_URL"]
THOTH_DEPLOYMENT_NAME = os.environ["THOTH_DEPLOYMENT_NAME"]


class TaskEnum(Enum):
    """Class for the task to be run."""

    CORRUPTION_CHECK = "graph_corruption_check"


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


def _create_common_metrics():
    """Create common metrics to pushgateway."""
    database_schema_revision_script.labels(
        COMPONENT_NAME, GraphDatabase().get_script_alembic_version_head(), THOTH_DEPLOYMENT_NAME
    ).inc()


def _send_metrics():
    """Send metrics to pushgateway."""
    try:
        _LOGGER.debug(f"Submitting metrics to Prometheus pushgateway {THOTH_METRICS_PUSHGATEWAY_URL}")
        push_to_gateway(
            THOTH_METRICS_PUSHGATEWAY_URL,
            job=COMPONENT_NAME,
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


@click.command()
@click.option(
    "--task", "-t", type=click.Choice([entity.value for entity in TaskEnum], case_sensitive=False), required=True
)
def main(task):
    """Run log running task on the database for graph metrics exporter."""
    _LOGGER.debug("Debug mode is on.")

    _create_common_metrics()

    graph = GraphDatabase()
    graph.connect()

    _LOGGER.info(f"{task} task started...")

    if task == TaskEnum.CORRUPTION_CHECK.value:
        _graph_corruption_check(graph=graph)

    _send_metrics()
    _LOGGER.info("Graph metrics exporter finished.")


if __name__ == "__main__":
    _LOGGER.info("graph-metrics-exporter  v%s starting...", __service_version__)
    main(auto_envvar_prefix="THOTH_GRAPH_METRICS_EXPORTER")
