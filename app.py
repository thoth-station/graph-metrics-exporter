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


__version__ = "0.5.7"
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
    TABLE_BLOAT_DATA = "graph_table_bloat_data_check"
    INDEX_BLOAT_DATA = "graph_index_bloat_data_check"


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
    ["env"],
    registry=PROMETHEUS_REGISTRY,
)

graphdb_pct_bloat_data_table = Gauge(
    "thoth_graphdb_pct_bloat_data_table",
    "Bloat data (pct_bloat) per table in Thoth Knowledge Graph.",
    ["table_name", "env"],
    registry=PROMETHEUS_REGISTRY,
)

graphdb_mb_bloat_data_table = Gauge(
    "thoth_graphdb_mb_bloat_data_table",
    "Bloat data (mb_bloat) per table in Thoth Knowledge Graph.",
    ["table_name", "env"],
    registry=PROMETHEUS_REGISTRY,
)

graphdb_pct_index_bloat_data_table = Gauge(
    "thoth_graphdb_pct_index_bloat_data_table",
    "Index Bloat data (bloat_pct) per table in Thoth Knowledge Graph.",
    ["table_name", "index_name", "env"],
    registry=PROMETHEUS_REGISTRY,
)

graphdb_mb_index_bloat_data_table = Gauge(
    "thoth_graphdb_mb_index_bloat_data_table",
    "Index Bloat data (bloat_mb) per table in Thoth Knowledge Graph.",
    ["table_name", "index_name", "env"],
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
        graphdb_is_corrupted.labels(THOTH_DEPLOYMENT_NAME).set(1)
    else:
        _LOGGER.info("Graph database is not corrupted.")
        graphdb_is_corrupted.labels(THOTH_DEPLOYMENT_NAME).set(0)


def _graph_table_bloat_data(graph: GraphDatabase):
    bloat_data = graph.get_bloat_data()

    if bloat_data:
        for table_data in bloat_data:
            graphdb_pct_bloat_data_table.labels(table_data["tablename"], THOTH_DEPLOYMENT_NAME).set(
                table_data["pct_bloat"]
            )
            _LOGGER.info(
                "thoth_graphdb_pct_bloat_data_table(%r, %r)=%r",
                table_data["tablename"],
                THOTH_DEPLOYMENT_NAME,
                table_data["pct_bloat"],
            )

            graphdb_mb_bloat_data_table.labels(table_data["tablename"], THOTH_DEPLOYMENT_NAME).set(
                table_data["mb_bloat"]
            )
            _LOGGER.info(
                "thoth_graphdb_mb_bloat_data_table(%r, %r)=%r",
                table_data["tablename"],
                THOTH_DEPLOYMENT_NAME,
                table_data["mb_bloat"],
            )
    else:
        graphdb_pct_bloat_data_table.labels("No table pct", THOTH_DEPLOYMENT_NAME).set(0)
        _LOGGER.info("thoth_graphdb_pct_bloat_data_table is empty")

        graphdb_mb_bloat_data_table.labels("No table mb", THOTH_DEPLOYMENT_NAME).set(0)
        _LOGGER.info("thoth_graphdb_mb_bloat_data_table is empty")


def _graph_index_bloat_data(graph: GraphDatabase):
    index_bloat_data = graph.get_index_bloat_data()

    if index_bloat_data:
        for table_data in index_bloat_data:
            graphdb_pct_index_bloat_data_table.labels(
                table_data["table_name"], table_data["index_name"], THOTH_DEPLOYMENT_NAME
            ).set(table_data["bloat_pct"])
            _LOGGER.info(
                "thoth_graphdb_pct_index_bloat_data_table(%r, %r, %r)=%r",
                table_data["table_name"],
                table_data["index_name"],
                THOTH_DEPLOYMENT_NAME,
                table_data["bloat_pct"],
            )

            graphdb_mb_index_bloat_data_table.labels(
                table_data["table_name"], table_data["index_name"], THOTH_DEPLOYMENT_NAME
            ).set(table_data["bloat_mb"])
            _LOGGER.info(
                "thoth_graphdb_mb_index_bloat_data_table(%r, %r, %r)=%r",
                table_data["table_name"],
                table_data["index_name"],
                THOTH_DEPLOYMENT_NAME,
                table_data["bloat_mb"],
            )
    else:
        graphdb_pct_index_bloat_data_table.labels("No table pct", THOTH_DEPLOYMENT_NAME).set(0)
        _LOGGER.info("thoth_graphdb_pct_index_bloat_data_table is empty")

        graphdb_mb_index_bloat_data_table.labels("No table mb", THOTH_DEPLOYMENT_NAME).set(0)
        _LOGGER.info("thoth_graphdb_mb_index_bloat_data_table is empty")


@click.command()
@click.option(
    "--task", "-t", type=click.Choice([entity.value for entity in TaskEnum], case_sensitive=False), required=False
)
def main(task):
    """Run log running task on the database for graph metrics exporter."""
    _LOGGER.debug("Debug mode is on.")

    _create_common_metrics()

    graph = GraphDatabase()
    graph.connect()

    if task:
        _LOGGER.info(f"{task} task starting...")
    else:
        _LOGGER.info("No specific task selected, all tasks will be run...")

    if task == TaskEnum.CORRUPTION_CHECK.value or not task:
        _graph_corruption_check(graph=graph)

    if task == TaskEnum.TABLE_BLOAT_DATA.value or not task:
        _graph_table_bloat_data(graph=graph)

    if task == TaskEnum.INDEX_BLOAT_DATA.value or not task:
        _graph_index_bloat_data(graph=graph)

    _send_metrics()
    _LOGGER.info("Graph metrics exporter finished.")


if __name__ == "__main__":
    _LOGGER.info("graph-metrics-exporter  v%s starting...", __service_version__)
    main(auto_envvar_prefix="THOTH_GRAPH_METRICS_EXPORTER")
