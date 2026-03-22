resource "datadog_dashboard" "multicloud" {
  title       = "Multi-Cloud Platform Overview"
  description = "Unified view across AWS, Azure, and GCP"
  layout_type = "ordered"

  widget {
    timeseries_definition {
      title = "P99 Latency by Cloud"
      request { q = "avg:http.request.duration.p99{*} by {cloud}"; display_type = "line" }
    }
  }
  widget {
    timeseries_definition {
      title = "Error Rate by Cloud"
      request { q = "sum:http.errors{*}.as_rate() by {cloud}"; display_type = "bars" }
    }
  }
  widget {
    timeseries_definition {
      title = "DB Replication Lag"
      request { q = "avg:postgresql.replication.delay{cloud:azure}"; display_type = "line" }
      request { q = "avg:postgresql.replication.delay{cloud:gcp}"; display_type = "line" }
      marker { display_type = "error dashed"; value = "y = 30"; label = "Max lag (30s)" }
    }
  }
  widget {
    event_stream_definition { title = "DR Events"; query = "tags:type:dr-failover"; event_size = "l" }
  }
}
