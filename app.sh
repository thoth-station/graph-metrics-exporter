#!/usr/bin/env sh
#
# This script is run by OpenShift's s2i. Here we guarantee that we run desired
# command
#

set -o nounset
set -o errexit
set -o errtrace
set -o pipefail
trap 'echo "Aborting due to errexit on line $LINENO. Exit code: $?" >&2' ERR

THOTH_GRAPH_METRICS_EXPORTER=${THOTH_GRAPH_METRICS_EXPORTER:?'THOTH_GRAPH_METRICS_EXPORTER is not selected!'}

if [ "$THOTH_GRAPH_METRICS_EXPORTER" = "graph_corruption_check" ]; then
    exec python3 graph_corruption_check.py
fi
