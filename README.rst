Thoth Graph Metrics Exporter
--------------------------

.. image:: https://img.shields.io/github/v/tag/thoth-station/graph-metrics-exporter?style=plastic
  :target: https://github.com/thoth-station/graph-metrics-exporter/tags
  :alt: GitHub tag (latest by date)

.. image:: https://quay.io/repository/thoth-station/graph-metrics-exporter/status
  :target: https://quay.io/repository/thoth-station/graph-metrics-exporter?tab=tags
  :alt: Quay - Build

Periodic job that exports metrics out of the main database asynchronously.


Run single task
===============

You can run single tasks selecting the name of the task from the allows methods:

.. list-table::
   :widths: 25 25
   :header-rows: 1

   * - Task name
     - Description
   * - ``graph_corruption_check``
     - Check if the database is corruped.
   * - ``graph_table_bloat_data_check``
     - Check if the database tables are bloated.
   * - ``graph_index_bloat_data_check``
     - Check if the database index tables are bloated.
   * - ``graph_database_dumps_check``
     - Check if database dumps are correctly created.
