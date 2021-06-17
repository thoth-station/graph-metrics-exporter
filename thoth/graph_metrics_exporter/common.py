#!/usr/bin/env python3
# thoth-graph-metrics-exporter
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

"""Common methods for all graph metrics exporter async tasks."""

import logging

from prometheus_client import Gauge, push_to_gateway
from thoth.storages import GraphDatabase
from thoth.graph_metrics_exporter.configuration import Configuration

_LOGGER = logging.getLogger(__name__)


database_schema_revision_script = Gauge(
    "thoth_database_schema_revision_script",
    "Thoth database schema revision from script",
    ["component", "revision", "env"],
    registry=Configuration.PROMETHEUS_REGISTRY,
)


def create_common_metrics(component_name: str = Configuration.COMPONENT_NAME):
    """Create common metrics to pushgateway."""
    deployment_name = Configuration.THOTH_DEPLOYMENT_NAME

    if deployment_name:
        database_schema_revision_script.labels(
            component_name, GraphDatabase().get_script_alembic_version_head(), deployment_name
        ).inc()
    else:
        _LOGGER.warning("THOTH_DEPLOYMENT_NAME env variable is not set.")

def send_metrics(component_name: str = Configuration.COMPONENT_NAME):
    """Send metrics to pushgateway."""
    pushgateway_url = Configuration.THOTH_METRICS_PUSHGATEWAY_URL
    deployment_name = Configuration.THOTH_DEPLOYMENT_NAME
    if pushgateway_url and deployment_name:
        try:
            _LOGGER.debug(f"Submitting metrics to Prometheus pushgateway {pushgateway_url}")
            push_to_gateway(
                pushgateway_url,
                job=component_name,
                registry=Configuration.PROMETHEUS_REGISTRY,
            )
        except Exception as e:
            _LOGGER.exception(f"An error occurred pushing the metrics: {str(e)}")

    else:
        _LOGGER.warning("PROMETHEUS_PUSHGATEWAY_URL env variable is not set.")